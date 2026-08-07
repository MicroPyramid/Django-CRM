import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const ALLOWED = new Set(['frt', 'mttr', 'backlog', 'agents', 'sla', 'drilldown']);

/** Generic GET proxy for the analytics endpoints, passes the query string
 * through verbatim so filter handling stays on the backend.
 *
 * The upstream status is passed through too. `apiRequest` throws on any
 * non-2xx, and an uncaught throw in a `+server.js` handler is a 500 whatever
 * the cause was, so a `?from=banana` the API correctly refuses with a 400
 * reached the caller as "internal server error" with the field name and the
 * reason both discarded. The sibling `export/+server.js` already forwards
 * `upstream.status`; this route was the one that did not. */
/** @type {import('./$types').RequestHandler} */
export async function GET({ params, url, cookies, locals }) {
  if (!ALLOWED.has(params.metric)) {
    return json({ error: 'Unknown metric' }, { status: 404 });
  }
  const qs = url.searchParams.toString();
  try {
    const data = await apiRequest(
      `/cases/analytics/${params.metric}/${qs ? `?${qs}` : ''}`,
      {},
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    // `apiRequest` attaches the upstream status and its parsed body. A failure
    // with neither is a transport problem rather than a rejection, which is a
    // 502: the proxy reached nobody, so claiming the caller was at fault would
    // be a guess.
    const failure = /** @type {{ status?: number, body?: unknown, message?: string }} */ (err);
    return json(failure?.body ?? { error: failure?.message ?? 'Upstream error' }, {
      status: failure?.status ?? 502
    });
  }
}
