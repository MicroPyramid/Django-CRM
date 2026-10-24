import { fail, redirect } from '@sveltejs/kit';
import { EDITABLE_FIELDS, createDeal, getDealFormOptions } from '#lib/server/v2/deals.js';
import { getLeadSources } from '#lib/server/v2/lead-sources.js';
import {
  fieldsForNew,
  readCustomFields,
  saveRefusal
} from '#lib/server/v2/record-custom-fields.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  // The currency hint under the amount comes from the shell (`data.org.currency`
  // via `(app)/+layout.server.js`). It is the currency this deal will be created
  // in: the form has no currency field, so the serializer stamps the org default
  // (`OpportunityCreateSerializer.create`).
  const [options, sources, customFields] = await Promise.all([
    getDealFormOptions(event),
    getLeadSources(event),
    fieldsForNew(event.cookies, 'Opportunity')
  ]);
  return { ...options, sources: sources.sources, sourcesLive: sources.live, customFields };
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

    const custom = await readCustomFields(event.cookies, 'Opportunity', form);
    if (custom.refusal) return fail(503, { values, ...custom.refusal });
    if (custom.values) values.custom_fields = custom.values;

    /** @type {any} */
    let created;
    try {
      created = await createDeal(event, values);
    } catch (/** @type {any} */ err) {
      // `values` goes back so a rejected form is not a blank form. Retyping
      // eight fields because the ninth collided is how people learn to
      // distrust a create page.
      return fail(400, {
        values,
        ...saveRefusal(err, custom.definitions, 'Could not create the deal.')
      });
    }

    // Straight to the deal, not back to the list: the next thing anyone does
    // after creating one is look at it.
    redirect(303, created?.id ? `/pipeline/${created.id}` : '/pipeline');
  }
};
