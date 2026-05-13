import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** Create a draft invoice from a list of billable, single-currency time entries. */
/** @type {import('./$types').RequestHandler} */
export async function POST({ request, cookies, locals }) {
  const payload = await request.json().catch(() => ({}));
  try {
    const data = await apiRequest(
      `/invoices/from-time-entries/`,
      { method: 'POST', body: payload },
      { cookies, org: locals?.org }
    );
    return json(data, { status: 201 });
  } catch (err) {
    return json({ error: err?.message || 'Create invoice failed' }, { status: 400 });
  }
}
