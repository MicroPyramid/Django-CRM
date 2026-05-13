/**
 * CSV export proxy. Streams the upstream `text/csv` response straight through
 * to the browser so big windows don't get buffered. Uses `fmt` not `format`
 * because DRF's content negotiation eats `?format=`.
 */

import { env } from '$env/dynamic/public';

const API_BASE_URL = `${env.PUBLIC_DJANGO_API_URL}/api`;

/** @type {import('./$types').RequestHandler} */
export async function GET({ cookies, request, url }) {
  const accessToken = cookies.get('jwt_access');
  if (!accessToken) return new Response('Unauthorized', { status: 401 });

  const qs = url.searchParams.toString();
  // Org context lives inside the JWT — no extra header needed.
  const upstream = await fetch(
    `${API_BASE_URL}/cases/analytics/export/${qs ? `?${qs}` : ''}`,
    {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'text/csv'
      },
      signal: request.signal
    }
  );

  if (!upstream.ok || !upstream.body) {
    return new Response(`Upstream error: ${upstream.status}`, {
      status: upstream.status || 502
    });
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      'Content-Type': upstream.headers.get('Content-Type') || 'text/csv',
      'Content-Disposition':
        upstream.headers.get('Content-Disposition') ||
        'attachment; filename="cases.csv"'
    }
  });
}
