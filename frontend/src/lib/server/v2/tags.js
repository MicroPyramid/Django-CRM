/**
 * Tags: the wiring behind `/settings/tags`.
 *
 * Server-only. Reads `GET /tags/?include_archived=true`, which returns every
 * tag in the org (active and archived. The page shows the "Off" ones so an
 * admin can see what's been retired), each carrying a `usage` block
 * `{ accounts, leads, opportunities, cases }` and a `totals` summary
 * `{ count, active, unused }` for the stat cards. Both are computed server-side
 * (the usage counts are org-scoped subqueries, not a client tally over rows).
 *
 * Read-only page: the only controls ("New tag", the duplicate-merge banner) are
 * not wired, deferred, like the other settings builders. No write path here.
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ tags: any[], totals: any }>}
 */
export async function getTags({ cookies }) {
  const resp = await apiRequest('/tags/?include_archived=true', {}, { cookies });
  return {
    tags: resp.tags ?? [],
    totals: resp.totals ?? { count: 0, active: 0, unused: 0 }
  };
}
