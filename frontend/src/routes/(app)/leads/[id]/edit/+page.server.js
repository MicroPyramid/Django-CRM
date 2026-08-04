import { fail } from '@sveltejs/kit';
import { EDITABLE_FIELDS, getLeadForEdit, updateLead } from '$lib/server/v2/leads.js';
import { collectFromForm, leadFieldDefinitions } from '$lib/server/v2/lead-custom-fields.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  return await getLeadForEdit({ cookies }, params.id);
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

    /*
     * Custom fields are read against the org's own definitions, re-fetched
     * here rather than trusted from the body: the keys come from the server's
     * list, so a `cf_` input appended to the POST by hand names nothing and is
     * never read. The API is still the authority; `validate_payload` drops
     * unknown keys and coerces every value, but the form has no reason to
     * forward something it did not offer.
     *
     * Only sent when the org actually defines Lead fields, so an org with none
     * PATCHes exactly the body it did before.
     */
    const definitions = await leadFieldDefinitions(cookies);
    if (definitions.length > 0) {
      values.custom_fields = collectFromForm(form, definitions);
    }

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
      // `api-helpers` flattens DRF's field errors into one string. Surface it
      // rather than a generic failure: "email: lead with this email already
      // exists" tells somebody what to change; "Could not save" does not.
      return fail(400, { values, message: String(err?.message ?? 'Could not save this lead.') });
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
