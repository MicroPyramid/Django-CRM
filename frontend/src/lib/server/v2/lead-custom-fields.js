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
import { apiRequest } from '$lib/api-helpers.js';

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

/**
 * Render one stored value for reading.
 *
 * Values arrive already coerced by `_coerce_value`: number as a JSON number,
 * checkbox as a real boolean, date as a YYYY-MM-DD string, so this formats
 * rather than parses. A dropdown stores its `value`; the human-facing `label`
 * lives on the definition, so it is looked up here instead of showing the raw
 * key.
 *
 * @param {any} definition
 * @param {any} value
 * @returns {string}
 */
export function displayValue(definition, value) {
  if (value === null || value === undefined || value === '') return '';

  switch (definition.field_type) {
    case 'checkbox':
      return value ? 'Yes' : 'No';
    case 'number':
      return typeof value === 'number' ? value.toLocaleString() : String(value);
    case 'dropdown': {
      const match = (definition.options ?? []).find((/** @type {any} */ o) => o.value === value);
      return match?.label ?? String(value);
    }
    default:
      return String(value);
  }
}

/**
 * Pair definitions with a lead's stored values for the detail page.
 *
 * Every active definition appears, including the ones this record has no value
 * for. A blank "Possession by" is information, and a list that silently omits
 * unfilled fields hides what the org decided it tracks. `filled` lets the page
 * decide whether the block is worth showing at all.
 *
 * @param {any[]} definitions
 * @param {Record<string, any> | null | undefined} values
 */
export function pairForDisplay(definitions, values) {
  const stored = values ?? {};
  return definitions.map((d) => {
    const raw = stored[d.key];
    return {
      key: d.key,
      label: d.label,
      field_type: d.field_type,
      value: displayValue(d, raw),
      filled: raw !== null && raw !== undefined && raw !== ''
    };
  });
}

/**
 * Shape the definitions and current values for the edit form.
 *
 * A checkbox is normalised to a real boolean and everything else to a string,
 * because that is what the inputs bind to. `''` for an unset field means the
 * input renders empty and submits empty, which `_coerce_value` maps back to
 * `None`, so clearing a field works without a separate "remove" control.
 *
 * @param {any[]} definitions
 * @param {Record<string, any> | null | undefined} values
 */
export function pairForEdit(definitions, values) {
  const stored = values ?? {};
  return definitions.map((d) => {
    const raw = stored[d.key];
    return {
      key: d.key,
      label: d.label,
      field_type: d.field_type,
      options: d.options ?? [],
      is_required: d.is_required ?? false,
      value:
        d.field_type === 'checkbox'
          ? Boolean(raw)
          : raw === null || raw === undefined
            ? ''
            : String(raw)
    };
  });
}

/**
 * Collect `cf_<key>` inputs off a submitted form into a custom_fields object.
 *
 * Driven by the definition list, not by what the body happens to carry: a key
 * with no active definition is never read, and an unchecked checkbox, which
 * submits nothing at all in HTML. Becomes an explicit `false` rather than
 * silently keeping its previous value. Without that, a checkbox could be
 * ticked but never unticked.
 *
 * @param {FormData} form
 * @param {any[]} definitions
 * @returns {Record<string, any>}
 */
export function collectFromForm(form, definitions) {
  /** @type {Record<string, any>} */
  const out = {};
  for (const d of definitions) {
    const field = `cf_${d.key}`;
    if (d.field_type === 'checkbox') {
      out[d.key] = form.get(field) !== null;
      continue;
    }
    if (!form.has(field)) continue;
    const raw = form.get(field)?.toString().trim() ?? '';
    out[d.key] = raw === '' ? null : raw;
  }
  return out;
}
