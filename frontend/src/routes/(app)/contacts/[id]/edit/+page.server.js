import { fail, redirect } from '@sveltejs/kit';
import { EDITABLE_FIELDS, getContactForEdit, updateContact } from '$lib/server/v2/contacts.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** Fields the form submits as checkboxes: absent means false, not "unchanged". */
const FLAGS = ['do_not_call', 'is_active'];

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  return await getContactForEdit({ cookies }, params.id);
}

/** @type {import('./$types').Actions} */
export const actions = {
  save: async ({ cookies, params, request }) => {
    const form = await request.formData();

    /** @type {Record<string, any>} */
    const values = {};
    for (const field of EDITABLE_FIELDS) {
      if (FLAGS.includes(field)) continue;
      // Only fields the form actually submitted. A control that is absent or
      // disabled sends nothing, and "nothing" is how PATCH is told to leave a
      // field alone. See `updateContact`.
      if (form.has(field)) values[field] = form.get(field)?.toString().trim() ?? '';
    }

    /*
     * A cleared checkbox submits nothing at all, so "absent means leave alone"
     * is exactly wrong for these two: it would make "do not call" impossible to
     * switch off. Each one is paired with a hidden field that is always sent,
     * so the form can distinguish an unticked box from a field it does not own.
     */
    for (const flag of FLAGS) {
      if (form.has(`${flag}_present`)) values[flag] = form.get(flag) === 'on';
    }

    /*
     * The owner is only sent when somebody actually changed it.
     *
     * `assigned_to` is many-to-many and this form offers a single select, so
     * sending it unconditionally rewrites the whole list from one value, a
     * contact with two people on it silently loses one every time anybody edits
     * a phone number. The hidden `assigned_to_original` is what makes "nobody
     * touched this" distinguishable from "somebody chose this".
     */
    const owner = form.get('assigned_to')?.toString().trim() ?? '';
    const ownerWas = form.get('assigned_to_original')?.toString().trim() ?? '';
    if (owner !== ownerWas) values.assigned_to = owner;

    try {
      await updateContact({ cookies }, params.id, values);
    } catch (/** @type {any} */ err) {
      return fail(400, { values, error: readableError(err, 'Could not save this contact.') });
    }

    redirect(303, `/contacts/${params.id}`);
  }
};
