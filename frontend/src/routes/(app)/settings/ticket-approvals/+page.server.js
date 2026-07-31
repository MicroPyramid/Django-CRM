import { getApprovalRules } from '$lib/server/v2/ticket-approvals.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getApprovalRules({ cookies });
}
