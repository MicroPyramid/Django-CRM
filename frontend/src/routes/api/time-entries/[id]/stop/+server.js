import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Stop a running time entry. */
/** @type {import('./$types').RequestHandler} */
export async function POST({ params, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid entry id' }, { status: 400 });
  }
  try {
    const data = await apiRequest(
      `/time-entries/${params.id}/stop/`,
      { method: 'POST' },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Stop failed' }, { status: 400 });
  }
}
