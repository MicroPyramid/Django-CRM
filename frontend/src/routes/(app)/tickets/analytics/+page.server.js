import { getServiceAnalytics } from '$lib/server/v2/service.js';

/**
 * The service-analytics dashboard. `load` returns `{ can_view, totals, volume,
 * firstResponse, byType, byAgent }` — the exact fields the page reads. The
 * dashboard is admin-only; for a non-admin `can_view` is false and the figures
 * are an empty, valid shape, so the page shows its "admins only" state instead
 * of a personal slice under org-wide headings.
 *
 * An optional `?days=` narrows the window (the backend clamps it to 1–90);
 * absent, it defaults to the last 14 days.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, url }) {
  const days = url.searchParams.get('days');
  return await getServiceAnalytics({ cookies }, days ?? undefined);
}
