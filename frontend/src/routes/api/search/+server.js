import { json } from '@sveltejs/kit';
import { search } from '$lib/server/v2/search.js';

/**
 * ⌘K palette search. The palette runs in the browser and the access token is an
 * httpOnly cookie, so the query is proxied through here; the cookie stays
 * server-side and the Django endpoint scopes results to the caller's org.
 *
 * @type {import('./$types').RequestHandler}
 */
export async function GET({ url, cookies }) {
  const q = url.searchParams.get('q') || '';
  try {
    return json(await search({ cookies }, q));
  } catch (/** @type {any} */ err) {
    return json({ results: [], error: err?.message || 'Search failed' }, { status: 400 });
  }
}
