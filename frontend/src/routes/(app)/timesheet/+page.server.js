import { error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** Compute the Mon..Sun ISO-week range for `date`. */
function isoWeekRange(/** @type {Date} */ date) {
  const d = new Date(
    Date.UTC(date.getFullYear(), date.getMonth(), date.getDate())
  );
  const dayOfWeek = (d.getUTCDay() + 6) % 7; // Mon=0
  d.setUTCDate(d.getUTCDate() - dayOfWeek);
  const start = d.toISOString().slice(0, 10);
  d.setUTCDate(d.getUTCDate() + 6);
  const end = d.toISOString().slice(0, 10);
  return { start, end };
}

/** @type {import('./$types').PageServerLoad} */
export async function load({ url, locals, cookies }) {
  if (!locals.org) throw error(401, 'Organization context required');

  let start = url.searchParams.get('start');
  let end = url.searchParams.get('end');
  const profile = url.searchParams.get('profile') || '';

  if (!start || !end) {
    const range = isoWeekRange(new Date());
    start = start || range.start;
    end = end || range.end;
  }

  const qs = new URLSearchParams({ start, end });
  if (profile) qs.set('profile', profile);

  try {
    const data = await apiRequest(
      `/time-entries/timesheet/?${qs.toString()}`,
      {},
      { cookies, org: locals.org }
    );
    return {
      timesheet: data,
      start,
      end,
      profileFilter: profile,
      currentUserId: locals.user?.id || null,
      isAdmin: /** @type {any} */ (locals).profile?.role === 'ADMIN'
    };
  } catch (err) {
    console.error('Timesheet load failed:', err);
    return {
      timesheet: { days: [], total_minutes: 0, billable_minutes: 0 },
      start,
      end,
      profileFilter: profile,
      currentUserId: locals.user?.id || null,
      isAdmin: /** @type {any} */ (locals).profile?.role === 'ADMIN',
      loadError: err?.message || 'Could not load timesheet'
    };
  }
}
