/**
 * Server-side calls to the modules API (`/api/org/modules/`), the guard of
 * module pages, and the page an API `module_off` refusal becomes.
 *
 * Any member reads; only an admin writes, and the server decides. A failed
 * read answers null, which every caller treats as "all modules on".
 */

import { error } from '@sveltejs/kit';
import { apiRequest } from '#lib/api-helpers.js';
import { readableError } from '#lib/server/v2/form-errors.js';
import { refusalFor, requirementFor } from '#lib/v2/modules.js';

/** @typedef {import('#lib/v2/modules.js').ModuleRow} ModuleRow */

/** @typedef {{ modules: ModuleRow[], canEdit: boolean }} ModulesAnswer */

/**
 * @param {any} data
 * @returns {ModulesAnswer | null}
 */
function shape(data) {
  if (!data || !Array.isArray(data.modules)) return null;
  return { modules: data.modules, canEdit: data.can_edit === true };
}

/** @type {WeakMap<object, Promise<ModulesAnswer | null>>} */
const reads = new WeakMap();

/**
 * The list, read once per request: every load of a request (the shell, a
 * folder guard, the page) gets the same read through `event.locals`.
 *
 * @param {any} event
 * @returns {Promise<ModulesAnswer | null>}
 */
export function getModules(event) {
  const locals = event?.locals;
  if (!locals || typeof locals !== 'object') return readModules(event);
  let read = reads.get(locals);
  if (!read) {
    read = readModules(event);
    reads.set(locals, read);
  }
  return read;
}

/**
 * @param {any} event
 * @returns {Promise<ModulesAnswer | null>}
 */
async function readModules(event) {
  try {
    const data = await apiRequest(
      '/org/modules/',
      { quietErrors: true, expectedStatuses: [404] },
      event
    );
    return shape(data);
  } catch {
    return null;
  }
}

/**
 * @param {any} event
 * @param {{ off: string[], order: string[] }} body
 * @returns {Promise<ModulesAnswer | null>}
 */
export async function putModules(event, { off, order }) {
  try {
    const data = await apiRequest('/org/modules/', { method: 'PUT', body: { off, order } }, event);
    return shape(data);
  } finally {
    // A form post without JavaScript runs the loads in the same request.
    if (event?.locals) reads.delete(event.locals);
  }
}

/**
 * The body that flips one module, keeping the order as served.
 *
 * @param {ModuleRow[]} rows
 * @param {string} key
 * @param {boolean} on
 * @returns {{ off: string[], order: string[] } | null}
 */
export function switchBody(rows, key, on) {
  if (!rows.some((r) => r.key === key)) return null;
  const off = rows.filter((r) => !r.enabled && r.key !== key).map((r) => r.key);
  if (!on) off.push(key);
  return {
    off: rows.map((r) => r.key).filter((k) => off.includes(k)),
    order: rows.map((r) => r.key)
  };
}

/**
 * The body that swaps a module with its neighbour in the same group.
 *
 * @param {ModuleRow[]} rows
 * @param {string} key
 * @param {string} direction `up` or `down`
 * @returns {{ off: string[], order: string[] } | null}
 */
export function moveBody(rows, key, direction) {
  if (direction !== 'up' && direction !== 'down') return null;
  const row = rows.find((r) => r.key === key);
  if (!row) return null;
  const peers = rows.filter((r) => r.group === row.group);
  const at = peers.indexOf(row);
  const other = peers[direction === 'up' ? at - 1 : at + 1];
  if (!other) return null;
  const order = rows.map((r) => r.key);
  const a = order.indexOf(row.key);
  const b = order.indexOf(other.key);
  [order[a], order[b]] = [order[b], order[a]];
  return { off: rows.filter((r) => !r.enabled).map((r) => r.key), order };
}

/**
 * @param {any} err the error thrown by `putModules`
 * @returns {string[]}
 */
export function moduleErrors(err) {
  const body = err?.body;
  if (err?.status === 400 && body && typeof body === 'object') {
    const out = [];
    for (const field of ['off', 'order']) {
      const list = body[field];
      if (Array.isArray(list)) out.push(...list.filter((m) => typeof m === 'string'));
      else if (typeof list === 'string') out.push(list);
    }
    if (out.length) return out;
  }
  if (err?.status === 403) {
    const text = body?.errors ?? body?.detail;
    if (typeof text === 'string' && text.trim()) return [text];
  }
  return [readableError(err, 'Could not save the modules.')];
}

/**
 * The `load` of each folder holding a module page: a page of a switched-off
 * module becomes the module page, rendered by `(app)/+error.svelte`.
 *
 * It asks for the list itself, and only on a module route: `parent()` would
 * rerun the whole shell load on every client-side navigation.
 *
 * @param {{ route: { id: string | null }, cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{}>}
 */
export async function moduleGuard(event) {
  if (!requirementFor(event.route.id)) return {};
  const answer = await getModules(event);
  const refusal = refusalFor(event.route.id, answer?.modules ?? null);
  if (refusal) {
    error(404, `${refusal.label} is switched off for this organization.`, {
      code: 'module_off',
      module: refusal.key,
      label: refusal.label
    });
  }
  return {};
}

/**
 * The page error for an API `module_off` refusal, or undefined for any other
 * error. The 409 delete refusal is a form's message, not a page.
 *
 * @param {any} err an error thrown by `apiRequest`
 * @returns {App.Error | undefined}
 */
export function moduleOffError(err) {
  const body = err?.body;
  if (err?.status !== 404 || body?.code !== 'module_off') return undefined;
  return { status: 404, message: body.detail, code: 'module_off', module: body.module };
}

/**
 * Throws the module page when `err` is a `module_off` refusal; returns otherwise.
 *
 * @param {any} err
 */
export function rethrowModuleOff(err) {
  const off = moduleOffError(err);
  if (off) error(404, off.message, { code: off.code, module: off.module });
}

/**
 * The `detail` of an upstream `module_off` 404, or null. Reads the body, so
 * call it only on a response that is not passed on.
 *
 * @param {Response} response
 * @returns {Promise<string | null>}
 */
export async function moduleOffDetail(response) {
  if (response.status !== 404) return null;
  try {
    const body = await response.json();
    return body?.code === 'module_off' && typeof body.detail === 'string' ? body.detail : null;
  } catch {
    return null;
  }
}
