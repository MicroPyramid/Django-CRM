/**
 * Business hours — the wiring behind `/settings/business-hours`.
 *
 * Server-only. Reads `GET /business-hours/calendar/`, the org's default
 * calendar (created on first read if missing). This is the calendar every SLA
 * target is measured against.
 *
 * Reshape, not analytics. The backend stores the week as fourteen flat
 * TimeFields (`monday_open`/`monday_close` … `sunday_open`/`sunday_close`, a
 * null pair meaning "closed") and serializes each as "HH:MM:SS". The page reads
 * an ordered `days: [{ day, open, close }]` Monday-first, with times as "HH:MM",
 * so fold the flat fields into that array here and trim the seconds. Holidays
 * already arrive as `{ id, date, name }`.
 *
 * Read-only page: "Edit hours" / "Add holiday" are deferred builders (the
 * backend has admin PUT/POST/DELETE endpoints, but no form is wired yet), so
 * there is no write path here.
 */
import { apiRequest } from '$lib/api-helpers.js';

/** Monday-first weekday label ↔ the model's field prefix. */
const WEEKDAYS = [
  ['Monday', 'monday'],
  ['Tuesday', 'tuesday'],
  ['Wednesday', 'wednesday'],
  ['Thursday', 'thursday'],
  ['Friday', 'friday'],
  ['Saturday', 'saturday'],
  ['Sunday', 'sunday']
];

/** "09:00:00" → "09:00"; null/"" stays null (a closed day). */
function toHm(value) {
  return value ? value.slice(0, 5) : null;
}

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ calendar: any }>}
 */
export async function getBusinessHours({ cookies }) {
  const cal = await apiRequest('/business-hours/calendar/', {}, { cookies });
  return {
    calendar: {
      id: cal.id,
      name: cal.name,
      timezone: cal.timezone,
      is_default: cal.is_default,
      days: WEEKDAYS.map(([label, key]) => ({
        day: label,
        open: toHm(cal[`${key}_open`]),
        close: toHm(cal[`${key}_close`])
      })),
      holidays: (cal.holidays ?? []).map((h) => ({
        id: h.id,
        name: h.name,
        date: h.date
      }))
    }
  };
}
