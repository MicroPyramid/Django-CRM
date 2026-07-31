import { getDeal } from '$lib/server/v2/deals.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  return await getDeal(event, event.params.id);
}
