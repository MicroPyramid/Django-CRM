import { fail, redirect } from '@sveltejs/kit';
import { EDITABLE_FIELDS, createDeal, getDealFormOptions } from '$lib/server/v2/deals.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  // The currency hint under the amount comes from the shell (`data.org.currency`
  // via `(app)/+layout.server.js`). It is the currency this deal will be created
  // in: the form has no currency field, so the serializer stamps the org default
  // (`OpportunityCreateSerializer.create`).
  return await getDealFormOptions(event);
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
      created = await createDeal(event, values);
    } catch (/** @type {any} */ err) {
      // `values` goes back so a rejected form is not a blank form. Retyping
      // eight fields because the ninth collided is how people learn to
      // distrust a create page.
      return fail(400, { values, error: String(err?.message ?? 'Could not create the deal.') });
    }

    // Straight to the deal, not back to the list: the next thing anyone does
    // after creating one is look at it.
    redirect(303, created?.id ? `/pipeline/${created.id}` : '/pipeline');
  }
};
