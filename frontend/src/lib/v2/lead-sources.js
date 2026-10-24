/**
 * The org's lead sources as pickers, filters and labels read them.
 *
 * Browser-safe, so `.svelte` files and tests can import it. The list comes
 * from `GET /api/leads/sources/` (`#lib/server/v2/lead-sources.js`); a source
 * is `{ id, key, label, is_active, order }` and a record stores its `key`.
 */

/**
 * What an API without `/leads/sources/` accepts: the old fixed list, keys
 * exactly as that API validates them. `compaign` is its stored spelling;
 * the new API migrates it to `campaign`, and only the new API has the list.
 */
export const LEGACY_LEAD_SOURCES = [
  ['call', 'Call'],
  ['email', 'Email'],
  ['existing customer', 'Existing customer'],
  ['partner', 'Partner'],
  ['public relations', 'Public relations'],
  ['compaign', 'Campaign'],
  ['other', 'Other']
].map(([key, label], order) => ({ id: null, key, label, is_active: true, order }));

/** @typedef {{ id: string | null, key: string, label: string, is_active: boolean, order: number }} LeadSource */

/**
 * @param {LeadSource[] | null | undefined} sources
 * @param {string | null | undefined} key
 * @returns {string} the label, the key itself when the list does not have it, or ''
 */
export function sourceLabel(sources, key) {
  if (!key) return '';
  return (sources ?? []).find((s) => s.key === key)?.label ?? key;
}

/**
 * A record's source select: the active sources in order, plus the record's
 * current value when it is retired or unknown, so the select can show it and
 * a save sends it back unchanged rather than nothing.
 *
 * @param {LeadSource[] | null | undefined} sources
 * @param {string | null | undefined} [current]
 * @returns {{ key: string, label: string, retired: boolean }[]}
 */
export function sourceOptions(sources, current) {
  const list = sources ?? [];
  const options = list
    .filter((s) => s.is_active !== false)
    .map((s) => ({ key: s.key, label: s.label, retired: false }));
  if (current && !options.some((o) => o.key === current)) {
    const stored = list.find((s) => s.key === current);
    options.unshift({
      key: current,
      label: `${stored?.label ?? current} (retired)`,
      retired: true
    });
  }
  return options;
}

/**
 * The list filter's options: every source, retired ones too, since old
 * records still carry them. Shaped as the filter bar's `{ id, name }`.
 *
 * @param {LeadSource[] | null | undefined} sources
 * @returns {{ id: string, name: string }[]}
 */
export function sourceFilterOptions(sources) {
  return (sources ?? []).map((s) => ({
    id: s.key,
    name: s.is_active === false ? `${s.label} (retired)` : s.label
  }));
}

/**
 * The keys in their new order after moving `key` one place, or null when it
 * cannot move that way.
 *
 * @param {LeadSource[]} sources in their current order
 * @param {string} key
 * @param {string} direction `up` or `down`
 * @returns {string[] | null}
 */
export function moveKeys(sources, key, direction) {
  if (direction !== 'up' && direction !== 'down') return null;
  const keys = (sources ?? []).map((s) => s.key);
  const at = keys.indexOf(key);
  const to = direction === 'up' ? at - 1 : at + 1;
  if (at < 0 || to < 0 || to >= keys.length) return null;
  [keys[at], keys[to]] = [keys[to], keys[at]];
  return keys;
}
