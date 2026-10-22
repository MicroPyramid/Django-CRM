/**
 * The Related section on a built-in record's page: the load and the two form
 * actions every detail page shares.
 */

import { fail } from '@sveltejs/kit';
import {
  getRelated,
  addRelated,
  removeRelated,
  checkKey,
  checkFieldKey,
  checkId
} from '#lib/server/v2/custom-objects.js';
import { readableError } from '#lib/server/v2/form-errors.js';

const REFUSED = 'No such record, or you cannot open it.';

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} to A built-in registry key.
 * @param {string} id
 * @returns {Promise<any | null>} Null on any failure, including no custom objects.
 */
export function loadRelated(event, to, id) {
  return getRelated(event, to, id);
}

/**
 * The record and link field from a form. The field may be `<object key>:<field
 * key>` (the add select), of which only the field key goes to the API.
 *
 * @param {FormData} form
 * @returns {{ record: string, field: string } | null} Null for anything malformed.
 */
function readLink(form) {
  const record = form.get('record')?.toString() ?? '';
  const raw = form.get('field')?.toString() ?? '';
  const parts = raw.split(':');
  if (parts.length > 2) return null;
  try {
    if (parts.length === 2) checkKey(parts[0]);
    return { record: checkId(record), field: checkFieldKey(parts[parts.length - 1]) };
  } catch {
    return null;
  }
}

/**
 * @param {string} to A built-in registry key.
 * @param {typeof addRelated} call
 * @param {string} fallback
 * @param {boolean} [needsRecord] Refuse an empty record before any API call.
 */
function writer(to, call, fallback, needsRecord = false) {
  /** @param {import('@sveltejs/kit').RequestEvent} event */
  return async (event) => {
    const form = await event.request.formData();
    if (needsRecord && !form.get('record')?.toString()) {
      return fail(400, { related: { error: 'Choose a record to add.' } });
    }
    const link = readLink(form);
    if (!link) return fail(400, { related: { error: REFUSED } });
    try {
      await call(event, { to, id: event.params.id ?? '', ...link });
    } catch (/** @type {any} */ err) {
      const code = [400, 403, 404].includes(err?.status) ? err.status : 400;
      return fail(code, { related: { error: readableError(err, fallback) } });
    }
    return { related: { done: true } };
  };
}

/**
 * @param {string} to A built-in registry key.
 * @returns {{ relatedAdd: import('@sveltejs/kit').Action, relatedRemove: import('@sveltejs/kit').Action }}
 */
export function relatedActions(to) {
  return {
    relatedAdd: writer(to, addRelated, 'Could not add this record.', true),
    relatedRemove: writer(to, removeRelated, 'Could not remove this record.')
  };
}
