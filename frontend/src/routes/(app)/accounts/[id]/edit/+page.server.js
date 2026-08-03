import { fail, redirect } from '@sveltejs/kit';
import { EDITABLE_FIELDS, getAccountForEdit, updateAccount } from '$lib/server/v2/accounts.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  return await getAccountForEdit({ cookies }, params.id);
}

/** @type {import('./$types').Actions} */
export const actions = {
  save: async ({ cookies, params, request }) => {
    const form = await request.formData();

    /** @type {Record<string, string>} */
    const values = {};
    for (const field of EDITABLE_FIELDS) {
      // Only fields the form actually submitted. A control that is absent or
      // disabled sends nothing, and "nothing" is how PATCH is told to leave a
      // field alone. See `updateAccount`.
      if (form.has(field)) values[field] = form.get(field)?.toString().trim() ?? '';
    }

    /*
     * The owner is only sent when somebody actually changed it.
     *
     * `assigned_to` is many-to-many and this form offers a single select, so
     * sending it unconditionally rewrites the whole list from one value, an
     * account with two people on it silently loses one every time anybody
     * edits the phone number. The hidden `assigned_to_original` is what makes
     * "nobody touched this" distinguishable from "somebody chose this".
     */
    const owner = form.get('assigned_to')?.toString().trim() ?? '';
    const ownerWas = form.get('assigned_to_original')?.toString().trim() ?? '';
    if (owner !== ownerWas) values.assigned_to = owner;

    try {
      await updateAccount({ cookies }, params.id, values);
    } catch (/** @type {any} */ err) {
      return fail(400, { values, error: readableError(err, 'Could not save this account.') });
    }

    redirect(303, `/accounts/${params.id}`);
  }
};
