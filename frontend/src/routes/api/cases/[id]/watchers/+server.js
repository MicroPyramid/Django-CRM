import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** @type {import('./$types').RequestHandler} */
export async function GET({ params, cookies, locals }) {
  if (!UUID_RE.test(params.id)) return json({ watchers: [], count: 0 }, { status: 400 });
  const data = await apiRequest(
    `/cases/${params.id}/watchers/`,
    {},
    { cookies, org: locals?.org }
  );
  return json(data);
}
