/**
 * Which v2 routes are wired to the real API.
 *
 * One list, because two would drift and the thing that drifts is a banner
 * telling somebody a page is a sandbox while it writes to their org.
 *
 * Add a prefix here in the same change that wires the module — not before it
 * works, and not after. A module counts as migrated when its reads *and* its
 * writes go to the API; a page that lists real rows behind a form that still
 * pretends to save does not belong on this list.
 */
export const MIGRATED_ROUTES = [
  '/v2/leads',
  '/v2/pipeline',
  '/v2/accounts',
  '/v2/contacts',
  '/v2/tickets',
  '/v2/solutions',
  '/v2/tasks',
  '/v2/invoices',
  '/v2/team',
  '/v2/goals',
  '/v2/documents',
  '/v2/notifications',
  '/v2/profile',
  '/v2/settings/api-tokens',
  '/v2/settings/organization',
  '/v2/settings/macros',
  '/v2/settings/tags',
  '/v2/settings/custom-fields',
  '/v2/settings/reopen',
  '/v2/settings/escalation',
  '/v2/settings/routing',
  '/v2/settings/inbound-email',
  '/v2/settings/ticket-approvals',
  '/v2/settings/business-hours',
  '/v2/timesheet'
];

/**
 * Routes migrated as an EXACT path only — they must never act as a prefix.
 *
 * The dashboard root `/v2` is the case in point. It is live (it reads the real
 * `GET /dashboard/today/` queue), but as a prefix `/v2` would match every path
 * under it and hang "Live data" over the pages still on fixtures — settings/*,
 * timesheet, the public portal. So it is matched exactly and never as a stem.
 */
export const MIGRATED_EXACT = ['/v2', '/v2/settings'];

/**
 * Pages under a migrated prefix that are still fixtures.
 *
 * `/v2/tickets` is the first prefix with sub-pages that did not come with it.
 * The queue, the ticket itself, the analytics dashboard and the approvals inbox
 * are all live now, each on its own endpoints. A prefix match alone would hang
 * "Live data" over anything under the prefix, so a page still on fixtures has to
 * opt out here by exact path until it is wired.
 *
 * Exact paths, not prefixes, so a real `/v2/tickets/<uuid>` cannot be caught
 * by an entry meant for a sibling page.
 *
 * `/v2/tasks/board` used to sit here for a sharper reason than "not done yet":
 * a board card is a `tasks.BoardTask`, a **different table** from the
 * `tasks.Task` the list page writes, so wiring one did not wire the other and a
 * prefix match would have claimed it did. It is wired now too — the board reads
 * real columns and cards and persists a drag with `PUT /boards/tasks/<id>/`, its
 * column server-validated to a sibling of the same board. With it done, no page
 * under a migrated prefix is still on fixtures, so this list is empty.
 */
export const NOT_MIGRATED_ROUTES = [
  /* Empty: every page under a migrated prefix now reads and writes the real
     org. Add an exact path here the moment a new sub-page ships on fixtures. */
];

/**
 * @param {string} pathname
 * @returns {boolean} True when this route reads and writes the real org.
 */
export function isMigrated(pathname) {
  if (NOT_MIGRATED_ROUTES.includes(pathname)) return false;
  if (MIGRATED_EXACT.includes(pathname)) return true;
  return MIGRATED_ROUTES.some((route) => pathname === route || pathname.startsWith(route + '/'));
}
