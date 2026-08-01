/**
 * Reopen policy — the wiring behind `/settings/reopen`.
 *
 * Server-only. Reads `GET /cases/reopen-policy/`, the per-org singleton
 * (admin-only, auto-created on first read). The endpoint returns the four
 * policy fields (is_enabled, reopen_window_days, reopen_to_status,
 * notify_assigned) alongside three 30-day metrics the settings page draws —
 * reopened_last_30d, replies_after_window_30d, median_days_to_reply — all
 * computed server-side from the reopen audit trail (REOPENED activities + the
 * out-of-window flag the signal writes on late replies).
 *
 * Read-only page: "Edit policy" is a deferred builder (no form on the page yet),
 * so there is no write path to wire here. The whole flat response is the page's
 * `policy` object.
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ policy: any }>}
 */
export async function getReopenPolicy({ cookies }) {
  const policy = await apiRequest('/cases/reopen-policy/', {}, { cookies });
  return { policy };
}
