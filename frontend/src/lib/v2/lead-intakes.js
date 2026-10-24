/**
 * Lead webhooks (`/api/leads/intakes/`) as the Lead capture pages read them.
 *
 * Browser-safe, so the pages and tests can import it. An intake is a public
 * URL that turns each post into a lead; its mapping says which field of the
 * post fills which lead field. The server validates every mapping target, so
 * the lists here only decide what the editor offers.
 */
import { WEBFORM_LEAD_FIELDS } from '#lib/v2/webform-fields.js';

/** `LeadIntake.preset` choices, in the order the create panel offers them. */
export const INTAKE_PRESETS = [
  { value: 'generic', label: 'Any tool that posts JSON or a form' },
  { value: 'google_ads', label: 'Google Ads lead form' },
  { value: 'tally', label: 'Tally' },
  { value: 'gravity_forms', label: 'Gravity Forms' }
];

/** @param {string | null | undefined} preset */
export function presetLabel(preset) {
  return INTAKE_PRESETS.find((p) => p.value === preset)?.label ?? 'Any tool';
}

/** The source a new webhook starts with, by preset, when the org has it. */
const PRESET_SOURCE = /** @type {Record<string, string>} */ ({
  generic: 'web form',
  google_ads: 'google ads',
  tally: 'web form',
  gravity_forms: 'web form'
});

/**
 * @param {string} preset
 * @param {{ key: string, is_active?: boolean }[]} sources
 * @returns {string} the preset's usual source key when it is active, else ''
 */
export function presetSource(preset, sources) {
  const key = PRESET_SOURCE[preset];
  return key && (sources ?? []).some((s) => s.key === key && s.is_active !== false) ? key : '';
}

/**
 * How a mapping names a custom field. Lead columns are named as web forms
 * name them (`first_name`); a custom field is its definition key behind this.
 */
export const CUSTOM_TARGET_PREFIX = 'custom_fields.';

/**
 * What a mapping row may fill: the web forms' lead columns, then the org's
 * active lead custom fields.
 *
 * @param {{ key: string, label: string }[]} customFields
 * @returns {{ value: string, label: string }[]}
 */
export function mappingTargets(customFields) {
  return [
    ...WEBFORM_LEAD_FIELDS.map((f) => ({ value: f.value, label: f.label })),
    ...(customFields ?? []).map((f) => ({
      value: `${CUSTOM_TARGET_PREFIX}${f.key}`,
      label: f.label
    }))
  ];
}

/**
 * The targets plus any a stored row names that the list cannot offer (a
 * preset's own target, or a custom field turned off since), so the row's
 * select keeps its value and a save does not drop it.
 *
 * @param {{ value: string, label: string }[]} targets
 * @param {{ from: string, to: string }[]} mapping
 */
export function targetsFor(targets, mapping) {
  const known = new Set(targets.map((t) => t.value));
  const extra = [];
  for (const row of mapping ?? []) {
    if (row?.to && !known.has(row.to)) {
      known.add(row.to);
      extra.push({ value: row.to, label: row.to });
    }
  }
  return [...targets, ...extra];
}

/**
 * Rows as the API takes them: trimmed strings, both halves set, nothing else.
 *
 * @param {any} rows
 * @returns {{ from: string, to: string }[]}
 */
export function cleanMapping(rows) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((r) => ({
      from: typeof r?.from === 'string' ? r.from.trim() : '',
      to: typeof r?.to === 'string' ? r.to.trim() : ''
    }))
    .filter((r) => r.from && r.to);
}

/** @typedef {'moss' | 'ink' | 'slate' | 'rust' | 'clay'} Tone */

const RESULTS = /** @type {Record<string, { label: string, tone: Tone }>} */ ({
  created: { label: 'Created', tone: 'moss' },
  merged: { label: 'Merged', tone: 'ink' },
  duplicate: { label: 'Duplicate', tone: 'slate' },
  test: { label: 'Test', tone: 'slate' },
  rejected: { label: 'Rejected', tone: 'rust' }
});

/**
 * @param {string} result a delivery's `result`
 * @returns {{ label: string, tone: Tone }}
 */
export function deliveryResult(result) {
  return RESULTS[result] ?? { label: result || 'Unknown', tone: 'slate' };
}

/**
 * @param {{ is_active?: boolean, last_received_at?: string | null }} intake
 * @returns {{ label: string, tone: 'moss' | 'slate' }}
 */
export function intakeState(intake) {
  if (!intake?.is_active) return { label: 'Off', tone: 'slate' };
  if (!intake.last_received_at) return { label: 'Waiting', tone: 'slate' };
  return { label: 'Receiving', tone: 'moss' };
}
