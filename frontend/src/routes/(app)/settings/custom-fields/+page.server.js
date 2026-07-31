import { getCustomFields } from '$lib/server/v2/custom-fields.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getCustomFields({ cookies });
}
