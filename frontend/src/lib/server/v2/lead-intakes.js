/**
 * Lead webhooks: the wiring behind the webhooks half of `/settings/lead-capture`.
 *
 * Admin-only, reads included (`/api/leads/intakes/` answers a member 403), so
 * the list folds a 403 into `forbidden`. An API older than intakes answers
 * 404, which hides the webhooks part of the page.
 *
 * THE KEY
 * The full key travels in exactly two responses, a create and a replace, and
 * goes to the page for that one render. Every read is rebuilt from an
 * allow-list that leaves `key` out, so a detail page can only ever show
 * `key_hint`, even if a response starts carrying more.
 */
import { error } from '@sveltejs/kit';
import { apiRequest } from '#lib/api-helpers.js';
import { rethrowModuleOff } from '#lib/server/v2/modules.js';
import { viewerIsAdmin } from '#lib/server/v2/organization.js';
import { UUID } from '#lib/v2/custom-objects.js';
import { cleanMapping } from '#lib/v2/lead-intakes.js';

const INTAKE_GONE = 'That webhook does not exist.';

/** @typedef {{ cookies: import('@sveltejs/kit').Cookies }} Event */

/**
 * A list read off any of the shapes a DRF list view answers with.
 *
 * @param {any} resp
 * @param {string} key
 * @returns {any[]}
 */
function listOf(resp, key) {
  if (Array.isArray(resp)) return resp;
  if (Array.isArray(resp?.[key])) return resp[key];
  return Array.isArray(resp?.results) ? resp.results : [];
}

/** @param {any} value an id, or an object carrying one */
function idOf(value) {
  if (typeof value === 'string') return value;
  return typeof value?.id === 'string' ? value.id : null;
}

/**
 * The fields the pages read. `key` is deliberately not among them.
 *
 * @param {any} raw
 */
export function toIntake(raw) {
  const owner = raw?.assignee_details;
  return {
    id: raw?.id ?? '',
    name: raw?.name ?? '',
    preset: raw?.preset ?? 'generic',
    url: raw?.url ?? '',
    key_hint: raw?.key_hint ?? '',
    mapping: cleanMapping(raw?.mapping),
    default_source: raw?.default_source ?? '',
    source_detail: raw?.source_detail ?? '',
    tags: (Array.isArray(raw?.tags) ? raw.tags : []).map(idOf).filter(Boolean),
    assignee: idOf(raw?.assignee),
    // The name for an owner the people picker no longer lists (deactivated).
    assignee_name: owner?.name || owner?.email || null,
    is_active: raw?.is_active !== false,
    last_received_at: raw?.last_received_at ?? null,
    last_error: raw?.last_error ?? '',
    created_at: raw?.created_at ?? null
  };
}

/** @param {any} raw */
function toDelivery(raw) {
  return {
    id: raw?.id ?? '',
    received_at: raw?.received_at ?? null,
    result: raw?.result ?? '',
    lead: idOf(raw?.lead),
    external_id: raw?.external_id ?? '',
    error: raw?.error ?? ''
  };
}

/** @param {string} id */
function checkId(id) {
  if (typeof id !== 'string' || !UUID.test(id)) error(404, INTAKE_GONE);
  return id;
}

/**
 * @param {Event} event
 * @returns {Promise<{ state: 'ok' | 'forbidden' | 'absent' | 'failed', intakes: ReturnType<typeof toIntake>[] }>}
 */
export async function listIntakes({ cookies }) {
  try {
    const resp = await apiRequest('/leads/intakes/', { expectedStatuses: [403, 404] }, { cookies });
    return { state: 'ok', intakes: listOf(resp, 'intakes').map(toIntake) };
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) return { state: 'forbidden', intakes: [] };
    if (err?.status === 404) return { state: 'absent', intakes: [] };
    return { state: 'failed', intakes: [] };
  }
}

/**
 * One intake and its newest deliveries (the API keeps 50). The deliveries are
 * best-effort: a failed read leaves the settings usable.
 *
 * @param {Event} event
 * @param {string} id
 */
