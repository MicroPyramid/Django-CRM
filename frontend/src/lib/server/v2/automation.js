/**
 * The automation builder's API, behind `/settings/automation`. Server-only.
 * The contract is the code in `backend/automation/`.
 */
import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '#lib/api-helpers.js';
import { readableError } from '#lib/server/v2/form-errors.js';
import { checkId } from '#lib/server/v2/custom-objects.js';

export const RULE_GONE = 'That rule does not exist, or you do not have access to it.';
const UNREADABLE = 'Could not read the rule.';

/** Runs per page on a rule's history. */
export const RUN_PAGE = 20;

/** @typedef {{ cookies: import('@sveltejs/kit').Cookies }} Event */

/** @param {Event} event */
export async function getCatalogue({ cookies }) {
  return await apiRequest('/automation/catalogue/', { expectedStatuses: [403] }, { cookies });
}

/** @param {Event} event */
export async function listRules({ cookies }) {
  try {
    const resp = await apiRequest('/automation/rules/', { expectedStatuses: [403] }, { cookies });
    return { summary: resp?.summary ?? null, rules: resp?.results ?? [] };
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) return { forbidden: true };
    throw err;
  }
}

/**
 * @param {Event} event
 * @param {string} id
 */
export async function getRule({ cookies }, id) {
  checkId(id);
  try {
    return await apiRequest(
      `/automation/rules/${id}/`,
      { expectedStatuses: [403, 404] },
      { cookies }
    );
  } catch (/** @type {any} */ err) {
    if (err?.status === 404) error(404, RULE_GONE);
    throw err;
  }
}

/**
 * @param {Event} event
 * @param {Record<string, any>} body
 */
export async function createRule({ cookies }, body) {
  return await apiRequest('/automation/rules/', { method: 'POST', body }, { cookies });
}

/**
 * @param {Event} event
 * @param {string} id
 * @param {Record<string, any>} body
 */
export async function updateRule({ cookies }, id, body) {
  checkId(id);
  return await apiRequest(`/automation/rules/${id}/`, { method: 'PATCH', body }, { cookies });
}

/**
 * @param {Event} event
 * @param {string} id
 */
export async function switchOff(event, id) {
  return await updateRule(event, id, { is_active: false });
}

/**
 * @param {Event} event
 * @param {string} id
 */
export async function deleteRule({ cookies }, id) {
  checkId(id);
  await apiRequest(`/automation/rules/${id}/`, { method: 'DELETE' }, { cookies });
}

/**
 * @param {Event} event
 * @param {string} id
 * @param {string} recordId
 * @returns {Promise<any[]>}
 */
export async function tryRule({ cookies }, id, recordId) {
  checkId(id);
  const resp = await apiRequest(
    `/automation/rules/${id}/try/`,
    { method: 'POST', body: { record_id: recordId } },
    { cookies }
  );
  return resp?.steps ?? [];
}

/**
 * @param {Event} event
 * @param {string} id
 * @param {number} rawOffset
 */
export async function listRuns({ cookies }, id, rawOffset) {
  checkId(id);
  const whole = Math.trunc(Number(rawOffset));
  const offset = Number.isSafeInteger(whole) ? Math.max(0, whole) : 0;
  const resp = await apiRequest(
    `/automation/rules/${id}/runs/?limit=${RUN_PAGE}&offset=${offset}`,
    {},
    { cookies }
  );
  return { count: resp?.count ?? 0, runs: resp?.results ?? [], offset, pageSize: RUN_PAGE };
}

/**
 * @param {Event} event
 * @param {string[]} ids
 */
export async function reorderRules({ cookies }, ids) {
  return await apiRequest(
    '/automation/rules/reorder/',
    { method: 'POST', body: { ids } },
    { cookies }
  );
}

/**
 * The Settings tile's numbers. Any failure is null: the tile just does not show.
 * @param {Event} event
 * @returns {Promise<{ active: number, failing: number, attention: boolean } | null>}
 */
export async function automationSummary({ cookies }) {
  try {
    const resp = await apiRequest('/automation/rules/', { quietErrors: true }, { cookies });
    const rules = Array.isArray(resp?.results) ? resp.results : [];
    let active = 0;
    let failing = 0;
    let attention = false;
    for (const r of rules) {
      const bad = r.failures_7d > 0 || r.status === 'needs_attention';
      if (r.is_active) active += 1;
      if (bad) failing += 1;
      if (bad || r.status === 'paused') attention = true;
    }
    return { active, failing, attention };
  } catch {
    return null;
  }
}

