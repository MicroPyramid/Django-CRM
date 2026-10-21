/**
 * Server-side calls to the custom objects API (`/api/objects/`).
 *
 * A self-hosted install has no such routes and answers 404 to all of them;
 * `getCustomObjects` and `getRelated` turn that into `null` so callers can
 * hide the feature. Every key and id is checked before it reaches a path.
 */

import { error } from '@sveltejs/kit';
import { apiRequest } from '#lib/api-helpers.js';
import { readableError } from '#lib/server/v2/form-errors.js';
import { listLeads } from '#lib/server/v2/leads.js';
import { listContacts } from '#lib/server/v2/contacts.js';
import { listAccounts } from '#lib/server/v2/accounts.js';
import { listDeals } from '#lib/server/v2/deals.js';
import { listTickets } from '#lib/server/v2/tickets.js';
import { listTasks } from '#lib/server/v2/tasks.js';
import { attachmentHref } from '#lib/server/v2/files.js';
import { isPhoto, OBJECT_KEY, UUID } from '#lib/v2/custom-objects.js';

export const FIELD_KEY = /^[a-z][a-z0-9_]{0,63}$/;

const PAGE_SIZE = 20;
const ABSENT_FOR_MS = 5 * 60 * 1000;
const NOT_AVAILABLE = 'Custom objects are not available here.';
export const OBJECT_GONE = 'That object does not exist, or you do not have access to it.';
const RECORD_GONE = 'That record does not exist, or you do not have access to it.';

/** @typedef {{ cookies: import('@sveltejs/kit').Cookies }} Event */

/**
 * @param {string} key
 * @returns {string}
 */
export function checkKey(key) {
  if (typeof key !== 'string' || !OBJECT_KEY.test(key)) error(404, OBJECT_GONE);
  return key;
}

/**
 * @param {string} key
 * @returns {string}
 */
export function checkFieldKey(key) {
  if (typeof key !== 'string' || !FIELD_KEY.test(key)) error(404, OBJECT_GONE);
  return key;
}

/**
 * @param {string} id
 * @returns {string}
 */
export function checkId(id) {
  if (typeof id !== 'string' || !UUID.test(id)) error(404, RECORD_GONE);
  return id;
}

/**
 * A query string with %20 for spaces, as the API paths are written elsewhere.
 *
 * @param {Record<string, string | number | undefined>} values
 * @returns {string}
 */
function query(values) {
  const params = new URLSearchParams();
  for (const [name, value] of Object.entries(values)) {
    if (value !== undefined && value !== '') params.set(name, String(value));
  }
  return params.toString().replaceAll('+', '%20');
}

/**
 * Run a call, turning a 404 into a page 404 and rethrowing anything else.
 *
 * @template T
 * @param {() => Promise<T>} call
 * @param {string} message
 * @returns {Promise<T>}
 */
async function orNotFound(call, message) {
  try {
    return await call();
  } catch (/** @type {any} */ err) {
    if (err?.status === 404) error(404, message);
    throw err;
  }
}

/**
 * Set when `GET /objects/` answers 404 (a backend without custom objects), so
 * that backend's request log gains one line per 5 minutes, not one per page.
 */
let absentUntil = 0;

const absent = () => Date.now() < absentUntil;

/** Forget the absent memo; for tests. */
export function resetObjectsAbsentMemo() {
  absentUntil = 0;
}

/**
 * The objects answer, or null where there are no custom objects or the call
 * failed for any reason.
 *
 * @param {Event} event
 * @returns {Promise<{ has_custom_objects: boolean, objects: any[], link_targets: any[] } | null>}
 */
export async function getCustomObjects({ cookies }) {
  if (absent()) return null;
  try {
    const body = await apiRequest(
      '/objects/',
      { quietErrors: true, expectedStatuses: [404] },
      { cookies }
    );
    absentUntil = 0;
    return Array.isArray(body?.objects) && Array.isArray(body?.link_targets) ? body : null;
  } catch (/** @type {any} */ err) {
    if (err?.status === 404) absentUntil = Date.now() + ABSENT_FOR_MS;
    return null;
  }
}

