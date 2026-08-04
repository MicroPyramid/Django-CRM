/**
 * Weekly timesheet: the wiring behind /v2/timesheet.
 *
 * Server-only. `GET /time-entries/timesheet/` returns the caller's own week
 * grouped into day buckets (every day present, empty or not) with week
 * totals, the billable split, and a running-timer count. The page reads it
 * verbatim as `data.week`.
 *
 * The v2 page is always "your timesheet", it has no profile switcher, so this
 * layer never passes a `profile`, which also keeps it clear of the endpoint's
 * admin-only "another profile" 403. `TimesheetView` already expands `case` and
 * `invoice` to `{id, name}` / `{id, invoice_number}` and names the profile, so
 * there is no reshaping here.
 *
 * `stopTimer` is the one write path here: `POST /time-entries/<id>/stop/`.
 * Nothing else on this page is editable.
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * Mon..Sun ISO-week range for `date` (UTC), as YYYY-MM-DD strings.
 * @param {Date} date
 */
function isoWeekRange(date) {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const dow = (d.getUTCDay() + 6) % 7; // Mon=0
  d.setUTCDate(d.getUTCDate() - dow);
  const start = d.toISOString().slice(0, 10);
  d.setUTCDate(d.getUTCDate() + 6);
  const end = d.toISOString().slice(0, 10);
  return { start, end };
}

/**
 * The caller's timesheet for a Mon..Sun week, shaped for the page.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {{ start?: string, end?: string }} [range] explicit week; defaults to this ISO week
 * @returns {Promise<{ week: any }>}
 */
export async function getTimesheet({ cookies }, { start, end } = {}) {
  if (!start || !end) {
    const range = isoWeekRange(new Date());
    start = start || range.start;
    end = end || range.end;
  }
  const qs = new URLSearchParams({ start, end });
  const week = await apiRequest(`/time-entries/timesheet/?${qs.toString()}`, {}, { cookies });
  return { week };
}

/**
 * Stop a running timer.
 *
 * The id guard is not defensive noise: an empty id would POST to
 * `/time-entries//stop/`, which is a different path, and the failure would
 * read as a routing bug rather than a missing argument.
 *
 * Ownership is the backend's call. The endpoint is org-scoped and checks the
 * entry belongs to the caller, so this does not re-check it here and must not
 * be read as having done so.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} entryId
 * @returns {Promise<any>} the stopped entry
 */
export async function stopTimer({ cookies }, entryId) {
  if (!entryId) throw new Error('Which time entry? No entry id was given.');

  return await apiRequest(`/time-entries/${entryId}/stop/`, { method: 'POST' }, { cookies });
}
