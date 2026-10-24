/**
 * Lead sources: the org's editable list behind every source picker, and the
 * wiring of `/settings/lead-sources`.
 *
 * Any member reads `GET /leads/sources/`; adding, renaming, retiring and
 * ordering are admin-only, and the API decides. There is no delete: a retired
 * source stays on the records that carry it.
 *
 * An API older than this list answers 404. Pickers then fall back to the old
 * fixed list (`LEGACY_LEAD_SOURCES`, which that API validates against), and
 * the settings page says the feature is not available.
 */
import { error } from '@sveltejs/kit';
import { apiRequest } from '#lib/api-helpers.js';
import { rethrowModuleOff } from '#lib/server/v2/modules.js';
import { viewerIsAdmin } from '#lib/server/v2/organization.js';
import { LEGACY_LEAD_SOURCES } from '#lib/v2/lead-sources.js';
import { UUID } from '#lib/v2/custom-objects.js';

const NOT_AVAILABLE = 'Lead sources are not available here.';
const SOURCE_GONE = 'That source does not exist.';

/** @typedef {import('#lib/v2/lead-sources.js').LeadSource} LeadSource */
/** @typedef {{ cookies: import('@sveltejs/kit').Cookies }} Event */

/**
 * @param {any} resp
 * @returns {LeadSource[]}
 */
function shape(resp) {
  const rows = Array.isArray(resp?.sources) ? resp.sources : [];
  return rows
    .filter((/** @type {any} */ s) => s && typeof s.key === 'string')
    .map((/** @type {any} */ s) => ({
      id: s.id ?? null,
      key: s.key,
      label: typeof s.label === 'string' && s.label ? s.label : s.key,
      is_active: s.is_active !== false,
      order: Number.isFinite(s.order) ? s.order : 0
    }))
    .sort((a, b) => a.order - b.order);
}

/**
 * The list for a picker, a filter or a label, retired sources included.
 * Never throws: `live` is false when the API has no list (404, and then the
 * old fixed list stands in) or could not be read (and then the list is empty,
 * so a form keeps a record's value rather than offering keys the API refuses).
 *
 * @param {Event} event
 * @returns {Promise<{ sources: LeadSource[], live: boolean }>}
 */
export async function getLeadSources({ cookies }) {
  try {
    const resp = await apiRequest(
      '/leads/sources/',
      { quietErrors: true, expectedStatuses: [404] },
      { cookies }
    );
    return { sources: shape(resp), live: true };
  } catch (/** @type {any} */ err) {
    if (err?.status === 404 && err?.body?.code !== 'module_off') {
      return { sources: LEGACY_LEAD_SOURCES, live: false };
    }
    return { sources: [], live: false };
  }
}

/**
 * The settings page's list. A 404 is the page's answer: no such feature here.
 *
 * @param {Event} event
 * @returns {Promise<{ sources: LeadSource[], canEdit: boolean }>}
 */
export async function listSourcesForSettings({ cookies }) {
  try {
    const resp = await apiRequest('/leads/sources/', { expectedStatuses: [404] }, { cookies });
    // A display hint; every write is refused server-side to a member.
    return { sources: shape(resp), canEdit: viewerIsAdmin(cookies) };
  } catch (/** @type {any} */ err) {
    rethrowModuleOff(err);
    if (err?.status === 404) error(404, NOT_AVAILABLE);
    throw err;
  }
}

/**
 * The settings hub's numbers: null when they cannot be read, false when the
 * API has no list, so the hub hides the row.
 *
 * @param {Event} event
 * @returns {Promise<{ active: number, count: number } | null | false>}
 */
export async function leadSourcesSummary({ cookies }) {
  try {
    const resp = await apiRequest(
      '/leads/sources/',
      { quietErrors: true, expectedStatuses: [404] },
      { cookies }
    );
    const sources = shape(resp);
    return { active: sources.filter((s) => s.is_active).length, count: sources.length };
  } catch (/** @type {any} */ err) {
    return err?.status === 404 && err?.body?.code !== 'module_off' ? false : null;
  }
}

/** @param {string} id */
function checkId(id) {
  if (typeof id !== 'string' || !UUID.test(id)) error(404, SOURCE_GONE);
  return id;
}

/**
 * The key is derived from the label server-side, so only the label is sent.
 *
 * @param {Event} event
 * @param {string} label
 */
export async function createLeadSource({ cookies }, label) {
  const clean = String(label ?? '').trim();
  if (!clean) throw new Error('A source needs a name.');
  return await apiRequest(
    '/leads/sources/',
    { method: 'POST', body: { label: clean } },
    { cookies }
  );
}

/**
 * Rename or retire. Only `label` and `is_active` are ever sent; the key never
 * changes, because records store it.
 *
 * @param {Event} event
 * @param {string} id
 * @param {{ label?: string, is_active?: boolean }} values
 */
export async function updateLeadSource({ cookies }, id, values) {
  checkId(id);
  /** @type {Record<string, any>} */
  const body = {};
  if (values.label !== undefined) {
    body.label = String(values.label).trim();
    if (!body.label) throw new Error('A source needs a name.');
  }
  if (values.is_active !== undefined) body.is_active = values.is_active === true;
  return await apiRequest(`/leads/sources/${id}/`, { method: 'PATCH', body }, { cookies });
}

/**
 * @param {Event} event
 * @param {string[]} keys every key, in the new order
 */
export async function orderLeadSources({ cookies }, keys) {
  return await apiRequest(
    '/leads/sources/order/',
    { method: 'POST', body: { keys: keys.map(String) } },
    { cookies }
  );
}