/**
 * Every object, archived ones included (admins only see those).
 *
 * @param {Event} event
 * @returns {Promise<{ has_custom_objects: boolean, objects: any[], link_targets: any[] }>}
 */
export async function listObjectsForSettings({ cookies }) {
  return await orNotFound(
    () => apiRequest('/objects/?include_archived=true', { expectedStatuses: [404] }, { cookies }),
    NOT_AVAILABLE
  );
}

/**
 * @param {Event} event
 * @param {string} key
 * @returns {Promise<any>} The object with its active `fields`.
 */
export async function getObject({ cookies }, key) {
  checkKey(key);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/`, { expectedStatuses: [404] }, { cookies }),
    OBJECT_GONE
  );
}

/**
 * @param {Event} event
 * @param {string} key
 * @returns {Promise<any[]>} Admins also get turned-off fields.
 */
export async function listFields({ cookies }, key) {
  checkKey(key);
  const response = await orNotFound(
    () => apiRequest(`/objects/${key}/fields/`, { expectedStatuses: [404] }, { cookies }),
    OBJECT_GONE
  );
  return response?.fields ?? [];
}

/**
 * @param {Event} event
 * @param {Record<string, unknown>} body
 */
export async function createObject({ cookies }, body) {
  return await apiRequest('/objects/', { method: 'POST', body }, { cookies });
}

/**
 * @param {Event} event
 * @param {string} key
 * @param {Record<string, unknown>} body
 */
export async function updateObject({ cookies }, key, body) {
  checkKey(key);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/`, { method: 'PATCH', body }, { cookies }),
    OBJECT_GONE
  );
}

/**
 * Archives an active object; deletes an archived one for good.
 *
 * @param {Event} event
 * @param {string} key
 * @returns {Promise<any | null>} The archived object, or null on 204.
 */
export async function deleteObject({ cookies }, key) {
  checkKey(key);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/`, { method: 'DELETE' }, { cookies }),
    OBJECT_GONE
  );
}

/**
 * @param {Event} event
 * @param {string} key
 * @param {Record<string, unknown>} body
 */
export async function createField({ cookies }, key, body) {
  checkKey(key);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/fields/`, { method: 'POST', body }, { cookies }),
    OBJECT_GONE
  );
}

/**
 * @param {Event} event
 * @param {string} key
 * @param {string} fieldKey
 * @param {Record<string, unknown>} body
 */
export async function updateField({ cookies }, key, fieldKey, body) {
  checkKey(key);
  checkFieldKey(fieldKey);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/fields/${fieldKey}/`, { method: 'PATCH', body }, { cookies }),
    OBJECT_GONE
  );
}

/**
 * Turns a field off; its values and links are kept.
 *
 * @param {Event} event
 * @param {string} key
 * @param {string} fieldKey
 */
export async function turnOffField({ cookies }, key, fieldKey) {
  checkKey(key);
  checkFieldKey(fieldKey);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/fields/${fieldKey}/`, { method: 'DELETE' }, { cookies }),
    OBJECT_GONE
  );
}

/**
 * @param {Event} event
 * @param {string} key
 * @param {{ q?: string, page?: number }} [params]
 * @returns {Promise<{ count: number, results: any[] }>}
 */
export async function listRecords({ cookies }, key, { q = '', page = 1 } = {}) {
  checkKey(key);
  const offset = (Math.max(1, Math.floor(page) || 1) - 1) * PAGE_SIZE;
  const qs = query({ q: q.trim(), limit: PAGE_SIZE, offset });
  return await orNotFound(
    () => apiRequest(`/objects/${key}/records/?${qs}`, { expectedStatuses: [404] }, { cookies }),
    OBJECT_GONE
  );
}

/**
 * @param {Event} event
 * @param {string} key
 * @param {string} id
 * @returns {Promise<any>} The record detail.
 */
