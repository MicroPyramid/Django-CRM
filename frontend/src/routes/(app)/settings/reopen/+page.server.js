import { getReopenPolicy } from '$lib/server/v2/reopen.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getReopenPolicy({ cookies });
}
