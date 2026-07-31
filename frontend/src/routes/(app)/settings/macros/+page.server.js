import { getMacros } from '$lib/server/v2/macros.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getMacros({ cookies });
}
