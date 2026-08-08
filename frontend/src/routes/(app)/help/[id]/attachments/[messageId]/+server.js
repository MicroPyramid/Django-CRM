import { error } from '@sveltejs/kit';
import { env } from '$env/dynamic/public';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/** @type {import('./$types').RequestHandler} */
export async function GET({ cookies, params, fetch }) {
  if (!UUID.test(params.id) || !UUID.test(params.messageId)) error(404, 'Attachment not found');
  const token = cookies.get('jwt_access');
  if (!token) error(401, 'Sign in to download this attachment');

  const response = await fetch(
    `${env.PUBLIC_DJANGO_API_URL}/api/support/messages/${params.messageId}/attachment/`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!response.ok || !response.body) {
    error(response.status === 404 ? 404 : 502, 'Could not download this attachment');
  }

  const headers = new Headers({
    'Cache-Control': 'private, no-store',
    'Content-Type': response.headers.get('content-type') ?? 'application/octet-stream',
    'X-Content-Type-Options': 'nosniff'
  });
  const disposition = response.headers.get('content-disposition');
  if (disposition) headers.set('Content-Disposition', disposition);
  return new Response(response.body, { headers });
}
