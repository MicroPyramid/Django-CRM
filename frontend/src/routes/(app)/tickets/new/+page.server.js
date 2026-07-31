import { fail, redirect } from '@sveltejs/kit';
import { createTicket, getTicketFormOptions } from '$lib/server/v2/tickets.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, url }) {
  return await getTicketFormOptions({ cookies }, url.searchParams.get('account'));
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ cookies, request }) => {
    const form = await request.formData();

    /** @type {Record<string, any>} */
    const values = {};
    for (const field of ['name', 'status', 'priority', 'case_type', 'description', 'account']) {
      values[field] = form.get(field)?.toString().trim() ?? '';
    }

    const owner = form.get('assigned_to')?.toString().trim() ?? '';
    if (owner) values.assigned_to = owner;
    const contacts = form.getAll('contacts').map((id) => id.toString());
    if (contacts.length) values.contacts = contacts;

    if (!values.name) {
      return fail(400, { values, error: 'A ticket needs a subject.' });
    }

    /** @type {any} */
    let created;
    try {
      created = await createTicket({ cookies }, values);
    } catch (/** @type {any} */ err) {
      return fail(400, { values, error: readableError(err, 'Could not raise this ticket.') });
    }

    // `CaseListView.post` returns the new id, so this lands on the ticket
    // rather than back at a queue where the user has to go and find it.
    redirect(303, created?.id ? `/tickets/${created.id}` : '/tickets');
  }
};
