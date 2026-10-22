/**
 * Field rendering and form collection shared by every page that edits
 * per-org custom fields (leads, custom object records). Server-only by
 * location, but imports only a browser-safe helper, so it is also safe to unit test in Node.
 */
import { sameIds } from '#lib/v2/pickers.js';

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
 * Pair definitions with a record's stored values for the detail page.
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
    let options = d.options ?? [];
    // A select with no option for the stored value submits nothing and clears it.
    if (
      d.field_type === 'dropdown' &&
      raw !== null &&
      raw !== undefined &&
      raw !== '' &&
      !options.some((/** @type {any} */ o) => o.value === raw)
    ) {
      options = [...options, { value: raw, label: `${raw} (no longer an option)` }];
    }
    return {
      key: d.key,
      label: d.label,
      field_type: d.field_type,
      options,
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

/**
 * Link fields of a `Field` list, paired with the record's `links` answer.
 * A one-record field held by a link the caller cannot open is read-only: the
 * server refuses a write to it, so the form shows no input.
 *
 * @param {any[]} fields
 * @param {Record<string, any> | null | undefined} links
 */
export function linkFieldsForEdit(fields, links) {
  const held = links ?? {};
  return fields
    .filter((f) => f.field_type === 'link')
    .map((f) => {
      const entry = held[f.key] ?? {};
      const many = Boolean(f.many);
      const hidden = entry.hidden ?? 0;
      return {
        key: f.key,
        label: f.label,
        target: f.target,
        many,
        records: /** @type {{ id: string, name: string }[]} */ (entry.records ?? []),
        hidden,
        readOnly: !many && hidden > 0
      };
    });
}

/**
 * @param {string[]} ids
 * @param {string} was Comma-joined ids the page showed.
 */
const differs = (ids, was) => !sameIds(ids.filter(Boolean), was.split(',').filter(Boolean));

/**
 * Link ids to send, keyed by field, only for fields whose ids changed since
 * the page rendered. A field without a `link_<key>__was` input (read-only) is
 * never sent.
 *
 * @param {FormData} form
 * @param {{ key: string }[]} linkFields
 * @returns {Record<string, string[]>}
 */
export function collectLinks(form, linkFields) {
  /** @type {Record<string, string[]>} */
  const out = {};
  for (const { key } of linkFields) {
    const was = form.get(`link_${key}__was`);
    if (was === null) continue;
    const ids = form.getAll(`link_${key}`).map(String);
    if (differs(ids, String(was))) out[key] = ids.filter(Boolean);
  }
  return out;
}

/**
 * Assignee ids to send, or `undefined` when they are unchanged. A form with no
 * `assigned_to__was` (a create form) always sends what was picked.
 *
 * @param {FormData} form
 * @returns {string[] | undefined}
 */
export function collectAssignees(form) {
  const ids = form.getAll('assigned_to').map(String);
  const was = form.get('assigned_to__was');
  if (was === null) return ids;
  return differs(ids, String(was)) ? ids : undefined;
}
