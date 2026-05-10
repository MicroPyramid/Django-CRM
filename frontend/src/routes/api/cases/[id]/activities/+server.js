import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, url, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ activities: [], count: 0, offset: null }, { status: 400 });
  }
  const limit = url.searchParams.get('limit') || '20';
  const offset = url.searchParams.get('offset');
  const qs = new URLSearchParams({ limit });
  if (offset) qs.set('offset', offset);
  const res = await apiRequest(
    `/cases/${params.id}/activities/?${qs.toString()}`,
    {},
    { cookies, org: locals?.org }
  );
  return json(res);
}
