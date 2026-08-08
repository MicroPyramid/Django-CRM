/**
 * API tokens: the tenth v2 module wired to the real API.
 *
 * Lives under `$lib/server` like the nine before it: this directory is the one
 * SvelteKit refuses to bundle into client code, and a token is a bearer
 * credential the browser must never handle except for the single moment it is
 * shown. Org is a JWT claim, never a parameter.
 *
 * WHY THIS PAGE IS ADMIN-ONLY, AND WHAT IT READS
 * This is the *oversight* view: every token across the org, so an admin can
 * spot the two rows worth acting on. One whose owner was deactivated, and one
 * nobody has used in months. That is inherently cross-user, so it reads a NEW
 * admin-gated endpoint (`GET /api/org/tokens/`). The pre-existing
 * `/api/profile/tokens/` stays self-scoped and untouched.
 *
 * The self-scoped half lives here too (`listMyTokens` / `revokeMyToken`) and
 * feeds /profile/tokens. The two are kept apart on purpose: the oversight
 * endpoints are admin-gated and org-wide, the self ones are open to any member
 * and filtered to `profile=request.profile` server-side, and widening either
 * into the other is how a self guard stops being one.
 *
 * WHAT THE MOCK ASSERTED THAT THE BACKEND DOES NOT
 * The fixture's headline was "a token whose owner was deactivated keeps working
 * with the role they had." It does not. `resolve_valid_pat` rejects a token
 * whose `profile.is_active` is false, and deactivating someone sets exactly
 * that flag (common/tests/test_pat_auth.py::test_inactive_profile_raises proves
 * it). So an "owner deactivated" token is dormant, refused at login today,
 * revived only if the account is reactivated. The page says that instead: still
 * worth revoking on offboarding, but not a live credential. (The /v2/team page
 * carried the same false claim; corrected there too.)
 *
 * WRITES
 * - Create posts to the self-scoped `/api/profile/tokens/`. A token can only
 *   ever be created for yourself (the server sets `profile=request.profile`);
 *   there is no "create on behalf of", by design. The raw value comes back
 *   once, in that response, and is never retrievable again.
 * - Revoke posts to the admin `DELETE /api/org/tokens/<id>/`. Org-scoped, so
 *   an admin can retire any token in their own org (a colleague's included).
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * Live first, then most-recently-used first, the order an admin scans in,
 * with the dormant and revoked rows sinking to the bottom.
 *
 * @param {any} a
 * @param {any} b
 */
function byUrgency(a, b) {
  if (a.is_live !== b.is_live) return a.is_live ? -1 : 1;
  return new Date(b.last_used_at ?? 0).getTime() - new Date(a.last_used_at ?? 0).getTime();
}

/**
 * The oversight list. `/api/org/tokens/` is admin-only; a non-admin who reaches
 * this settings page (the nav shows it) gets a clean `forbidden` state rather
 * than a crash. The same shape [[/v2/team]] uses.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 */
export async function listOrgTokens({ cookies }) {
  let resp;
  try {
    resp = await apiRequest('/org/tokens/', {}, { cookies });
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) return { forbidden: true };
    throw err;
  }

  const tokens = (resp?.tokens ?? []).slice().sort(byUrgency);
  return {
    forbidden: false,
    tokens,
    totals: resp?.totals ?? { count: 0, live: 0, orphaned: 0, unused_90d: 0 },
    // Ids of the live tokens on deactivated owners, so "revoke them all" can be
    // one submit instead of the admin hunting each row. Derived from the same
    // rows the page renders, no second source to drift.
    orphaned_ids: tokens
      .filter((/** @type {any} */ t) => t.is_live && !t.owner?.is_active)
      .map((/** @type {any} */ t) => t.id)
  };
}

/**
 * Create a token for the signed-in admin. `POST /api/profile/tokens/` sets the
 * owner server-side from the JWT, so there is no way to mint one for someone
 * else. Returns the created row plus `token`, the raw value, shown once.
 *
 * `scopes` is `<resource>:<action>` strings, validated against the vocabulary in
 * `common/scopes.py` and enforced in middleware before the view runs. An empty
 * list means unrestricted, which is what every token predating enforcement
 * carries, so omitting it preserves the old behaviour rather than locking a
 * token out of everything.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {{ name: string, expires_at?: string | null, scopes?: string[] }} body
 */
export function createToken({ cookies }, body) {
  return apiRequest('/profile/tokens/', { method: 'POST', body }, { cookies });
}

/**
 * Revoke a token: `DELETE /api/org/tokens/<id>/`. Admin-only and org-scoped, so
 * a foreign id 404s rather than being revoked cross-tenant. Idempotent.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} id  the token id
 */
export function revokeToken({ cookies }, id) {
  return apiRequest(`/org/tokens/${id}/`, { method: 'DELETE' }, { cookies });
}

/**
 * Your own tokens. `GET /api/profile/tokens/` filters on
 * `org=request.profile.org` AND `profile=request.profile`, so this cannot
 * return anybody else's row whatever this page does.
 *
 * Open to every member, which is the point: the endpoint has always been
 * self-service and until now the only page in either client that touched
 * tokens was the admin oversight list, which 403s a member on the read. So the
 * endpoint was reachable by curl and by nothing else.
 *
 * `is_live` is not on this payload the way it is on the oversight one, so it
 * is derived here from the same two facts the model uses: not revoked, and not
 * past its expiry. The rules module reads `is_live`, and a row without it
 * would draw every live token as expired.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 */
export async function listMyTokens({ cookies }) {
  const resp = await apiRequest('/profile/tokens/', {}, { cookies });
  const now = Date.now();
  const tokens = (resp?.tokens ?? [])
    .map((/** @type {any} */ t) => ({
      ...t,
      is_live: !t.revoked_at && !(t.expires_at && new Date(t.expires_at).getTime() <= now)
    }))
    .sort(byUrgency);
  return {
    tokens,
    live: tokens.filter((/** @type {any} */ t) => t.is_live).length
  };
}

/**
 * Revoke one of your own: `DELETE /api/profile/tokens/<id>/`. Self-scoped
 * server-side, so a colleague's id 404s here rather than being revoked. That
 * is why this is a separate function from `revokeToken` above, which is the
 * admin's org-wide one; calling the admin path from a member's page would 403
 * them out of retiring their own credential.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} id
 */
export function revokeMyToken({ cookies }, id) {
  return apiRequest(`/profile/tokens/${id}/`, { method: 'DELETE' }, { cookies });
}
