/**
 * Custom fields — the wiring behind `/v2/settings/custom-fields`.
 *
 * Server-only. Reads `GET /custom-fields/` (no filter, so it returns every
 * definition including the turned-off ones the page dims). Each row carries the
 * computed `records_missing_value` — how many records of that target_model
 * predate the field and hold no value for it — and the response includes a
 * `totals` block { count, active, models_extended, required_with_gaps } for the
 * stat cards. Both are org-scoped server-side; the page never counts records.
 *
 * Read-only page: "New field" is a deferred builder, and the rows have no
 * inline edit/toggle controls. No write path here. The page groups by
 * target_model and orders by display_order itself.
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ fields: any[], totals: any }>}
 */
export async function getCustomFields({ cookies }) {
  const resp = await apiRequest('/custom-fields/', {}, { cookies });
  return {
    fields: resp.definitions ?? [],
    totals: resp.totals ?? {
      count: 0,
      active: 0,
      models_extended: 0,
      required_with_gaps: 0
    }
  };
}
