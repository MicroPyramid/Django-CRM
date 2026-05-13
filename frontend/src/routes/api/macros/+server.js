import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies, locals }) {
  // The composer picker fetches active macros visible to the requester
  // (server-side filter via /api/macros/?active=true).
  const params = new URLSearchParams();
  params.set('active', 'true');
  const search = url.searchParams.get('search');
  if (search) params.set('search', search);
  const data = await apiRequest(
    `/macros/?${params.toString()}`,
    {},
    { cookies, org: locals?.org }
  );
  return json(data);
}
