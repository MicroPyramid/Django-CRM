import { listAccounts } from '$lib/server/v2/accounts.js';

/**
 * Only filters the API actually applies are forwarded. A parameter that
 * changes the URL and nothing else teaches people the filter bar is decorative.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, url }) {
  const params = new URLSearchParams();
  for (const key of ['search', 'name', 'city', 'industry', 'assigned_to', 'tags', 'limit']) {
    const value = url.searchParams.get(key);
    if (value) params.set(key, value);
  }

  const { results, totals } = await listAccounts({ cookies }, params);
  return { accounts: results, totals };
}
