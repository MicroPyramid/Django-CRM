import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** Billable, stopped, not-yet-invoiced entries (optionally filtered by account). */
/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies, locals }) {
  const qs = url.searchParams.toString();
  try {
    const data = await apiRequest(
      `/time-entries/unbilled/${qs ? `?${qs}` : ''}`,
      { method: 'GET' },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Unbilled list failed' }, { status: 400 });
  }
}
