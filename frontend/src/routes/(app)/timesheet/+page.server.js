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

  const isAdmin = /** @type {any} */ (locals).profile?.role === 'ADMIN';

  // Only admins can view others' timesheets, so only fetch the user list for them.
  const usersPromise = isAdmin
    ? apiRequest('/users/', {}, { cookies, org: locals.org }).catch(() => ({}))
    : Promise.resolve({});

  try {
    const [data, usersRes] = await Promise.all([
      apiRequest(
        `/time-entries/timesheet/?${qs.toString()}`,
        {},
        { cookies, org: locals.org }
      ),
      usersPromise
    ]);
    const users = (
      /** @type {any} */ (usersRes).active_users?.active_users || []
    ).map(
      /** @param {any} p */ (p) => ({
        id: p.id,
        email: p.user_details?.email || p.email || 'Unknown',
        name:
          p.user_details?.first_name || p.user_details?.last_name
            ? `${p.user_details?.first_name || ''} ${p.user_details?.last_name || ''}`.trim()
            : ''
      })
    );
    return {
      timesheet: data,
      start,
      end,
      profileFilter: profile,
      currentUserId: locals.user?.id || null,
      isAdmin,
      users
    };
  } catch (err) {
    console.error('Timesheet load failed:', err);
    return {
      timesheet: {
        days: [],
        total_minutes: 0,
        billable_minutes: 0,
        running_count: 0,
        server_now: new Date().toISOString()
      },
      start,
      end,
      profileFilter: profile,
      currentUserId: locals.user?.id || null,
      isAdmin,
      users: [],
      loadError: /** @type {any} */ (err)?.message || 'Could not load timesheet'
    };
  }
}
