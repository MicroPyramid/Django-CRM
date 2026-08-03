import { listTasks } from '$lib/server/v2/tasks.js';

/**
 * The task calendar: the third face of Tasks, after the list and the boards.
 *
 * v1 had a `/tasks/calendar` route that only redirected: the calendar was a
 * view-mode folded into the main tasks page. Here it is its own page under the
 * Tasks tabs, reading the same list endpoint the queue reads, so it inherits
 * the queue's visibility rule exactly (an admin sees the org's tasks, a member
 * sees the ones they made or were handed) with no new authorisation surface.
 *
 * Only DATED, month-windowed tasks are fetched: the API is asked for the grid's
 * date range with `due_date__gte`/`due_date__lte`, so a calendar of July never
 * pulls a year of rows. Tasks with no due date can't sit on a day and so don't
 * appear here at all. The page says so, and points at the list where they live.
 */

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December'
];

/** Local-time `YYYY-MM-DD`. Built from date parts, never `toISOString()`, so a
 *  day never slips across midnight UTC into the wrong cell. */
function ymd(/** @type {Date} */ d) {
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${m}-${day}`;
}

/** `?month=YYYY-MM` → `{ year, month }` (month 0-based), or the current month
 *  when absent or malformed. Range-checked so a hand-typed URL can't throw. */
function resolveMonth(/** @type {string | null} */ raw, /** @type {Date} */ now) {
  const match = /^(\d{4})-(\d{2})$/.exec(raw ?? '');
  if (match) {
    const year = Number(match[1]);
    const month = Number(match[2]) - 1;
    if (year >= 1970 && year <= 9999 && month >= 0 && month <= 11) {
      return { year, month };
    }
  }
  return { year: now.getFullYear(), month: now.getMonth() };
}

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  const now = new Date();
  const { year, month } = resolveMonth(event.url.searchParams.get('month'), now);

  // Monday-start grid. `offset` is how many days of the previous month lead the
  // 1st; `cells` rounds up to whole weeks so the grid is always 4-6 clean rows.
  const first = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const offset = (first.getDay() + 6) % 7; // JS Sun=0..Sat=6 → Mon=0..Sun=6
  const cellCount = Math.ceil((offset + daysInMonth) / 7) * 7;
  const gridStart = new Date(year, month, 1 - offset);
  const gridEnd = new Date(year, month, 1 - offset + cellCount - 1);
  const todayStr = ymd(now);

  // Ask only for the window the grid shows. `limit` is generous for a month;
  // if the org somehow exceeds it we flag truncation rather than lie.
  const params = new URLSearchParams();
  params.set('due_date__gte', ymd(gridStart));
  params.set('due_date__lte', ymd(gridEnd));
  params.set('limit', '250');
  const { results, totals } = await listTasks(event, params);

  // Group by due date once, so each cell is a lookup rather than a scan.
  /** @type {Record<string, any[]>} */
  const byDate = {};
  for (const task of results) {
    if (!task.due_date) continue;
    (byDate[task.due_date] ??= []).push({
      id: task.id,
      title: task.title,
      priority: task.priority,
      is_done: task.is_done,
      status: task.status,
      overdue: !task.is_done && task.due_date < todayStr,
      related: task.related
    });
  }

  /** @type {any[][]} */
  const weeks = [];
  for (let i = 0; i < cellCount; i++) {
    const d = new Date(year, month, 1 - offset + i);
    const dateStr = ymd(d);
    const dow = d.getDay();
    const cell = {
      date: dateStr,
      day: d.getDate(),
      inMonth: d.getMonth() === month,
      isToday: dateStr === todayStr,
      isWeekend: dow === 0 || dow === 6,
      tasks: byDate[dateStr] ?? []
    };
    if (i % 7 === 0) weeks.push([]);
    weeks[weeks.length - 1].push(cell);
  }

  // Agenda for narrow screens: only the days in this month that carry work,
  // in order. Built from the same cells so the two views can never disagree.
  const agenda = weeks
    .flat()
    .filter((c) => c.inMonth && c.tasks.length > 0)
    .map((c) => ({ date: c.date, day: c.day, isToday: c.isToday, tasks: c.tasks }));

  // Count only tasks whose due date is IN this month. The leading/trailing
  // cells can carry a day or two of the neighbouring months, and the header
  // says "July", so a spillover task must not inflate July's number.
  const monthKey = `${year}-${String(month + 1).padStart(2, '0')}`;
  const shown = results.filter(
    (/** @type {any} */ t) => t.due_date && t.due_date.slice(0, 7) === monthKey
  ).length;

  return {
    year,
    month,
    monthLabel: `${MONTHS[month]} ${year}`,
    weekdays: WEEKDAYS,
    weeks,
    agenda,
    today: todayStr,
    prevMonth: monthParam(year, month - 1),
    nextMonth: monthParam(year, month + 1),
    thisMonth: monthParam(now.getFullYear(), now.getMonth()),
    isThisMonth: year === now.getFullYear() && month === now.getMonth(),
    // The header counts this month's dated tasks; `truncated` compares rows
    // fetched against the total the date filter matched, so it only fires when
    // the window genuinely overflowed the fetch limit.
    datedCount: shown,
    truncated: (totals?.matched ?? results.length) > results.length
  };
}

/** `YYYY-MM` for a (possibly out-of-range) month index, normalised. */
function monthParam(/** @type {number} */ year, /** @type {number} */ month) {
  const d = new Date(year, month, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}
