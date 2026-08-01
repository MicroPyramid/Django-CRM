import { getEscalationPolicies } from '$lib/server/v2/escalation.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getEscalationPolicies({ cookies });
}
