import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').RequestHandler} */
export async function POST({ request, cookies, locals }) {
  /** @type {Record<string, unknown>} */
  let body = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }
  await apiRequest(
    `/notifications/read-all/`,
    { method: 'POST', body },
    { cookies, org: locals?.org }
  );
  return new Response(null, { status: 204 });
}
