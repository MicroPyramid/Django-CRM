import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** Weekly timesheet by profile and start/end dates (default = current ISO week). */
/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies, locals }) {
  const qs = url.searchParams.toString();
  try {
    const data = await apiRequest(
      `/time-entries/timesheet/${qs ? `?${qs}` : ''}`,
      { method: 'GET' },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Timesheet failed' }, { status: 400 });
  }
}
