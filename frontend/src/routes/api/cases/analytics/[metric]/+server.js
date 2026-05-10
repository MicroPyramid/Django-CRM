import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const ALLOWED = new Set([
  'frt',
  'mttr',
  'backlog',
  'agents',
  'sla',
  'drilldown'
]);

/** Generic GET proxy for the analytics endpoints — passes the query string
 * through verbatim so filter handling stays on the backend. */
/** @type {import('./$types').RequestHandler} */
export async function GET({ params, url, cookies, locals }) {
  if (!ALLOWED.has(params.metric)) {
    return json({ error: 'Unknown metric' }, { status: 404 });
  }
  const qs = url.searchParams.toString();
  const data = await apiRequest(
    `/cases/analytics/${params.metric}/${qs ? `?${qs}` : ''}`,
    {},
    { cookies, org: locals?.org }
  );
  return json(data);
}
