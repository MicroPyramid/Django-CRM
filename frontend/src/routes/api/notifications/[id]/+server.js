import { apiRequest } from '$lib/api-helpers.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** @type {import('./$types').RequestHandler} */
export async function DELETE({ params, cookies, locals }) {
  if (!UUID_RE.test(params.id)) return new Response(null, { status: 400 });
  await apiRequest(
    `/notifications/${params.id}/`,
    { method: 'DELETE' },
    { cookies, org: locals?.org }
  );
  return new Response(null, { status: 204 });
}
