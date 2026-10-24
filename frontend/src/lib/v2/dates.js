/**
 * Calendar dates for a form's defaults, as `YYYY-MM-DD`.
 *
 * "Today" is the org's day, not UTC's and not the browser's: an invoice raised
 * at 09:00 in Kolkata is dated that day, although UTC still reads yesterday.
 * The zone comes from the layout (`data.org.timezone`, the JWT's org claim).
 */

/**
 * Today in `timeZone`. A zone the runtime does not know falls back to UTC, the
 * API's own default zone, rather than throwing on a form's first render.
 *
 * @param {string} timeZone IANA name, e.g. `Asia/Kolkata`
 * @param {Date} [now]
 */
export function todayIn(timeZone, now = new Date()) {
  let parts;
  try {
    parts = new Intl.DateTimeFormat('en-US', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).formatToParts(now);
  } catch {
    return now.toISOString().slice(0, 10);
  }
  /** @param {string} type */
  const part = (type) => parts.find((p) => p.type === type)?.value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}

/**
 * `days` after a `YYYY-MM-DD` date. Pure calendar arithmetic in UTC, so no
 * zone can move the answer.
 *
 * @param {string} isoDate
 * @param {number} days
 */
export function addDays(isoDate, days) {
  const d = new Date(`${isoDate}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/**
 * A `datetime-local` value (`YYYY-MM-DDTHH:MM`, seconds optional) read as the
 * wall clock in `timeZone`, as an ISO instant. Null for anything else,
 * impossible dates included. A zone the runtime does not know reads as UTC.
 *
 * @param {string | null | undefined} local
 * @param {string} timeZone IANA name
 * @returns {string | null}
 */
export function wallTimeToIso(local, timeZone) {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(String(local ?? ''));
  if (!m) return null;
  const [y, mo, d, h, mi, s] = m.slice(1).map((v) => Number(v ?? 0));
  const wall = Date.UTC(y, mo - 1, d, h, mi, s);
  const check = new Date(wall);
  if (check.getUTCMonth() !== mo - 1 || check.getUTCDate() !== d || h > 23 || mi > 59 || s > 59) {
    return null;
  }
  // The second pass settles a first guess that landed across a DST change.
  let instant = wall - zoneOffset(wall, timeZone);
  instant = wall - zoneOffset(instant, timeZone);
  return new Date(instant).toISOString();
}

/**
 * How far `timeZone`'s wall clock is ahead of UTC at `instant`, in ms.
 *
 * @param {number} instant
 * @param {string} timeZone
 */
function zoneOffset(instant, timeZone) {
  let parts;
  try {
    parts = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hourCycle: 'h23',
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      second: 'numeric'
    }).formatToParts(new Date(instant));
  } catch {
    return 0;
  }
  /** @param {string} type */
  const part = (type) => Number(parts.find((p) => p.type === type)?.value);
  const wall = Date.UTC(
    part('year'),
    part('month') - 1,
    part('day'),
    part('hour'),
    part('minute'),
    part('second')
  );
  return wall - Math.floor(instant / 1000) * 1000;
}
