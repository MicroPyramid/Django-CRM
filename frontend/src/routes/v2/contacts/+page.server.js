import { listContacts } from '$lib/server/v2/contacts.js';

/**
 * Only filters the API actually applies are forwarded. A parameter that
 * changes the URL and nothing else teaches people the filter bar is decorative.
 *
 * `inactive=1` in the URL is kept from the fixture page, because the question
 * it asks is a good one — but it is answered by the API now (`?is_active=`)
 * rather than by discarding rows after they arrive, which was only ever right
 * on the first page.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, url }) {
  const params = new URLSearchParams();
  for (const key of ['search', 'name', 'city', 'email', 'phone', 'assigned_to', 'tags', 'limit']) {
    const value = url.searchParams.get(key);
    if (value) params.set(key, value);
  }

  const includeInactive = url.searchParams.get('inactive') === '1';
  if (!includeInactive) params.set('is_active', 'true');

  const { results, totals } = await listContacts({ cookies }, params);
  return { contacts: results, totals, includeInactive, search: params.get('search') ?? '' };
}
