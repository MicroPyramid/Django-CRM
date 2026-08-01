import { getToday } from '$lib/server/v2/today.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  return await getToday(event);
}
