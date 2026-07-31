import { getTimesheet } from '$lib/server/v2/timesheet.js';

/**
 * `?start=&end=` (YYYY-MM-DD) pick the week; absent, it defaults to this ISO
 * week. The week-nav buttons drive those params.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, url }) {
  const start = url.searchParams.get('start') || undefined;
  const end = url.searchParams.get('end') || undefined;
  return await getTimesheet({ cookies }, { start, end });
}
