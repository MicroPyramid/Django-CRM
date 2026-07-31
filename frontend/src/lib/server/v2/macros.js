/**
 * Macros — the wiring behind `/v2/settings/macros`.
 *
 * Server-only. Reads one endpoint, `GET /macros/`, which returns the macros
 * visible to the requester (every org-scope row plus their own personal ones),
 * a `totals` block for the stat cards, and the server's `placeholders` set for
 * the reference card. Visibility is decided by the API from the JWT — a member
 * never sees another member's personal macros — so nothing here filters rows.
 *
 * This page is read-only: it lists and explains macros; the only mutating
 * control ("New macro") is a builder that is not wired yet. There is no write
 * path here.
 *
 * The one reshape is `owner`: the API returns it as a Profile id plus a
 * separate `owner_name` (the owner's email — `User` has no display name), while
 * the page wants a nested `{ id, name }` it can print. Org macros have no owner
 * (they are shared) and stay `null`. `unknown_placeholders` is computed by the
 * server per row and passed straight through — the page never recomputes which
 * tokens are broken, so its "broken placeholder" flag can't drift from the set
 * the renderer actually expands.
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ macros: any[], totals: any, placeholders: any[] }>}
 */
export async function getMacros({ cookies }) {
  const resp = await apiRequest('/macros/', {}, { cookies });
  const results = (resp.results ?? []).map((m) => ({
    ...m,
    owner: m.owner ? { id: m.owner, name: m.owner_name || m.owner } : null
  }));
  return {
    macros: results,
    totals: resp.totals ?? {
      count: 0,
      org: 0,
      personal: 0,
      inactive: 0,
      with_unknown_placeholders: 0
    },
    placeholders: resp.placeholders ?? []
  };
}
