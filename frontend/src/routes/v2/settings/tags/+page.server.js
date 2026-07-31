import { getTags } from '$lib/server/v2/tags.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getTags({ cookies });
}
