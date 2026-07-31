import { getRoutingRules } from '$lib/server/v2/routing.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getRoutingRules({ cookies });
}
