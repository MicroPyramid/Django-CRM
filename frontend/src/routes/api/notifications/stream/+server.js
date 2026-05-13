/**
 * SSE proxy.
 *
 * The browser cannot send custom headers via EventSource — so we proxy the
 * stream through SvelteKit, where we can read the JWT cookie server-side
 * and attach it as an Authorization header on the upstream fetch. The
 * upstream Response body is piped straight through.
 */

import { env } from '$env/dynamic/public';

const API_BASE_URL = `${env.PUBLIC_DJANGO_API_URL}/api`;

/** @type {import('./$types').RequestHandler} */
export async function GET({ cookies, request }) {
  const accessToken = cookies.get('jwt_access');
  if (!accessToken) return new Response('Unauthorized', { status: 401 });

  const upstream = await fetch(`${API_BASE_URL}/notifications/stream/`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: 'text/event-stream'
    },
    // Abort the upstream when the browser hangs up.
    signal: request.signal
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(`Upstream error: ${upstream.status}`, {
      status: upstream.status || 502
    });
  }

  // Note: `Connection` is a hop-by-hop header — Node refuses to forward it
  // and HTTP keep-alive is the default in HTTP/1.1 anyway. Don't set it.
  return new Response(upstream.body, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'X-Accel-Buffering': 'no'
    }
  });
}
