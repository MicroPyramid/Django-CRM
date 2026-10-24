import { fail, redirect } from '@sveltejs/kit';
import { EDITABLE_FIELDS, createLead, getLeadFormOptions } from '#lib/server/v2/leads.js';
import { getLeadSources } from '#lib/server/v2/lead-sources.js';
import {
  fieldsForNew,
  readCustomFields,
  saveRefusal
} from '#lib/server/v2/record-custom-fields.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  const [options, { sources }, customFields] = await Promise.all([
    getLeadFormOptions(event),
    getLeadSources(event),
    fieldsForNew(event.cookies, 'Lead')
  ]);
  return { ...options, sources, customFields };
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
    const custom = await readCustomFields(event.cookies, 'Lead', form);
    if (custom.refusal) return fail(503, { values, ...custom.refusal });
    if (custom.values) values.custom_fields = custom.values;

    /** @type {any} */
    let created;
    try {
      created = await createLead(event, values);
    } catch (/** @type {any} */ err) {
      // Values go back so a rejected form is not a blank form.
      return fail(400, {
        values,
        ...saveRefusal(err, custom.definitions, 'Could not create the lead.')
      });
    }

    redirect(303, created?.id ? `/leads/${created.id}` : '/leads');
  }
};
