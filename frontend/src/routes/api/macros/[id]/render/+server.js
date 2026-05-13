import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').RequestHandler} */
export async function POST({ params, request, cookies, locals }) {
  const payload = await request.json().catch(() => ({}));
  const data = await apiRequest(
    `/macros/${params.id}/render/`,
    { method: 'POST', body: payload },
    { cookies, org: locals?.org }
  );
  return json(data);
}
