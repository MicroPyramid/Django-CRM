import { getAccount } from '$lib/server/v2/accounts.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  return await getAccount({ cookies }, params.id);
}
