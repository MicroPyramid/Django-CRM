/**
 * Service analytics: the wiring behind /v2/tickets/analytics.
 *
 * Server-only. One admin-only backend call, `/cases/analytics/service/`,
 * returns the whole "service health" page shape; this layer only re-keys the
 * top level from the backend's snake_case (`first_response`, `by_type`,
 * `by_agent`) to the camelCase the page reads (`firstResponse`, `byType`,
 * `byAgent`). The inner field names are already what the page reads.
 *
 * WHY THIS IS ADMIN-ONLY
 * These are org-wide support KPIs: opened/closed volume, first-response
 * attainment across every priority, the case-type mix, and a leaderboard of
 * who is carrying the queue. The per-metric analytics endpoints narrow a
 * non-admin to their own cases; showing a rep those same figures under
 * org-wide headings would misrepresent them. The backend 403s a non-admin and
 * this layer surfaces `can_view` so the page can say so plainly rather than
 * render a dashboard built from a personal slice.
 */
import { apiRequest } from '$lib/api-helpers.js';

/** A fully-shaped but empty payload, so a non-admin render never throws. */
const EMPTY = {
  totals: {
    opened: 0,
    closed: 0,
    open_now: 0,
    median_resolution_hours: 0,
    window_days: 14,
    business_hours_applied: false,
    calendar_name: null
  },
  volume: [],
  firstResponse: [],
  byType: [],
  byAgent: []
};

/**
 * The service-analytics dashboard, shaped for the page. Admin-only: a non-admin
 * gets `{ can_view: false }` and the empty-but-valid shape above.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string | number} [days] optional window length in days (backend clamps 1-90)
 */
export async function getServiceAnalytics({ cookies }, days) {
  const query = days ? `?days=${encodeURIComponent(days)}` : '';
  let data;
  try {
    data = await apiRequest(`/cases/analytics/service/${query}`, {}, { cookies });
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) return { can_view: false, ...EMPTY };
    throw err;
  }
  return {
    can_view: true,
    totals: data.totals ?? EMPTY.totals,
    volume: data.volume ?? [],
    firstResponse: data.first_response ?? [],
    byType: data.by_type ?? [],
    byAgent: data.by_agent ?? []
  };
}
