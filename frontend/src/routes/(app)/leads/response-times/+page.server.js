import { getResponseTimes, responseDays, RESPONSE_DAYS } from '#lib/server/v2/leads.js';
import { viewerIsAdmin } from '#lib/server/v2/organization.js';

/**
 * Time to first response per person. The API narrows the rows: an admin gets
 * every active member, anyone else only themselves. `isAdmin` only words the
 * page.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, url }) {
  const days = responseDays(url.searchParams.get('days'));
  const { since, rows } = await getResponseTimes({ cookies }, days);
  return { days, periods: RESPONSE_DAYS, since, rows, isAdmin: viewerIsAdmin(cookies) };
}
