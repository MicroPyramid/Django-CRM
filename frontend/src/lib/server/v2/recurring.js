/**
 * Recurring invoices — the sixteenth v2 module, third of the invoices sub-pages.
 *
 * Same rules as the fifteen before it: server-only, because the access token is
 * an httpOnly cookie; the org is a JWT claim the backend reads, never a param.
 *
 * WHY THIS MODULE, AND THE FINDING IT CARRIED
 * A recurring invoice is an owned billing record — `AssignableMixin` +
 * `created_by`, the same shape as Invoice and Estimate — but its endpoints
 * filtered on `org` ONLY: no object-level check on detail/update/delete/toggle
 * and no non-admin list scoping. Any member could read, edit, delete or
 * pause/resume every schedule in the org, while Invoice and Estimate beside it
 * scoped non-admins to their own and assigned. That was fixed on the backend
 * (a `get_recurring_or_error` mirroring the estimate one, plus list scoping);
 * this page is the client that finally draws the writes those endpoints guard.
 *
 * THE ONE WRITE: PAUSE / RESUME
 * The page's thesis is "does anyone have to do anything" — `auto_send`, and
 * whether a schedule is live or paused. Pause/resume is the one action that
 * belongs on a schedule worklist, so it is wired here (`toggle`) and everything
 * else — creating a schedule, a builder with line items and FK pickers — is
 * deferred, the same class of surface as the invoice builder (#48).
 *
 * TOTALS ARE COMPUTED HERE
 * The list endpoint has no `totals` envelope. The four header figures are
 * derived from the rows the API returns for this requester (org-wide for an
 * admin, own-and-assigned for a member), so the pills and the table describe the
 * same set. `monthly_run_rate` normalises every ACTIVE schedule to a month by
 * its cadence — the one figure nobody can eyeball off the rows, because each is
 * on a different frequency. `limit=1000`; past that the derived figures would
 * undercount, and that ceiling is called out where it is set.
 */
import { apiRequest } from '$lib/api-helpers.js';

const num = (/** @type {any} */ value) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
};

/** Whole days from today to an ISO date; negative when the date is in the past. */
function daysUntil(/** @type {string | null} */ iso) {
  if (!iso) return null;
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return null;
  const startOfDay = (/** @type {Date} */ d) =>
    new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  return Math.round((startOfDay(then) - startOfDay(new Date())) / 86_400_000);
}

/** Times a fixed cadence generates per year; CUSTOM is derived from custom_days. */
const YEARLY_OCCURRENCES = {
  WEEKLY: 52,
  BIWEEKLY: 26,
  MONTHLY: 12,
  QUARTERLY: 4,
  SEMI_ANNUALLY: 2,
  YEARLY: 1
};

/** One schedule's contribution to the monthly run rate: amount × runs-per-month. */
function monthlyRunRate(/** @type {any} */ s) {
  let perYear;
  if (s.frequency === 'CUSTOM') {
    perYear = s.custom_days ? 365.25 / s.custom_days : 0;
  } else {
    perYear = YEARLY_OCCURRENCES[s.frequency] ?? 0;
  }
  return (s.total_amount * perYear) / 12;
}

/**
 * A list row from `RecurringInvoiceListSerializer`. The account is split into an
 * `account` uuid and `account_name`; the page wants the nested `{ id, name }`,
 * and reads `contact` as a plain name.
 *
 * @param {any} row
 */
function toRow(row) {
  return {
    id: row.id,
    title: row.title || '(untitled schedule)',
    is_active: Boolean(row.is_active),
    account: { id: row.account ?? null, name: row.account_name ?? '(no account)' },
    contact: row.contact_name ?? row.client_name ?? '',
    frequency: row.frequency,
    custom_days: row.custom_days ?? null,
    payment_terms: row.payment_terms,
    start_date: row.start_date ?? null,
    end_date: row.end_date ?? null,
    next_generation_date: row.next_generation_date ?? null,
    auto_send: Boolean(row.auto_send),
    total_amount: num(row.total_amount),
    currency: row.currency ?? 'USD',
    invoices_generated: row.invoices_generated ?? 0
  };
}

/**
 * The four header figures, derived from the visible rows.
 *
 * - `active` — schedules currently generating.
 * - `monthly_run_rate` — every active schedule normalised to a month.
 * - `due_within_7d` — active schedules generating within a week (or overdue):
 *   drafts to check before they send.
 *
 * @param {any[]} rows
 */
function computeTotals(rows) {
  let active = 0;
  let runRate = 0;
  let due_within_7d = 0;
  for (const s of rows) {
    if (!s.is_active) continue;
    active += 1;
    runRate += monthlyRunRate(s);
    const d = daysUntil(s.next_generation_date);
    if (d !== null && d <= 7) due_within_7d += 1;
  }
  return { active, monthly_run_rate: Math.round(runRate), due_within_7d };
}

/** Active schedules first, then soonest to next generate. */
function bySchedulePriority(/** @type {any} */ a, /** @type {any} */ b) {
  if (a.is_active !== b.is_active) return Number(b.is_active) - Number(a.is_active);
  const da = daysUntil(a.next_generation_date);
  const db = daysUntil(b.next_generation_date);
  if (da === null) return 1;
  if (db === null) return -1;
  return da - db;
}

/**
 * The schedules worklist. Rows follow whatever the API returns for the requester
 * (the endpoint scopes non-admins to their own and assigned), so the pills and
 * the table cover the same set.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 */
export async function listRecurringInvoices({ cookies }) {
  const query = new URLSearchParams();
  // One page covers every real org; totals derive from what comes back.
  query.set('limit', '1000');

  const response = await apiRequest(`/invoices/recurring/?${query.toString()}`, {}, { cookies });
  const rows = (response.results ?? []).map(toRow);
  rows.sort(bySchedulePriority);

  return {
    schedules: rows,
    totals: {
      count: response.count ?? rows.length,
      ...computeTotals(rows)
    }
  };
}

/**
 * Pause or resume a schedule. A bare POST through `get_recurring_or_error`, so
 * the API — not this layer — decides who may toggle (creator, an assignee, or
 * an admin) and refuses the rest. The endpoint flips `is_active` and returns the
 * updated row.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} id
 */
export async function toggleRecurring({ cookies }, id) {
  return apiRequest(`/invoices/recurring/${id}/toggle/`, { method: 'POST', body: {} }, { cookies });
}
