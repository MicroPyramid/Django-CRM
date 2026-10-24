import { fail, redirect } from '@sveltejs/kit';
import { EDITABLE_FIELDS, createAccount, getAccountFormOptions } from '#lib/server/v2/accounts.js';
import {
  fieldsForNew,
  readCustomFields,
  saveRefusal
} from '#lib/server/v2/record-custom-fields.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  const [options, customFields] = await Promise.all([
    getAccountFormOptions({ cookies }),
    fieldsForNew(cookies, 'Account')
  ]);
  return { ...options, customFields };
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ cookies, request }) => {
    const form = await request.formData();

    /** @type {Record<string, any>} */
    const values = {};
    for (const field of EDITABLE_FIELDS) {
      if (form.has(field)) values[field] = form.get(field)?.toString().trim() ?? '';
    }
    // On create there is nothing to preserve, so the owner is always sent,
    // including empty, which is how an account is deliberately left unowned.
    values.assigned_to = form.get('assigned_to')?.toString().trim() ?? '';

    const custom = await readCustomFields(cookies, 'Account', form);
    if (custom.refusal) return fail(503, { values, ...custom.refusal });
    if (custom.values) values.custom_fields = custom.values;

    /** @type {any} */
    let created;
    try {
      created = await createAccount({ cookies }, values);
    } catch (/** @type {any} */ err) {
      return fail(400, {
        values,
        ...saveRefusal(err, custom.definitions, 'Could not create this account.')
      });
    }

    // The API returns the new id. Landing on the account is the point of
    // creating one; landing back on the list makes you go and find it.
    redirect(303, created?.id ? `/accounts/${created.id}` : '/accounts');
  }
};
