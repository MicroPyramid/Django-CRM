import { fail } from '@sveltejs/kit';
import { EDITABLE_FIELDS, getLeadForEdit, updateLead } from '#lib/server/v2/leads.js';
import { readCustomFields, saveRefusal } from '#lib/server/v2/record-custom-fields.js';
import { getLeadSources } from '#lib/server/v2/lead-sources.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  const [lead, { sources }] = await Promise.all([
    getLeadForEdit({ cookies }, params.id),
    getLeadSources({ cookies })
  ]);
  return { ...lead, sources };
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * The form posts here. The client-side checks in `+page.svelte` mirror the
   * API's rules so somebody finds out before they press save. They are not
   * the thing that enforces them. Anything reaching this action is validated
   * again by the DRF serializer, and a request that skips the page entirely
   * meets exactly the same rules.
   *
   * Note what is *not* read out of the form: `org`, `created_by`, and the
   * conversion side-effects. Only the fields the form owns are picked out by
   * name, so a field appended to the POST body by hand is not forwarded.
   */
  save: async ({ cookies, params, request }) => {
    const form = await request.formData();

    // Only fields the form actually submitted. A field that is absent stays
    // absent all the way to the PATCH, where absent means "leave it alone",
    // which is how the disabled status select on a converted lead avoids
    // sending a value that `validate_status` would reject.
    /** @type {Record<string, any>} */
    const values = {};
    for (const field of EDITABLE_FIELDS) {
      if (form.has(field)) values[field] = form.get(field)?.toString().trim() ?? '';
    }

    /*
     * The owner is only sent when somebody actually changed it.
     *
     * `assigned_to` is many-to-many and this form offers a single select, so
     * sending it unconditionally rewrites the whole list from one value, a
     * lead with two people on it loses one every time anybody edits a phone
     * number. Found while wiring the pipeline, which has the same shape; the
     * two forms should keep behaving the same way.
     */
    const owner = form.get('assigned_to')?.toString().trim() ?? '';
    const ownerWas = form.get('assigned_to_original')?.toString().trim() ?? '';
    if (owner !== ownerWas) values.assigned_to = owner;

    const custom = await readCustomFields(cookies, 'Lead', form);
    if (custom.refusal)
      return fail(503, { values, message: custom.refusal.error, fieldErrors: {} });
    if (custom.values) values.custom_fields = custom.values;

    if (!values.first_name && !values.last_name) {
      return fail(400, {
        values,
        errors: { last_name: 'A lead needs a name to be findable. First or last will do.' }
      });
    }

    /** @type {any} */
    let result;
    try {
      result = await updateLead({ cookies }, params.id, values);
    } catch (/** @type {any} */ err) {
      const { error, fieldErrors } = saveRefusal(
        err,
        custom.definitions,
        'Could not save this lead.'
      );
      return fail(400, { values, message: error, fieldErrors });
    }

    // A save that also converted the lead (status -> "converted") carries the
    // three created records in `result`. An ordinary field save does not, so
    // these are null and the extra links never render.
    return {
      saved: true,
      account_id: result?.account_id ?? null,
      contact_id: result?.contact_id ?? null,
      opportunity_id: result?.opportunity_id ?? null
    };
  }
};
