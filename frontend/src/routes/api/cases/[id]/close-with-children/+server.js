import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Tier 3 parent/child: close parent and (optionally) cascade-close descendants.
 *  Body: { resolution_comment?: string, cascade?: boolean }. */
/** @type {import('./$types').RequestHandler} */
export async function POST({ params, request, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid case id' }, { status: 400 });
  }
  const payload = await request.json().catch(() => ({}));
  try {
    const data = await apiRequest(
      `/cases/${params.id}/close-with-children/`,
      { method: 'POST', body: payload },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Close failed' }, { status: 400 });
  }
}
