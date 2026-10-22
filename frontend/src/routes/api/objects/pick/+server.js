import { json } from '@sveltejs/kit';
import { searchLinkTargets } from '#lib/server/v2/custom-objects.js';

/**
 * The link picker's search. The session token is an httpOnly cookie, so the
 * browser asks here; the API still decides what the caller may open.
 *
 * @type {import('./$types').RequestHandler}
 */
export async function GET({ url, cookies }) {
  if (!cookies.get('jwt_access')) return json({ error: 'Not signed in.' }, { status: 401 });
  const target = url.searchParams.get('target') ?? '';
  const q = (url.searchParams.get('q') ?? '').trim().slice(0, 100);
  try {
    const matches = await searchLinkTargets({ cookies }, target, q);
    return json(matches, { headers: { 'Cache-Control': 'private, no-store' } });
  } catch {
    return json({ error: 'Could not search.' }, { status: 502 });
  }
}
