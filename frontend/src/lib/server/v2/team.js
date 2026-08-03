/**
 * Team and access: the ninth v2 module wired to the real API.
 *
 * Lives under `$lib/server` for the same reason as the eight before it:
 * SvelteKit refuses to bundle this directory into client code, and the access
 * token is an httpOnly cookie the browser must never see. Org is a JWT claim,
 * never a parameter.
 *
 * WHY THIS MODULE
 * This is the access-control page: who is an admin, who has been deactivated,
 * and whose API tokens still authenticate after their login was pulled. Wiring
 * it meant driving `/api/users/` and `/api/user/<id>/` for real, and those are
 * the endpoints where a plain member could PATCH their own profile to
 * role="ADMIN" and become an org admin. The page's own header comment claimed
 * "the server refuses to let anyone change their own role"; it did not. Fixing
 * that (in common/views/user_views.py + CreateProfileSerializer) is the point
 * of this migration; the wiring is what proved it end to end.
 *
 * WHAT THE MOCK ASSUMED THAT THE API DID NOT
 * - **Names.** The fixture split every person into `first_name`/`last_name`.
 *   `User` has a single `name`; the real `user_details` carries `name` (and
 *   `email`, `last_login`), so that is what the page shows, falling back to the
 *   email when someone was invited and has no name yet.
 * - **Per-member teams.** `ProfileSerializer` does not list a person's teams.
 *   They are derived here from `/api/teams/`, whose serializer nests each
 *   team's members, one source of truth, not a second field that could drift.
 * - **Token counts.** The one genuinely urgent thing this page surfaces. A
 *   live token on a deactivated account. Needs a real count, so the users list
 *   now returns `active_token_count` per profile (computed once server-side,
 *   not on the shared serializer). No count is invented.
 *
 * WHAT STAYED FIXTURES, ON PURPOSE
 * The People/access half is wired: list, invite, role change, activate and
 * deactivate. Team CRUD (create/edit membership) is a separate write surface
 * with its own picker UI and is left for later, exactly as estimates were left
 * beside invoices. The teams list still renders, read-only, because the
 * people rows need it to show who is on what.
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * Profile.role is ADMIN | USER, the only two the backend recognises. There is
 * no MANAGER despite ApprovalRule offering it; a picker offering a value the
 * server rejects is worse than not offering it.
 */
export const ROLES = ['ADMIN', 'USER'];

/**
 * The signed-in user's id, read from the `user_id` claim of the access token.
 *
 * Used only to mark ", you" on a row and to withhold the controls a person
 * must not use on themselves. It is a display hint, never an authorization
 * decision: the server re-derives identity from the same token and is the
 * thing that actually refuses a self-role-change. Decoded, not verified.
 * Verifying our own freshly-read cookie would buy nothing.
 *
 * @param {import('@sveltejs/kit').Cookies} cookies
 * @returns {string | null}
 */
function viewerUserId(cookies) {
  const token = cookies.get('jwt_access');
  if (!token) return null;
  try {
    const payload = token.split('.')[1];
    const json = Buffer.from(payload, 'base64url').toString('utf-8');
    return JSON.parse(json).user_id ?? null;
  } catch {
    return null;
  }
}

/**
 * One person as the page reads it, from a `ProfileSerializer` row.
 *
 * `id` is the profile id; `user_id` is the User id, which is the pk every
 * `/api/user/<id>/` verb takes. Keeping both here means the template never has
 * to remember which one an action needs.
 *
 * @param {any} p
 * @param {Record<string, string[]>} teamsByProfile
 * @param {string | null} viewerId
 */
function toMember(p, teamsByProfile, viewerId) {
  const details = p.user_details ?? {};
  return {
    id: p.id,
    user_id: details.id,
    name: details.name || details.email || 'Unnamed',
    email: details.email,
    role: p.role,
    is_active: p.is_active,
    teams: teamsByProfile[p.id] ?? [],
    last_login: details.last_login ?? null,
    active_token_count: p.active_token_count ?? 0,
    is_you: !!viewerId && details.id === viewerId
  };
}

/**
 * The team-and-access page.
 *
 * `/api/users/` and `/api/teams/` are both admin-only. A non-admin who reaches
 * this page (the nav shows it to everyone) gets a clean "admins only" state
 * rather than an error: `forbidden` is the API's 403 turned into a fact the
 * page can render, not a crash.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 */
export async function listTeam({ cookies }) {
  let usersResp, teamsResp;
  try {
    [usersResp, teamsResp] = await Promise.all([
      apiRequest('/users/', {}, { cookies }),
      apiRequest('/teams/', {}, { cookies })
    ]);
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) return { forbidden: true };
    throw err;
  }

  const viewerId = viewerUserId(cookies);
  const teamRows = teamsResp?.teams ?? [];

  // profile id -> the names of the teams it belongs to, from the teams payload.
  /** @type {Record<string, string[]>} */
  const teamsByProfile = {};
  for (const t of teamRows) {
    for (const u of t.users ?? []) {
      (teamsByProfile[u.id] ??= []).push(t.name);
    }
  }

  const active = (usersResp?.active_users?.active_users ?? []).map((/** @type {any} */ p) =>
    toMember(p, teamsByProfile, viewerId)
  );
  const inactive = (usersResp?.inactive_users?.inactive_users ?? []).map((/** @type {any} */ p) =>
    toMember(p, teamsByProfile, viewerId)
  );

  const teams = teamRows.map((/** @type {any} */ t) => ({
    id: t.id,
    name: t.name,
    description: t.description || '',
    member_count: (t.users ?? []).length
  }));

  const admins = active.filter((/** @type {any} */ m) => m.role === 'ADMIN');

  return {
    forbidden: false,
    active,
    inactive,
    teams,
    roles: ROLES,
    totals: {
      count: active.length,
      admins: admins.length,
      never_signed_in: active.filter((/** @type {any} */ m) => !m.last_login).length,
      deactivated: inactive.length,
      // A live token outliving the account that owns it, the number worth acting on.
      tokens_on_deactivated: inactive.reduce(
        (/** @type {number} */ a, /** @type {any} */ m) => a + m.active_token_count,
        0
      )
    },
    // Whether the org would have a second admin left if one were removed. The
    // page mirrors "keep at least one admin" as a hint; the server enforces it.
    last_admin_id: admins.length === 1 ? admins[0].user_id : null
  };
}

/**
 * Invite someone: `POST /api/users/`. Admin-only server-side. Role is chosen
 * at invite time. That is legitimate on this path (an admin choosing a new
 * member's role), unlike a member setting their own.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {{ email: string, role: string }} body
 */
export function inviteUser({ cookies }, body) {
  return apiRequest('/users/', { method: 'POST', body }, { cookies });
}

/**
 * Change a person's role: `PATCH /api/user/<userId>/`. The server allows this
 * only for an admin acting on someone other than themselves, so the page never
 * offers it on your own row or when it would strip the last admin.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} userId  the User id, not the profile id
 * @param {string} role
 */
export function setRole({ cookies }, userId, role) {
  return apiRequest(`/user/${userId}/`, { method: 'PATCH', body: { role } }, { cookies });
}

/**
 * Activate or deactivate: `POST /api/user/<userId>/status/`. The server refuses
 * to deactivate the last active admin.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} userId
 * @param {'Active' | 'Inactive'} status
 */
export function setStatus({ cookies }, userId, status) {
  return apiRequest(`/user/${userId}/status/`, { method: 'POST', body: { status } }, { cookies });
}
