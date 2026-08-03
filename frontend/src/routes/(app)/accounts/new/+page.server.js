import { fail, redirect } from '@sveltejs/kit';
import { EDITABLE_FIELDS, createAccount, getAccountFormOptions } from '$lib/server/v2/accounts.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return await getAccountFormOptions({ cookies });
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ cookies, request }) => {
    const form = await request.formData();

    /** @type {Record<string, string>} */
    const values = {};
    for (const field of EDITABLE_FIELDS) {
      if (form.has(field)) values[field] = form.get(field)?.toString().trim() ?? '';
    }
    // On create there is nothing to preserve, so the owner is always sent,
    // including empty, which is how an account is deliberately left unowned.
    values.assigned_to = form.get('assigned_to')?.toString().trim() ?? '';

    /** @type {any} */
    let created;
    try {
      created = await createAccount({ cookies }, values);
    } catch (/** @type {any} */ err) {
      return fail(400, { values, error: readableError(err, 'Could not create this account.') });
    }

    // The API returns the new id. Landing on the account is the point of
    // creating one; landing back on the list makes you go and find it.
    redirect(303, created?.id ? `/accounts/${created.id}` : '/accounts');
  }
};
