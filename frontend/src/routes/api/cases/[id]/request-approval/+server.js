import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Tier 3 approvals: request approval for closing this case. */
/** @type {import('./$types').RequestHandler} */
export async function POST({ params, request, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid case id' }, { status: 400 });
  }
  const payload = await request.json().catch(() => ({}));
  try {
    const data = await apiRequest(
      `/cases/${params.id}/request-approval/`,
      { method: 'POST', body: payload },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json(
      { error: err?.message || 'Approval request failed' },
      { status: 400 }
    );
  }
}
