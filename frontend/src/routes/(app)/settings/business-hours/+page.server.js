import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const WEEKDAY_FIELDS = [
  'monday_open',
  'monday_close',
  'tuesday_open',
  'tuesday_close',
  'wednesday_open',
  'wednesday_close',
  'thursday_open',
  'thursday_close',
  'friday_open',
  'friday_close',
  'saturday_open',
  'saturday_close',
  'sunday_open',
  'sunday_close'
];

/** Normalize a HTML <input type="time"> value (HH:MM) to HH:MM:SS for the API. */
function normalizeTime(raw) {
  if (raw === null || raw === undefined) return null;
  const trimmed = String(raw).trim();
  if (!trimmed) return null;
  return trimmed.length === 5 ? `${trimmed}:00` : trimmed;
}

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, locals }) {
  const profile = locals.profile;
  if (profile?.role !== 'ADMIN' && !profile?.is_organization_admin) {
    throw error(403, 'Only admins can manage business hours');
  }

  try {
    const calendar = await apiRequest(
      '/business-hours/calendar/',
      {},
      { cookies, org: locals?.org }
    );
    return { calendar };
  } catch (err) {
    console.error('Failed to load business calendar:', err);
    throw error(500, 'Failed to load business calendar');
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  update: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = formData.get('id');
    if (!id) {
      return fail(400, { error: 'Missing calendar id' });
    }

    /** @type {Record<string, unknown>} */
    const data = {
      timezone: formData.get('timezone') || 'UTC',
      name: formData.get('name') || 'Default'
    };
    for (const field of WEEKDAY_FIELDS) {
      const closedKey = `${field.split('_')[0]}_closed`;
      // The form posts a "<weekday>_closed" hidden flag; if checked we send
      // both open and close as empty (null on the API), regardless of the
      // time-input residue.
      if (formData.get(closedKey) === 'true' && field.endsWith('_open')) {
        data[field] = null;
      } else if (formData.get(closedKey) === 'true' && field.endsWith('_close')) {
        data[field] = null;
      } else {
        data[field] = normalizeTime(formData.get(field));
      }
    }

    try {
      const calendar = await apiRequest(
        `/business-hours/calendar/${id}/`,
        { method: 'PUT', body: data },
        { cookies, org: locals?.org }
      );
      return { success: true, calendar };
    } catch (err) {
      console.error('Failed to update business calendar:', err);
      return fail(400, { error: err?.message || 'Failed to update calendar' });
    }
  },

  addHoliday: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = formData.get('id');
    const date = formData.get('date');
    const name = formData.get('name');
    if (!id || !date || !name) {
      return fail(400, { error: 'Date and name are required' });
    }
    try {
      await apiRequest(
        `/business-hours/calendar/${id}/holidays/`,
        { method: 'POST', body: { date, name } },
        { cookies, org: locals?.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Failed to add holiday:', err);
      return fail(400, { error: err?.message || 'Failed to add holiday' });
    }
  },

  removeHoliday: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = formData.get('id');
    const hid = formData.get('hid');
    if (!id || !hid) {
      return fail(400, { error: 'Missing holiday id' });
    }
    try {
      await apiRequest(
        `/business-hours/calendar/${id}/holidays/${hid}/`,
        { method: 'DELETE' },
        { cookies, org: locals?.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Failed to remove holiday:', err);
      return fail(400, { error: err?.message || 'Failed to remove holiday' });
    }
  }
};
