/**
 * Invoice reports: the seventeenth v2 module, fourth of the invoices sub-pages.
 *
 * Server-only, like the sixteen before it. This one fans three endpoints,
 * `/invoices/reports/{dashboard,revenue,aging}/`: into the single shape the
 * "Where the money is" page reads.
 *
 * WHY THIS IS ADMIN-ONLY
 * These are org-wide financial roll-ups: total invoiced and collected, revenue
 * by month, AR aging, and who owes what across every account. The invoice and
 * estimate *lists* scope a non-admin to their own records; a report that showed
 * a rep the whole org's revenue and receivables would leak exactly what those
 * scopes protect. The three endpoints are admin-only on the backend, and this
 * layer surfaces a `can_view` flag so the page can say so plainly rather than
 * rendering a broken dashboard. The backend is still the one enforcing it.
 *
 * WHAT THE PAGE NEEDED THAT THE ENDPOINTS DID NOT HAVE
 * The dashboard gained `average_days_to_pay` and `invoice_count`; the revenue
 * report gained an `invoiced` series alongside `revenue` (paid), the two counted
 * on different dates on purpose; the aging report gained a `by_account` roll-up
 * (the "who owes it" table. The capped per-bucket invoice lists could not give
 * it). All added to the real endpoints, not faked here.
 */
import { apiRequest } from '$lib/api-helpers.js';

const num = (/** @type {any} */ value) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
};

/** The header window; the revenue call asks for the trailing 12 months. */
const WINDOW_MONTHS = 12;

/** A fully-shaped but empty dashboard, so a non-admin render never throws. */
const EMPTY = {
  dashboard: {
    window_months: WINDOW_MONTHS,
    invoice_count: 0,
    total_invoiced: 0,
    total_paid: 0,
    overdue_amount: 0,
    average_days_to_pay: 0
  },
  revenue: [],
  aging: {
    not_yet_due: { amount: 0, count: 0 },
    buckets: [
      { key: '1_30', label: '1-30 days', amount: 0, count: 0 },
      { key: '31_60', label: '31-60 days', amount: 0, count: 0 },
      { key: '61_90', label: '61-90 days', amount: 0, count: 0 },
      { key: '90_plus', label: 'Over 90 days', amount: 0, count: 0 }
    ],
    overdue_count: 0
  },
  overdueByAccount: []
};

/**
 * The invoice reports, shaped for the dashboard page. Admin-only: a non-admin
 * gets `{ can_view: false }` and an empty-but-valid shape, so the page shows the
 * "admins only" state without the deriveds tripping over missing data.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 */
export async function listReports({ cookies }) {
  let dashboard;
  let revenue;
  let aging;
  try {
    [dashboard, revenue, aging] = await Promise.all([
      apiRequest('/invoices/reports/dashboard/', {}, { cookies }),
      apiRequest('/invoices/reports/revenue/?group_by=month', {}, { cookies }),
      apiRequest('/invoices/reports/aging/', {}, { cookies })
    ]);
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) return { can_view: false, ...EMPTY };
    throw err;
  }

  const summary = dashboard.summary ?? {};
  const agingOverdue = aging.overdue ?? {};

  return {
    can_view: true,
    dashboard: {
      window_months: WINDOW_MONTHS,
      invoice_count: dashboard.invoice_count ?? 0,
      total_invoiced: num(summary.total_invoiced),
      total_paid: num(summary.total_paid),
      // The overdue stat is sourced from the aging report so the number over the
      // chart is the same number the chart draws.
      overdue_amount: num(agingOverdue.amount),
      average_days_to_pay: dashboard.average_days_to_pay ?? 0
    },
    revenue: (revenue.data ?? []).map((/** @type {any} */ r) => ({
      period: r.period,
      invoiced: num(r.invoiced),
      paid: num(r.revenue)
    })),
    aging: {
      not_yet_due: {
        amount: num(aging.current?.amount),
        count: aging.current?.count ?? 0
      },
      buckets: [
        {
          key: '1_30',
          label: '1-30 days',
          amount: num(aging['1_30_days']?.amount),
          count: aging['1_30_days']?.count ?? 0
        },
        {
          key: '31_60',
          label: '31-60 days',
          amount: num(aging['31_60_days']?.amount),
          count: aging['31_60_days']?.count ?? 0
        },
        {
          key: '61_90',
          label: '61-90 days',
          amount: num(aging['61_90_days']?.amount),
          count: aging['61_90_days']?.count ?? 0
        },
        {
          key: '90_plus',
          label: 'Over 90 days',
          amount: num(aging['over_90_days']?.amount),
          count: aging['over_90_days']?.count ?? 0
        }
      ],
      overdue_count: agingOverdue.count ?? 0
    },
    overdueByAccount: (aging.by_account ?? []).map((/** @type {any} */ a) => ({
      id: a.id,
      name: a.name,
      count: a.count,
      oldest_days: a.oldest_days,
      amount: num(a.amount)
    }))
  };
}
