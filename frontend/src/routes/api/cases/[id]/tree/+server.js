import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Tier 3 parent/child: descendant tree (max depth 3). */
/** @type {import('./$types').RequestHandler} */
export async function GET({ params, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid case id' }, { status: 400 });
  }
  const data = await apiRequest(
    `/cases/${params.id}/tree/`,
    {},
    { cookies, org: locals?.org }
  );
  return json(data);
}
