import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** @type {import('./$types').RequestHandler} */
export async function POST({ params, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid approval id' }, { status: 400 });
  }
  try {
    const data = await apiRequest(
      `/cases/approvals/${params.id}/cancel/`,
      { method: 'POST', body: {} },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Cancel failed' }, { status: 400 });
  }
}
