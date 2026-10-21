import { fail, redirect } from '@sveltejs/kit';
import {
  checkFieldKey,
  checkKey,
  createField,
  deleteObject,
  getObject,
  listFields,
  turnOffField,
  updateField,
  updateObject
} from '#lib/server/v2/custom-objects.js';
import { readableError } from '#lib/server/v2/form-errors.js';
import { readFieldForm, readObjectForm } from '#lib/server/v2/object-settings.js';
import { viewerIsAdmin } from '#lib/server/v2/organization.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  const key = checkKey(params.key);
  const [definition, fields] = await Promise.all([
    getObject({ cookies }, key),
    listFields({ cookies }, key)
  ]);
  return { definition, fields, can_edit: viewerIsAdmin(cookies) };
}

/**
 * Run a write and turn its failure into a `fail()` under the action's name.
 *
 * @param {string} name The action's namespace in `form`.
 * @param {string} forbidden What a 403 says.
 * @param {string} fallback What an unexplained failure says.
 * @param {() => Promise<unknown>} write
 * @param {Record<string, unknown>} [values] Echoed back on a refusal.
 */
async function attempt(name, forbidden, fallback, write, values) {
  try {
    await write();
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) {
      return fail(403, { [name]: { error: err?.body?.detail ?? forbidden } });
    }
    const error =
      typeof err?.body?.detail === 'string' ? err.body.detail : readableError(err, fallback);
    return fail(400, { [name]: { error, values } });
  }
  return null;
}

/** @param {FormData} form */
const fieldKeyOf = (form) => checkFieldKey(form.get('field_key')?.toString() ?? '');

/** @type {import('./$types').Actions} */
export const actions = {
  async update(event) {
    const key = checkKey(event.params.key);
    const body = readObjectForm(await event.request.formData(), { creating: false });
    return (
      (await attempt(
        'update',
        'Only an admin can change custom objects.',
        'Could not save the object.',
        () => updateObject(event, key, body),
        body
      )) ?? { updated: true }
    );
  },

  async archive(event) {
    const key = checkKey(event.params.key);
    return (
      (await attempt(
        'archive',
        'Only an admin can archive custom objects.',
        'Could not archive the object.',
        () => deleteObject(event, key)
      )) ?? { archived: true }
    );
  },

  async restore(event) {
    const key = checkKey(event.params.key);
    return (
      (await attempt(
        'restore',
        'Only an admin can restore custom objects.',
        'Could not restore the object.',
        () => updateObject(event, key, { is_active: true })
      )) ?? { restored: true }
    );
  },

  async destroy(event) {
    const key = checkKey(event.params.key);
    const failed = await attempt(
      'destroy',
      'Only an admin can delete custom objects.',
      'Could not delete the object.',
      () => deleteObject(event, key)
    );
    if (failed) return failed;
    redirect(303, '/settings/objects');
  },

  async createField(event) {
    const key = checkKey(event.params.key);
    const body = readFieldForm(await event.request.formData(), { creating: true });
    return (
      (await attempt(
        'createField',
        'Only an admin can add fields.',
        'Could not add the field.',
        () => createField(event, key, body),
        body
      )) ?? { fieldCreated: true }
    );
  },

  async updateField(event) {
    const key = checkKey(event.params.key);
    const form = await event.request.formData();
    const fieldKey = fieldKeyOf(form);
    const body = readFieldForm(form, { creating: false });
    return (
      (await attempt(
        'updateField',
        'Only an admin can change fields.',
        'Could not save the field.',
        () => updateField(event, key, fieldKey, body),
        body
      )) ?? { fieldUpdated: true }
    );
  },

  async fieldOff(event) {
    const key = checkKey(event.params.key);
    const fieldKey = fieldKeyOf(await event.request.formData());
    return (
      (await attempt(
        'fieldOff',
        'Only an admin can turn fields off.',
        'Could not turn the field off.',
        () => turnOffField(event, key, fieldKey)
      )) ?? { fieldOff: true }
    );
  },

  async fieldOn(event) {
    const key = checkKey(event.params.key);
    const fieldKey = fieldKeyOf(await event.request.formData());
    return (
      (await attempt(
        'fieldOn',
        'Only an admin can turn fields on.',
        'Could not turn the field on.',
        () => updateField(event, key, fieldKey, { is_active: true })
      )) ?? { fieldOn: true }
    );
  }
};
