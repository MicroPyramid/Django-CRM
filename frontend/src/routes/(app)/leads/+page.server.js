import { listLeads } from '$lib/server/v2/leads.js';

/**
 * Server load, not a universal one. The access token is an httpOnly cookie;
 * a `+page.js` would have to run this fetch in the browser too, where that
 * cookie is deliberately unreadable.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, url }) {
  // Forward the filter params the API already understands, so a filtered list
  // and its totals are produced by one query with one WHERE clause.
  const params = new URLSearchParams();
  for (const key of ['search', 'status', 'source', 'rating', 'limit']) {
    const value = url.searchParams.get(key);
    if (value) params.set(key, value);
  }

  const { results, totals } = await listLeads({ cookies }, params);
  return { leads: results, totals };
}
