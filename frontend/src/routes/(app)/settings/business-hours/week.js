/**
 * What a week of business hours adds up to.
 *
 * Client-side display logic, in its own module rather than inline in
 * `+page.svelte`, because the harness cannot import a `.svelte` file and this
 * is a rule with a right answer that lives in `business_hours/calendar.py`.
 * The routing and escalation routes do the same with `rotation.js` and
 * `outcome.js`.
 *
 * `mobile/lib/data/models/business_calendar.dart` carries the same rules.
 */

/**
 * Hours a day is open, or 0.
 *
 * Zero for a day whose close is not after its open, which is what
 * `_has_any_open_window` does with the same pair (`c > o`) and what the walker
 * does per day (`close_t <= open_t` counts as closed). The serializer refuses
 * that combination on write, so it can only arrive from older data, but it can
 * arrive.
 *
 * @param {{ open: string | null, close: string | null }} day
 */
export function dayHours(day) {
  if (!day?.open || !day?.close) return 0;
  const [oh, om] = day.open.split(':').map(Number);
  const [ch, cm] = day.close.split(':').map(Number);
  if ([oh, om, ch, cm].some((n) => Number.isNaN(n))) return 0;
  const span = ch * 60 + cm - (oh * 60 + om);
  return span > 0 ? span / 60 : 0;
}

/** @param {{ open: string | null, close: string | null }[]} days */
export function weeklyHours(days) {
  return (days ?? []).reduce((total, day) => total + dayHours(day), 0);
}

/**
 * Whether this calendar is consulted at all.
 *
 * **A calendar with no open window is a 24/7 calendar, not a closed one.**
 * `add_business_hours` checks `_has_any_open_window` first and, when nothing is
 * open, returns `start_dt + timedelta(hours=hours)`: plain wall-clock
 * arithmetic, holidays included. So marking every day Closed does not stop the
 * SLA clock, it makes it run continuously, which is the opposite of what a page
 * showing seven "Closed" rows otherwise implies. The one state where this page
 * has to contradict its own rows.
 *
 * @param {{ open: string | null, close: string | null }[]} days
 */
export function isAlwaysOn(days) {
  return (days ?? []).every((day) => dayHours(day) <= 0);
}
