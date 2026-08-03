/**
 * Vertical packs: the pack chooser shown at org creation.
 *
 * Server-only, matching every other `$lib/server/*` module: the JWT cookie
 * never leaves the server. `apiRequest` lives at `$lib/api-helpers.js` (NOT
 * `$lib/server/api`: that module does not exist) and its `API_BASE_URL`
 * already includes `/api`, so endpoints here are given WITHOUT the `/api`
 * prefix, same as every neighbouring module (see `$lib/server/v2/tags.js`,
 * `$lib/server/v2/organization.js`).
 *
 * GET /api/packs/ needs IsAuthenticated only, no org context. It is exempt
 * from HasOrgContext / RequireOrgContext (see `PackListView` and
 * `EXEMPT_EXACT_PATHS` in `common/middleware/rls_context.py`) precisely so a
 * brand-new user with zero orgs, who has no `org_id` claim on their JWT yet,
 * can still list packs on `/org/new`, the "first ever org" page. Callers must
 * still treat a failed listPacks() as "no packs available" rather than
 * letting the error propagate and break the page. This call can still fail
 * for other reasons (network, auth token expiry, etc).
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * The minimal shape `apiRequest` actually needs: something with a `.get()`
 * that returns the access token. A real SvelteKit `Cookies` satisfies this
 * structurally, but so does a throwaway bearer-only reader that is never
 * connected to the response's Set-Cookie headers. See `applyPack`'s use in
 * `org/new/+page.server.js`, where callers deliberately pass one instead of
 * the real cookie jar so an org-scoped token minted mid-request never gets
 * persisted to the caller's session.
 * @typedef {{ get: (name: string) => string | undefined }} CookieReader
 */

/**
 * @param {import('@sveltejs/kit').Cookies | CookieReader} cookies
 * @returns {Promise<Array<{ id: string, name: string, description: string, version: string }>>}
 */
export async function listPacks(cookies) {
  // apiRequest's own type only accepts a real Cookies here; at runtime it
  // only ever calls `.get()`, which both a real Cookies and a CookieReader
  // provide, so this cast is safe.
  const res = await apiRequest(
    '/packs/',
    { method: 'GET' },
    { cookies: /** @type {import('@sveltejs/kit').Cookies} */ (cookies) }
  );
  return res?.packs ?? [];
}

/**
 * POST /api/packs/<id>/apply/, ADMIN only, org derived server-side from
 * `request.profile.org`. Caller must supply cookies that already carry a
 * token scoped to the org the pack should apply to.
 *
 * @param {import('@sveltejs/kit').Cookies | CookieReader} cookies
 * @param {string} packId
 * @returns {Promise<{ report: { created: any[], skipped: any[], failed: any[] } }>}
 */
export async function applyPack(cookies, packId) {
  return apiRequest(
    `/packs/${encodeURIComponent(packId)}/apply/`,
    { method: 'POST' },
    { cookies: /** @type {import('@sveltejs/kit').Cookies} */ (cookies) }
  );
}

/**
 * DELETE /api/packs/sample-data/: ADMIN only, org derived server-side.
 * Deletes the demo records this org's applier created: accounts, contacts,
 * deals, tickets, tasks and leads carrying `is_sample`, and nothing else. See
 * `backend/common/packs/applier.py:clear_sample_data`. Real records, and
 * another org's sample records, are untouched.
 *
 * `retained_by_type` is a normal outcome rather than a failure: a demo record
 * the user has since attached their own work to (a real deal on a sample
 * account, billable time on a sample ticket, an invoice raised against a sample
 * account) is deliberately kept, because deleting it would take that work with
 * it, or, for the invoice case, fail outright on a PROTECT constraint. Surface
 * it to the user; do not treat it as an error.
 *
 * There is no separate endpoint to preview this count before deleting.
 * The applier module exposes exactly list/apply/clear, no dry-run. A caller
 * wanting to confirm "how many?" ahead of time has nothing authoritative to
 * ask; the count only exists once this call has already acted.
 *
 * @param {import('@sveltejs/kit').Cookies | CookieReader} cookies
 * @returns {Promise<{ deleted: number, deleted_by_type: Record<string, number>, retained_by_type: Record<string, number> }>}
 */
export async function clearSampleData(cookies) {
  return apiRequest(
    '/packs/sample-data/',
    { method: 'DELETE' },
    { cookies: /** @type {import('@sveltejs/kit').Cookies} */ (cookies) }
  );
}