export async function getRecord({ cookies }, key, id) {
  checkKey(key);
  checkId(id);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/records/${id}/`, { expectedStatuses: [404] }, { cookies }),
    RECORD_GONE
  );
}

/**
 * What the record detail page needs: the definition and the record, loaded
 * together, with attachments split into photos and files.
 *
 * @param {Event} event
 * @param {string} key
 * @param {string} id
 */
export async function recordPage(event, key, id) {
  checkKey(key);
  checkId(id);
  const [definition, record] = await Promise.all([
    getObject(event, key),
    getRecord(event, key, id)
  ]);
  if (definition.is_active === false) error(404, OBJECT_GONE);
  const attachments = (record.attachments ?? []).map((/** @type {any} */ a) => ({
    ...a,
    href: attachmentHref(a.id)
  }));
  return {
    definition,
    record,
    photos: attachments.filter((/** @type {any} */ a) => isPhoto(a)),
    files: attachments.filter((/** @type {any} */ a) => !isPhoto(a))
  };
}

/**
 * @param {Event} event
 * @param {string} key
 * @param {Record<string, unknown>} body
 */
export async function createRecord({ cookies }, key, body) {
  checkKey(key);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/records/`, { method: 'POST', body }, { cookies }),
    RECORD_GONE
  );
}

/**
 * Changes only what the body sends.
 *
 * @param {Event} event
 * @param {string} key
 * @param {string} id
 * @param {Record<string, unknown>} body
 */
