import { fail, redirect } from '@sveltejs/kit';
import { getTicketForEdit, updateTicket } from '$lib/server/v2/tickets.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** Scalars this form owns. `account` is not among them. See the loader note. */
const FIELDS = ['name', 'status', 'priority', 'case_type', 'description', 'closed_on'];

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  return await getTicketForEdit({ cookies }, params.id);
}

/** @type {import('./$types').Actions} */
export const actions = {
  save: async ({ cookies, params, request }) => {
    const form = await request.formData();

    /** @type {Record<string, any>} */
    const values = {};
    for (const field of FIELDS) {
      // Only fields the form actually submitted. A control that is absent or
      // disabled sends nothing, and "nothing" is how PATCH is told to leave a
      // field alone. See `updateTicket`.
      if (form.has(field)) values[field] = form.get(field)?.toString().trim() ?? '';
    }

    /*
     * The owner is only sent when somebody actually changed it.
     *
     * `assigned_to` is many-to-many and this form offers a single select, so
     * sending it unconditionally rewrites the whole list from one value, a
     * ticket with two people on it silently loses one every time anybody fixes
     * a typo in the subject. The hidden `assigned_to_original` is what makes
     * "nobody touched this" distinguishable from "somebody chose this".
     */
    const owner = form.get('assigned_to')?.toString().trim() ?? '';
    const ownerWas = form.get('assigned_to_original')?.toString().trim() ?? '';
    if (owner !== ownerWas) values.assigned_to = owner;

    /*
     * Same reasoning for the people on the ticket, one step harder: a
     * multi-select submits nothing when everything is deselected, which is
     * indistinguishable from a field the form does not own. The hidden
     * `contacts_present` marker is what tells them apart, so "remove the last
     * contact" is a thing this form can express.
     */
    if (form.has('contacts_present')) {
      values.contacts = form.getAll('contacts').map((id) => id.toString());
    }

    try {
      await updateTicket({ cookies }, params.id, values);
    } catch (/** @type {any} */ err) {
      return fail(400, { values, error: readableError(err, 'Could not save this ticket.') });
    }

    redirect(303, `/tickets/${params.id}`);
  }
};
