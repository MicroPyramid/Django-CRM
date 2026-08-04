import { fail } from '@sveltejs/kit';
import {
  getCustomFields,
  createCustomField,
  updateCustomField,
  deactivateCustomField
} from '$lib/server/v2/custom-fields.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getCustomFields({ cookies });
}

/**
 * Read the repeated option rows back into `{ value, label }` pairs.
 *
 * The form renders one hidden `option_value` and one text `option_label` per
 * row, so `getAll` returns two parallel arrays. A blank value marks a row the
 * admin just added; `createCustomField` slugifies a value for it. A non-blank
 * one is an existing option whose value is referenced by every record already
 * holding it, and it travels back unchanged.
 *
 * @param {FormData} form
 */
function readOptions(form) {
  const values = form.getAll('option_value').map((v) => v.toString());
  const labels = form.getAll('option_label').map((v) => v.toString());
  return labels.map((label, i) => ({ value: values[i] ?? '', label }));
}

/** @param {FormData} form */
function readValues(form) {
  return {
    target_model: form.get('target_model')?.toString() ?? '',
    key: form.get('key')?.toString().trim() ?? '',
    label: form.get('label')?.toString().trim() ?? '',
    field_type: form.get('field_type')?.toString() ?? '',
    is_required: form.get('is_required') === 'true',
    is_filterable: form.get('is_filterable') === 'true',
    display_order: form.get('display_order')?.toString() ?? '0',
    options: readOptions(form)
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  // Admin-only server-side (`CustomFieldDefinitionListCreateView.post` calls
  // `_is_admin` first). `can_edit` only hides the control.
  async create(event) {
    const form = await event.request.formData();
    const values = readValues(form);
    try {
      await createCustomField(event, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { create: { error: 'Only an admin can add custom fields.' } });
      }
      return fail(400, { create: { error: readableError(err, 'Could not add the field.') } });
    }
    return { created: true };
  },

  async update(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    const values = readValues(form);
    try {
      await updateCustomField(event, id, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { update: { error: 'Only an admin can change custom fields.' } });
      }
      return fail(400, { update: { error: readableError(err, 'Could not save the field.') } });
    }
    return { updated: true };
  },

  async deactivate(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    try {
      await deactivateCustomField(event, id);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { deactivate: { error: 'Only an admin can turn custom fields off.' } });
      }
      return fail(400, {
        deactivate: { error: readableError(err, 'Could not turn the field off.') }
      });
    }
    return { deactivated: true };
  },

  // A field's own action, not a reuse of `update`. `readValues` builds a full
  // field payload from the form, and this control only ever submits an id: if
  // it posted through `update`, the missing `label` would read back as `''`
  // (FormData has no key for it, `readValues` falls back to an empty string,
  // not `undefined`) and `buildBody` would forward that empty string, since
  // its allow-list only skips a field that is `undefined`. That would blank
  // the label on every reactivation. Calling `updateCustomField` directly with
  // only `{ is_active: true }` sidesteps `readValues` entirely, so the PUT
  // body is `{ is_active: true }` and nothing else.
  async activate(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    try {
      await updateCustomField(event, id, { is_active: true });
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { activate: { error: 'Only an admin can turn custom fields on.' } });
      }
      return fail(400, {
        activate: { error: readableError(err, 'Could not turn the field on.') }
      });
    }
    return { activated: true };
  }
};
