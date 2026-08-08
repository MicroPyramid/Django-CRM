import { loadHelpPage } from '$lib/server/v2/support.js';

/**
 * Help has two tiers and `loadHelpPage` decides which one. The decision lives
 * in the lib module rather than here so it is reachable by the test harness.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return loadHelpPage({ cookies });
}
