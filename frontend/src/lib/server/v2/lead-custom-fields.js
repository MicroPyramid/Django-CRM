/**
 * Per-org custom fields on a Lead: the definitions and a record's values.
 *
 * Server-only. Vertical packs create `CustomFieldDefinition` rows targeting
 * `Lead` (every shipped pack does; none targets another entity), and the
 * applier writes matching values into `Lead.custom_fields`. Until this module
 * existed both ends were invisible: the definitions showed only under
 * Settings → Custom fields, and the values sat in the JSON column with no page
 * rendering them. For a real-estate org "Budget (max)" and "Preferred
 * location" ARE the record, so a lead page that omits them omits the point.
 *
 * `GET /custom-fields/` is `(IsAuthenticated, HasOrgContext)` with no admin
 * gate. Definitions are shared config, read by any member and written only by
 * an admin, so this is safe to call from a page every member can open. It
 * returns every definition for the org including inactive ones and every
 * target; the filtering to active Lead fields happens here.
 *
 * On the way back in, `common.custom_fields.validate_payload` is the authority:
 * `LeadDetailView.patch` runs it over the submitted object, drops keys with no
 * definition and coerces each value to its declared type. The allow-list built
 * here is a convenience for the form, never the control. A forged key is
 * discarded server-side whatever this file does.
 */
import { apiRequest } from '#lib/api-helpers.js';

/**
 * Active custom-field definitions targeting Lead, in display order.
 *
 * A failure here returns [] rather than throwing: custom fields are an
 * enhancement to the lead page, and an org with none is the common case, so a
 * definitions call that fails should cost the reader the extra block, not the
 * lead they were trying to open.
 *
 * @param {import('@sveltejs/kit').Cookies} cookies
 * @returns {Promise<any[]>}
 */
export async function leadFieldDefinitions(cookies) {
  try {
    // `include_counts=false` matters: without it the endpoint computes
    // `records_missing_value` for every definition, which is one COUNT over
    // the org's entire Lead table each, N+1 full scans on every lead page
    // view, to render labels that need none of them. The filters are applied
    // server-side too, so this asks for the smallest useful answer.
    const response = await apiRequest(
      '/custom-fields/?target_model=Lead&active_only=true&include_counts=false',
      {},
      { cookies }
    );
    return (response.definitions ?? []).sort(
      (/** @type {any} */ a, /** @type {any} */ b) =>
        (a.display_order ?? 0) - (b.display_order ?? 0)
    );
  } catch {
    return [];
  }
}

export {
  displayValue,
  pairForDisplay,
  pairForEdit,
  collectFromForm
} from '#lib/server/v2/record-fields.js';
