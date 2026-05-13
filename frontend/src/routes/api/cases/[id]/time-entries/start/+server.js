import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Start a running timer on the given case. */
/** @type {import('./$types').RequestHandler} */
export async function POST({ params, request, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid case id' }, { status: 400 });
  }
  const payload = await request.json().catch(() => ({}));
  try {
    const data = await apiRequest(
      `/cases/${params.id}/time-entries/start/`,
      { method: 'POST', body: payload },
      { cookies, org: locals?.org }
    );
    return json(data, { status: 201 });
  } catch (err) {
    // 409 surfaces "you already have a running timer" — bubble up so the UI
    // can offer to switch the running timer to this case.
    const status = /already have a running/i.test(err?.message || '') ? 409 : 400;
    return json({ error: err?.message || 'Start failed' }, { status });
  }
}