/**
 * @param {any} source
 * @param {string[]} keys
 */
function pick(source, keys) {
  if (source === null || typeof source !== 'object' || Array.isArray(source)) {
    throw new Error(UNREADABLE);
  }
  /** @type {Record<string, any>} */
  const out = {};
  for (const key of keys) if (Object.hasOwn(source, key)) out[key] = source[key];
  return out;
}

/** @param {any} value */
function list(value) {
  if (!Array.isArray(value)) throw new Error(UNREADABLE);
  return value;
}

/** @type {Record<string, string[]>} */
const ACTION_KEYS = {
  set_field: ['target', 'field', 'value'],
  assign: ['mode', 'people'],
  create_task: ['title', 'due_in_days', 'priority', 'assign_to', 'person'],
  notify: ['to', 'people', 'message'],
  webhook: ['endpoint']
};

/**
 * A rule rebuilt key by key from parsed JSON; the server validates the values.
 * @param {any} raw
 * @param {{ create: boolean }} options
 */
export function ruleBody(raw, { create }) {
  const body = pick(raw, ['name', 'match', 'trigger', 'conditions', 'actions']);
  if (create && Object.hasOwn(raw, 'object_key')) body.object_key = raw.object_key;
  if (Object.hasOwn(raw, 'trigger')) body.trigger = pick(raw.trigger, ['event', 'field', 'to']);
  if (Object.hasOwn(raw, 'conditions')) {
    body.conditions = list(raw.conditions).map((c) => pick(c, ['field', 'op', 'value']));
  }
  if (Object.hasOwn(raw, 'actions')) {
    body.actions = list(raw.actions).map((a) => {
      const type = pick(a, ['type']).type;
      const keys =
        typeof type === 'string' && Object.hasOwn(ACTION_KEYS, type) ? ACTION_KEYS[type] : [];
      return pick(a, ['type', ...keys]);
    });
  }
  return body;
}

/**
 * The editor's `rule` field, which carries the whole draft as JSON, rebuilt by
 * `ruleBody`. Throws `Could not read the rule.` for anything else.
 * @param {FormData} form
 * @param {{ create: boolean }} options
 */
export function ruleFromForm(form, options) {
  const raw = form.get('rule');
  let parsed;
  try {
    parsed = JSON.parse(typeof raw === 'string' ? raw : '');
  } catch {
    throw new Error(UNREADABLE);
  }
  return ruleBody(parsed, options);
}

/**
 * A refused save as the editor shows it, with the API's status.
 * @param {any} err
 */
export function refusedSave(err) {
  const status = Number.isInteger(err?.status) && err.status >= 400 && err.status < 600;
  return fail(status ? err.status : 400, { save: ruleErrors(err) });
}

/**
 * @param {string[]} ids
 * @param {string} id
 * @param {string} direction `up` or `down`
 * @returns {string[] | null}
 */
export function moveRule(ids, id, direction) {
  const at = ids.indexOf(id);
  if (at === -1 || (direction !== 'up' && direction !== 'down')) return null;
  const to = direction === 'up' ? at - 1 : at + 1;
  if (to < 0 || to >= ids.length) return null;
  const next = [...ids];
  [next[at], next[to]] = [next[to], next[at]];
  return next;
}

/** @param {string} path */
function rowKey(path) {
  const m = /^(conditions|actions)\[(\d+)\]/.exec(path);
  if (m) return `${m[1]}.${m[2]}`;
  if (path === 'trigger' || path.startsWith('trigger.')) return 'trigger';
  return path;
}

/**
 * @param {any} err the error thrown by `apiRequest`
 * @returns {{ general: string | null, rows: Record<string, string> }}
 */
export function ruleErrors(err) {
  /** @type {Record<string, string>} */
  const rows = {};
  const errors = err?.body?.errors;
  if (err?.status === 400 && errors && typeof errors === 'object' && !Array.isArray(errors)) {
    for (const [path, messages] of Object.entries(errors)) {
      const message = Array.isArray(messages) ? messages[0] : messages;
      const key = rowKey(path);
      if (typeof message === 'string' && !Object.hasOwn(rows, key)) rows[key] = message;
    }
    if (Object.keys(rows).length) return { general: null, rows };
  }
  if (err?.status === 403 && typeof err?.body?.detail === 'string') {
    return { general: err.body.detail, rows };
  }
  return { general: readableError(err, 'Could not save the rule.'), rows };
}
