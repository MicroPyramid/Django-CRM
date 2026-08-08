import { fail } from '@sveltejs/kit';
import {
  getBusinessHours,
  updateBusinessHours,
  addHoliday as addHolidayWrite,
  removeHoliday as removeHolidayWrite
} from '$lib/server/v2/business-hours.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getBusinessHours({ cookies });
}

/** Monday-first weekday label ↔ the form field prefix each row posts under.
 *  Kept in one place so the seven names are typed once here, not seven
 *  times across the read of a form submission. */
const WEEKDAYS = [
  ['Monday', 'monday'],
  ['Tuesday', 'tuesday'],
  ['Wednesday', 'wednesday'],
  ['Thursday', 'thursday'],
  ['Friday', 'friday'],
  ['Saturday', 'saturday'],
  ['Sunday', 'sunday']
];

/**
 * Read the week back out of the form: one `open` and one `close` input per
 * day plus a `closed` checkbox, all named by weekday prefix. A checked
 * "closed" box wins outright and reports both fields null for that day,
 * regardless of whatever the (disabled, and so never actually submitted by
 * the browser) time inputs hold.
 *
 * @param {FormData} form
 */
function readDays(form) {
  return WEEKDAYS.map(([label, key]) => {
    const closed = form.get(`${key}_closed`) === 'true';
    return {
      day: label,
      open: closed ? null : form.get(`${key}_open`)?.toString() || null,
      close: closed ? null : form.get(`${key}_close`)?.toString() || null
    };
  });
}

/** The one 403 body all three admin-only writes share, turned into a sentence. */
const FORBIDDEN = 'Only admins can update business hours.';

/**
 * All three actions below are admin-only, enforced server-side by
 * `BusinessCalendarView.put` / `BusinessHolidayListView.post` /
 * `BusinessHolidayDetailView.delete`, each re-deriving admin status from
 * `request.profile`. `data.can_edit` in the page only hides the controls;
 * it is a display hint, never the authorization decision.
 *
 * @type {import('./$types').Actions}
 */
export const actions = {
  async updateHours(event) {
    const form = await event.request.formData();
    const days = readDays(form);
    const meta = {
      name: form.get('name')?.toString().trim() ?? '',
      timezone: form.get('timezone')?.toString().trim() ?? ''
    };
    try {
      // The calendar id never travels through the form: there is exactly
      // one calendar per org, and this read is org-scoped server-side, so
      // resolving it here rather than trusting a hidden field means there
      // is nothing for a hand-crafted POST to redirect at another org's row.
      const { calendar } = await getBusinessHours(event);
      await updateBusinessHours(event, calendar.id, days, meta);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { updateHours: { error: FORBIDDEN } });
      }
      return fail(400, {
        updateHours: { error: readableError(err, 'Could not save business hours.') }
      });
    }
    return { hoursUpdated: true };
  },

  async addHoliday(event) {
    const form = await event.request.formData();
    const date = form.get('date')?.toString() ?? '';
    const name = form.get('name')?.toString().trim() ?? '';
    /** @type {any} */
    let existing = null;
    try {
      const { calendar } = await getBusinessHours(event);
      // A date already on the calendar comes back as the row that was already
      // there, name included, rather than the one just typed. Not an error, but
      // not the same event as adding a holiday either: the typed name was
      // discarded, and reporting both as "added" is how a rename silently fails.
      existing = await addHolidayWrite(event, calendar.id, { date, name });
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { addHoliday: { error: FORBIDDEN } });
      }
      return fail(400, { addHoliday: { error: readableError(err, 'Could not add the holiday.') } });
    }
    const storedName = existing?.name ?? '';
    if (storedName && storedName !== name) {
      return { holidayAdded: true, holidayAlreadyNamed: storedName };
    }
    return { holidayAdded: true };
  },

  async removeHoliday(event) {
    const form = await event.request.formData();
    const holidayId = form.get('holiday_id')?.toString() ?? '';
    try {
      const { calendar } = await getBusinessHours(event);
      await removeHolidayWrite(event, calendar.id, holidayId);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { removeHoliday: { error: FORBIDDEN } });
      }
      return fail(400, {
        removeHoliday: { error: readableError(err, 'Could not remove the holiday.') }
      });
    }
    return { holidayRemoved: true };
  }
};
