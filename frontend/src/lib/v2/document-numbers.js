/**
 * Invoice and estimate numbers in the org's chosen format (#802), for a
 * preview only. The server assigns the real number on save
 * (`invoices.models._next_number`), counting what this org has already issued,
 * so a page can show the shape of the next number but never the number itself.
 *
 * A number is the prefix, then the date and a hyphen if the org dates its
 * numbers, then a counter padded to `number_padding` digits.
 */

/** `Org.NUMBER_DATE_PARTS`, in the order the settings form offers them. */
export const NUMBER_DATE_PARTS = [
  { value: 'NONE', label: 'No date, one running count' },
  { value: 'YEAR', label: 'Year, count restarts each year' },
  { value: 'MONTH', label: 'Year and month, count restarts each month' },
  { value: 'DAY', label: 'Full date, count restarts each day' }
];

/** How many digits of `YYYYMMDD` each date part keeps. */
const DATE_DIGITS = { NONE: 0, YEAR: 4, MONTH: 6, DAY: 8 };

/**
 * The server's prefix rule (`number_prefix_validator`): the number becomes a
 * PDF filename and an email subject, so nothing that means something in a
 * header or a path. A UX hint; the serializer is what refuses.
 */
export const NUMBER_PREFIX_PATTERN = /^[A-Za-z0-9_-]*$/;

/**
 * The part of a number before its counter. Mirrors `_number_series`.
 *
 * @param {string} prefix
 * @param {string} datePart one of `NUMBER_DATE_PARTS`
 * @param {string} today `YYYY-MM-DD` in the org's day (`todayIn`)
 */
export function numberSeries(prefix, datePart, today) {
  const digits = today.replace(/-/g, '').slice(0, DATE_DIGITS[datePart]);
  return digits ? `${prefix}${digits}-` : prefix;
}

/**
 * What a new number looks like in the format `settings` describe: the series
 * and its first counter. `settings` carries the five `/api/org/settings/`
 * fields, as stored or as a form holds them mid-edit.
 *
 * The starting number counts for undated invoices only, as on the server; a
 * form can still hold one after its date part changes, and the hidden field
 * sends 1 in that case. The width is clamped to the server's 1 to 10, so a
 * width still being typed cannot build an enormous string.
 *
 * @param {Record<string, any>} settings
 * @param {'invoice' | 'estimate'} kind
 * @param {string} today `YYYY-MM-DD` in the org's day
 */
export function exampleNumber(settings, kind, today) {
  const datePart = settings.number_date_part;
  const prefix =
    kind === 'invoice' ? settings.invoice_number_prefix : settings.estimate_number_prefix;
  const counter =
    kind === 'invoice' && datePart === 'NONE' ? Number(settings.invoice_number_start) || 1 : 1;
  const width = Math.min(Math.max(Number(settings.number_padding) || 1, 1), 10);
  return `${numberSeries(prefix, datePart, today)}${String(counter).padStart(width, '0')}`;
}

/**
 * The shape of the next number, with its counter left as `n`s: what a create
 * form can honestly promise before the server counts. `INV-2026-nnnn`.
 *
 * @param {Record<string, any>} settings
 * @param {'invoice' | 'estimate'} kind
 * @param {string} today `YYYY-MM-DD` in the org's day
 */
export function numberPattern(settings, kind, today) {
  const prefix =
    kind === 'invoice' ? settings.invoice_number_prefix : settings.estimate_number_prefix;
  return `${numberSeries(prefix, settings.number_date_part, today)}${'n'.repeat(settings.number_padding)}`;
}
