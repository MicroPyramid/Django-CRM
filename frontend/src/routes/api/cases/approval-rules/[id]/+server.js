import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Approval rule detail GET / PUT / DELETE. */
/** @type {import('./$types').RequestHandler} */
export async function GET({ params, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid rule id' }, { status: 400 });
  }
  try {
    const data = await apiRequest(
      `/cases/approval-rules/${params.id}/`,
      { method: 'GET' },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Rule fetch failed' }, { status: 400 });
  }
}

/** @type {import('./$types').RequestHandler} */
export async function PUT({ params, request, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid rule id' }, { status: 400 });
  }
  const payload = await request.json().catch(() => ({}));
  try {
    const data = await apiRequest(
      `/cases/approval-rules/${params.id}/`,
      { method: 'PUT', body: payload },
      { cookies, org: locals?.org }
    );
    return json(data);
  } catch (err) {
    return json({ error: err?.message || 'Rule update failed' }, { status: 400 });
  }
}

/** @type {import('./$types').RequestHandler} */
export async function DELETE({ params, cookies, locals }) {
  if (!UUID_RE.test(params.id)) {
    return json({ error: 'invalid rule id' }, { status: 400 });
  }
  try {
    const data = await apiRequest(
      `/cases/approval-rules/${params.id}/`,
      { method: 'DELETE' },
      { cookies, org: locals?.org }
    );
    return json(data || { ok: true });
  } catch (err) {
    return json({ error: err?.message || 'Rule delete failed' }, { status: 400 });
  }
}
