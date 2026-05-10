import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** PUT/DELETE a specific time entry. Owner or admin only (enforced server-side). */
/** @type {import('./$types').RequestHandler} */
export async function PUT({ params, request, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid entry id' }, { status: 400 });
  }
  const payload = await request.json().catch(() => ({}));
  try {
    const data = await apiRequest(
      `/time-entries/${params.id}/`,
      { method: 'PUT', body: payload },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Update failed' }, { status: 400 });
  }
}

/** @type {import('./$types').RequestHandler} */
export async function DELETE({ params, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid entry id' }, { status: 400 });
  }
  try {
    await apiRequest(
      `/time-entries/${params.id}/`,
      { method: 'DELETE' },
      { cookies, org: locals?.org }
    );
    return json({ ok: true });
  } catch (err) {
    return json({ error: err?.message || 'Delete failed' }, { status: 400 });
  }
}