export async function getIntake({ cookies }, id) {
  checkId(id);
  const [detail, deliveries] = await Promise.all([
    apiRequest(`/leads/intakes/${id}/`, { expectedStatuses: [403, 404] }, { cookies }).catch(
      (/** @type {any} */ err) => {
        if (err?.status === 403) return null;
        rethrowModuleOff(err);
        if (err?.status === 404) error(404, INTAKE_GONE);
        throw err;
      }
    ),
    apiRequest(`/leads/intakes/${id}/deliveries/`, { quietErrors: true }, { cookies }).then(
      (resp) =>
        listOf(resp, 'deliveries')
          .map(toDelivery)
          .sort((a, b) => String(b.received_at).localeCompare(String(a.received_at))),
      () => null
    )
  ]);
  if (detail === null) return { forbidden: true };
  return {
    forbidden: false,
    intake: toIntake(detail),
    deliveries: deliveries ?? [],
    deliveriesFailed: deliveries === null
  };
}

/** The fields an admin edits. `key`, `url`, `id` and the org never go up. */
const WRITABLE = [
  'name',
  'preset',
  'mapping',
  'default_source',
  'source_detail',
  'tags',
  'assignee',
  'is_active'
];

/** @param {Record<string, any>} values */
export function intakeBody(values) {
  /** @type {Record<string, any>} */
  const body = {};
  for (const key of WRITABLE) {
    if (values[key] !== undefined) body[key] = values[key];
  }
  if (body.name !== undefined) {
    body.name = String(body.name).trim();
    if (!body.name) throw new Error('A webhook needs a name.');
  }
  if (body.mapping !== undefined) body.mapping = cleanMapping(body.mapping);
  if (body.tags !== undefined) {
    body.tags = (Array.isArray(body.tags) ? body.tags : []).map(String).filter(Boolean);
  }
  if (body.assignee !== undefined) body.assignee = body.assignee || null;
  if (body.is_active !== undefined) body.is_active = body.is_active === true;
  for (const key of ['default_source', 'source_detail']) {
    if (body[key] !== undefined) body[key] = String(body[key] ?? '').trim();
  }
  return body;
}

/**
 * Returns the one response that carries the full key, cut to what the page
 * shows once: where to post and with what.
 *
 * @param {Event} event
 * @param {Record<string, any>} values
 */
export async function createIntake({ cookies }, values) {
  const body = intakeBody(values);
  if (!body.name) throw new Error('A webhook needs a name.');
  const resp = await apiRequest('/leads/intakes/', { method: 'POST', body }, { cookies });
  return {
    id: resp?.id ?? '',
    name: resp?.name ?? body.name,
    url: resp?.url ?? '',
    key: typeof resp?.key === 'string' ? resp.key : ''
  };
}

/**
 * @param {Event} event
 * @param {string} id
 * @param {Record<string, any>} values
 */
export async function updateIntake({ cookies }, id, values) {
  checkId(id);
  return await apiRequest(
    `/leads/intakes/${id}/`,
    { method: 'PATCH', body: intakeBody(values) },
    { cookies }
  );
}

/** @param {Event} event @param {string} id */
export async function deleteIntake({ cookies }, id) {
  checkId(id);
  return await apiRequest(`/leads/intakes/${id}/`, { method: 'DELETE' }, { cookies });
}

/**
 * A new key, answered once. The old one keeps working for 7 days server-side.
 *
 * @param {Event} event
 * @param {string} id
 * @returns {Promise<{ key: string }>}
 */
export async function replaceIntakeKey({ cookies }, id) {
  checkId(id);
  const resp = await apiRequest(`/leads/intakes/${id}/key/`, { method: 'POST' }, { cookies });
  return { key: typeof resp?.key === 'string' ? resp.key : '' };
}

/** Logs a `test` delivery and makes no lead. @param {Event} event @param {string} id */
export async function testIntake({ cookies }, id) {
  checkId(id);
  return await apiRequest(`/leads/intakes/${id}/test/`, { method: 'POST' }, { cookies });
}

/**
 * The settings hub's numbers, asked only for an admin (a member is refused).
 * Null when they cannot be read, false when the API has no intakes.
 *
 * @param {Event} event
 * @returns {Promise<{ count: number, active: number } | null | false>}
 */
export async function intakesSummary({ cookies }) {
  if (!viewerIsAdmin(cookies)) return null;
  try {
    const resp = await apiRequest(
      '/leads/intakes/',
      { quietErrors: true, expectedStatuses: [403, 404] },
      { cookies }
    );
    const rows = listOf(resp, 'intakes');
    return { count: rows.length, active: rows.filter((r) => r?.is_active !== false).length };
  } catch (/** @type {any} */ err) {
    return err?.status === 404 && err?.body?.code !== 'module_off' ? false : null;
  }
}
