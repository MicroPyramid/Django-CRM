import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** Forwards a case search to the backend. Used by the merge dialog's
 * "search target case" autocomplete. */
/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies, locals }) {
  const q = url.searchParams.get('search') || '';
  const limit = url.searchParams.get('limit') || '20';
  if (!q || q.length < 2) {
    return json({ cases: [] });
  }
  const qs = new URLSearchParams({ search: q, limit });
  const res = await apiRequest(`/cases/?${qs.toString()}`, {}, {
    cookies,
    org: locals?.org
  });
  return json({ cases: res.cases || [] });
}
