/**
 * Whether a time entry is billed. `invoiced` stays true while Invoices is
 * switched off, when `invoice` is emptied; an older answer carries only `invoice`.
 *
 * @param {{ invoiced?: boolean, invoice?: any } | null | undefined} entry
 * @returns {boolean}
 */
export function isBilled(entry) {
  return entry?.invoiced === true || entry?.invoice != null;
}
