import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Tier 3 time-tracking: list/create entries on a case. */
/** @type {import('./$types').RequestHandler} */
export async function GET({ params, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid case id' }, { status: 400 });
  }
  try {
    const data = await apiRequest(
      `/cases/${params.id}/time-entries/`,
      { method: 'GET' },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'List failed' }, { status: 400 });
  }
}

/** @type {import('./$types').RequestHandler} */
export async function POST({ params, request, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid case id' }, { status: 400 });
  }
  const payload = await request.json().catch(() => ({}));
  try {
    const data = await apiRequest(
      `/cases/${params.id}/time-entries/`,
      { method: 'POST', body: payload },
      { cookies, org: locals?.org }
    );
    return json(data, { status: 201 });
  } catch (err) {
    return json({ error: err?.message || 'Create failed' }, { status: 400 });
  }
}
