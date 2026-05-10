import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** Approval inbox. Query params: state, mine, case. */
/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies, locals }) {
  const qs = url.searchParams.toString();
  try {
    const data = await apiRequest(
      `/cases/approvals/${qs ? `?${qs}` : ''}`,
      { method: 'GET' },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Inbox failed' }, { status: 400 });
  }
}