export async function updateRecord({ cookies }, key, id, body) {
  checkKey(key);
  checkId(id);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/records/${id}/`, { method: 'PATCH', body }, { cookies }),
    RECORD_GONE
  );
}

/**
 * @param {Event} event
 * @param {string} key
 * @param {string} id
 */
export async function deleteRecord({ cookies }, key, id) {
  checkKey(key);
  checkId(id);
  return await orNotFound(
    () => apiRequest(`/objects/${key}/records/${id}/`, { method: 'DELETE' }, { cookies }),
    RECORD_GONE
  );
}

/**
 * @param {Event} event
 * @param {string} key
 * @param {string} id
 * @param {File} file
 */
export async function uploadAttachment({ cookies }, key, id, file) {
  checkKey(key);
  checkId(id);
  const body = new FormData();
  body.append('file', file);
  return await orNotFound(
    () =>
      apiRequest(
        `/objects/${key}/records/${id}/attachments/`,
        { method: 'POST', body },
        { cookies }
      ),
    RECORD_GONE
  );
}

/**
 * @param {Event} event
 * @param {string} key
 * @param {string} id
 * @param {string} attachmentId
 */
export async function deleteAttachment({ cookies }, key, id, attachmentId) {
  checkKey(key);
  checkId(id);
  checkId(attachmentId);
  return await orNotFound(
    () =>
      apiRequest(
        `/objects/${key}/records/${id}/attachments/${attachmentId}/`,
        { method: 'DELETE' },
        { cookies }
      ),
    RECORD_GONE
  );
}

const BUILT_IN = ['lead', 'contact', 'account', 'deal', 'ticket', 'task'];

/**
 * Custom records linked to a built-in record, or null on any failure.
 *
 * @param {Event} event
 * @param {string} to A built-in registry key.
 * @param {string} id
 * @returns {Promise<any | null>}
 */
export async function getRelated({ cookies }, to, id) {
  if (!BUILT_IN.includes(to) || !UUID.test(id) || absent()) return null;
  try {
    const body = await apiRequest(
      `/objects/related/?${query({ to, id })}`,
      { quietErrors: true, expectedStatuses: [404] },
      { cookies }
    );
    return Array.isArray(body?.groups) && Array.isArray(body?.link_fields) ? body : null;
  } catch {
    return null;
  }
}

/**
 * @param {{ to: string, id: string, record: string, field: string }} link
 */
function checkLink({ to, id, record, field }) {
  if (!BUILT_IN.includes(to)) error(404, RECORD_GONE);
  checkId(id);
  checkId(record);
  checkFieldKey(field);
}

/**
 * @param {Event} event
 * @param {{ to: string, id: string, record: string, field: string }} link
 * @returns {Promise<{ added: boolean }>}
 */
export async function addRelated({ cookies }, link) {
  checkLink(link);
  const { to, id, record, field } = link;
  return await apiRequest(
    '/objects/related/',
    { method: 'POST', body: { to, id, record, field } },
    { cookies }
  );
}

/**
 * @param {Event} event
 * @param {{ to: string, id: string, record: string, field: string }} link
 */
export async function removeRelated({ cookies }, link) {
  checkLink(link);
  const { to, id, record, field } = link;
  return await apiRequest(
    `/objects/related/?${query({ to, id, record, field })}`,
    { method: 'DELETE' },
    { cookies }
  );
}

/**
 * Each built-in kind's own list helper, so a name reads as it does on that
 * module's list page.
 *
 * @type {Record<string, (event: Event, params: URLSearchParams) => Promise<{ results: any[] }>>}
 */
const SEARCH = {
  lead: listLeads,
  contact: listContacts,
  account: listAccounts,
  deal: listDeals,
  ticket: listTickets,
  task: listTasks
};

/** @type {Record<string, (row: any) => string>} */
const ROW_NAME = {
  lead: (row) =>
    [row.first_name, row.last_name].filter(Boolean).join(' ').trim() ||
    row.company_name ||
    row.email ||
    'Untitled',
  contact: (row) => row.name,
  account: (row) => row.name,
  deal: (row) => row.name,
  ticket: (row) => row.name,
  task: (row) => row.title
};

/**
 * Names for a link picker, at most 20.
 *
 * @param {Event} event
 * @param {string} target A built-in registry key, or `obj:<key>`.
 * @param {string} q
 * @returns {Promise<{ id: string, name: string }[]>}
 */
export async function searchLinkTargets(event, target, q) {
  const search = String(q ?? '').trim();
  if (Object.hasOwn(SEARCH, target)) {
    const params = new URLSearchParams({ limit: String(PAGE_SIZE) });
    if (search) params.set('search', search);
    const { results } = await SEARCH[target](event, params);
    return results.slice(0, PAGE_SIZE).map((row) => ({ id: row.id, name: ROW_NAME[target](row) }));
  }
  if (typeof target === 'string' && target.startsWith('obj:') && OBJECT_KEY.test(target.slice(4))) {
    const qs = query({ q: search, limit: PAGE_SIZE });
    const response = await apiRequest(
      `/objects/${target.slice(4)}/records/?${qs}`,
      {},
      { cookies: event.cookies }
    );
    return (response?.results ?? [])
      .slice(0, PAGE_SIZE)
      .map((/** @type {any} */ row) => ({ id: row.id, name: row.name }));
  }
  return [];
}

/** @param {unknown} value */
const first = (value) => String(Array.isArray(value) ? value[0] : value);

/**
 * A refused record save as one line per refused field.
 *
 * @param {any} err The error thrown by a record write.
 * @param {{ key: string, label: string }[]} fields The object's field list.
 * @param {string} [nameLabel] The object's `name_label`.
 * @returns {string}
 */
export function recordWriteError(err, fields, nameLabel = 'Name') {
  const body = err?.body;
  /** @param {string} key */
  const label = (key) => fields.find((field) => field.key === key)?.label ?? key;
  /** @type {string[]} */
  const lines = [];
  if (body?.name) lines.push(`${nameLabel}: ${first(body.name)}`);
  for (const [key, message] of Object.entries(body?.custom_fields ?? {})) {
    lines.push(key === '_size' ? first(message) : `${label(key)}: ${first(message)}`);
  }
  for (const [key, message] of Object.entries(body?.links ?? {})) {
    lines.push(`${label(key)}: ${first(message)}`);
  }
  if (body?.assigned_to) lines.push(`Assignees: ${first(body.assigned_to)}`);
  if (lines.length) return lines.join('\n');
  if (typeof body?.detail === 'string') return body.detail;
  return readableError(err, 'Could not save this record.');
}
