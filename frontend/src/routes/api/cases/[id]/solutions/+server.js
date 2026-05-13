import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Record a case↔solution link from JS (suggester insert action).
 * The case-detail form actions handle link/unlink from the existing
 * sidebar; this proxy is the JS-callable equivalent. */
/** @type {import('./$types').RequestHandler} */
export async function POST({ params, request, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid case id' }, { status: 400 });
  }
  const payload = await request.json().catch(() => ({}));
  const data = await apiRequest(
    `/cases/${params.id}/solutions/`,
    { method: 'POST', body: payload },
    { cookies, org: locals?.org }
  );
  return json(data);
}
