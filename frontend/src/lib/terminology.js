/**
 * Label lookup for vertical packs.
 *
 * A pack can rename entities in the UI ("Leads" -> "Enquiries") by writing
 * keys into `Org.terminology` (e.g. `{ "lead.plural": "Enquiries" }`), which
 * the backend serializes back as `org.terminology`. This helper is the only
 * way a component should read that map.
 *
 * Always called with an explicit fallback, so an org with no pack, or a
 * terminology object missing this particular key. Renders exactly as it
 * does today. There is no branching on `org.vertical` anywhere; the entire
 * effect of a pack on the UI is carried by this map plus the ordinary config
 * rows the backend already created.
 *
 * `terminology` values are tenant-controlled text rendered as plain text.
 * Never pass the result of this function to `{@html}`.
 *
 * @param {Record<string, string> | null | undefined} terminology
 * @param {string} key
 * @param {string} fallback
 * @returns {string}
 */
export function t(terminology, key, fallback) {
  const value = terminology?.[key];
  return typeof value === 'string' && value.length > 0 ? value : fallback;
}
