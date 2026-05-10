import { json } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies, locals }) {
  const limit = url.searchParams.get('limit') || '20';
  const unread = url.searchParams.get('unread');
  const since = url.searchParams.get('since');
  const qs = new URLSearchParams({ limit });
  if (unread) qs.set('unread', unread);
  if (since) qs.set('since', since);
  const data = await apiRequest(`/notifications/?${qs.toString()}`, {}, { cookies, org: locals?.org });
  return json(data);
}
