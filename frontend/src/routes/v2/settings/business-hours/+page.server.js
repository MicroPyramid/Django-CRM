import { getBusinessHours } from '$lib/server/v2/business-hours.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getBusinessHours({ cookies });
}
