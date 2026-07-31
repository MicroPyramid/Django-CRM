import { getMailboxes } from '$lib/server/v2/inbound-email.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getMailboxes({ cookies });
}
