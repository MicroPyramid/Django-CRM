import { fail, redirect } from '@sveltejs/kit';
import { EDITABLE_FIELDS, createLead, getLeadFormOptions } from '$lib/server/v2/leads.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  return await getLeadFormOptions(event);
}

/** @type {import('./$types').Actions} */
export const actions = {
  async create(event) {
    const form = await event.request.formData();

    /** @type {Record<string, any>} */
    const values = {};
    for (const field of [...EDITABLE_FIELDS, 'assigned_to']) {
      if (form.has(field)) values[field] = form.get(field)?.toString().trim() ?? '';
    }

    /** @type {any} */
    let created;
    try {
      created = await createLead(event, values);
    } catch (/** @type {any} */ err) {
      // Values go back so a rejected form is not a blank form.
      return fail(400, { values, error: readableError(err, 'Could not create the lead.') });
    }

    redirect(303, created?.id ? `/leads/${created.id}` : '/leads');
  }
};
