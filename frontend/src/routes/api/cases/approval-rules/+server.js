import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** Approval rule list (GET) + create (POST). Admin-only on POST. */
/** @type {import('./$types').RequestHandler} */
export async function GET({ cookies, locals }) {
  try {
    const data = await apiRequest(
      '/cases/approval-rules/',
      { method: 'GET' },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Rule list failed' }, { status: 400 });
  }
}

/** @type {import('./$types').RequestHandler} */
export async function POST({ request, cookies, locals }) {
  const payload = await request.json().catch(() => ({}));
  try {
    const data = await apiRequest(
      '/cases/approval-rules/',
      { method: 'POST', body: payload },
      { cookies, org: locals?.org }
    );
    return json(data, { status: 201 });
  } catch (err) {
    return json(
      { error: err?.message || 'Rule create failed' },
      { status: 400 }
    );
  }
}
