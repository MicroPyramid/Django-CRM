import { fail } from '@sveltejs/kit';
import {
  createLeadSource,
  listSourcesForSettings,
  orderLeadSources,
  updateLeadSource
} from '#lib/server/v2/lead-sources.js';
import { readableError } from '#lib/server/v2/form-errors.js';
import { moveKeys } from '#lib/v2/lead-sources.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  return await listSourcesForSettings(event);
}

/**
 * The status and sentence for a refused write. Every write is admin-only
 * server-side; the page hides the controls from a member, and a member
 * posting anyway reads this.
 *
 * @param {any} err @param {string} fallback
 * @returns {{ status: number, error: string }}
 */
function refusal(err, fallback) {
  if (err?.status === 403) return { status: 403, error: 'Only an admin can change lead sources.' };
  if (err?.status === 404) return { status: 404, error: 'That source no longer exists.' };
  return { status: 400, error: readableError(err, fallback) };
}

/** A refusal under the action's key, with the row it was about. */
function refused(
  /** @type {string} */ key,
  /** @type {string} */ id,
  /** @type {any} */ err,
  /** @type {string} */ fallback
) {
  const { status, error } = refusal(err, fallback);
  return fail(status, { [key]: { id, error } });
}

/** @type {import('./$types').Actions} */
export const actions = {
  async add(event) {
    const form = await event.request.formData();
    const label = form.get('label')?.toString().trim() ?? '';
    if (!label) return fail(400, { add: { id: '', error: 'Give the source a name.', label } });
    try {
      await createLeadSource(event, label);
    } catch (err) {
      const { status, error } = refusal(err, 'Could not add the source.');
      return fail(status, { add: { id: '', error, label } });
    }
    return { added: label };
  },

  async rename(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    const label = form.get('label')?.toString().trim() ?? '';
    if (!label) return fail(400, { rename: { id, error: 'A source needs a name.' } });
    try {
      await updateLeadSource(event, id, { label });
    } catch (err) {
      return refused('rename', id, err, 'Could not rename the source.');
    }
    return { renamed: id };
  },

  // Retire and restore send `is_active` alone, so neither can carry a stale label.
  async retire(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    const active = form.get('is_active')?.toString();
    if (active !== 'true' && active !== 'false') {
      return fail(400, { retire: { id, error: 'That source could not be changed.' } });
    }
    try {
      await updateLeadSource(event, id, { is_active: active === 'true' });
    } catch (err) {
      return refused('retire', id, err, 'Could not change the source.');
    }
    return { retired: id };
  },

  /** Re-reads the list, so the order sent is built from what the server holds now. */
  async move(event) {
    const form = await event.request.formData();
    const key = form.get('key')?.toString() ?? '';
    const direction = form.get('direction')?.toString() ?? '';
    let keys;
    try {
      const { sources } = await listSourcesForSettings(event);
      keys = moveKeys(sources, key, direction);
    } catch (err) {
      return refused('move', key, err, 'Could not read the sources.');
    }
    if (!keys) return fail(400, { move: { id: key, error: 'That source cannot move that way.' } });
    try {
      await orderLeadSources(event, keys);
    } catch (err) {
      return refused('move', key, err, 'Could not reorder the sources.');
    }
    return { moved: key };
  }
};
