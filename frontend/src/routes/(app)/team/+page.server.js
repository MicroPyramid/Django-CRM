import { fail } from '@sveltejs/kit';
import { listTeam, inviteUser, setRole, setStatus, ROLES } from '$lib/server/v2/team.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * Team and access.
 *
 * Server load, so the JWT cookie stays server-side. The list, the totals and
 * the per-person token counts all arrive from the real org; a non-admin gets
 * `forbidden` back rather than a broken page, because the underlying endpoints
 * are admin-only.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return await listTeam({ cookies });
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Invite a new member: email + role. The server is the boundary. It gates
   * this to admins, rejects a duplicate within the org with a 400, and reuses
   * an account that already exists elsewhere instead of erroring.
   */
  invite: async ({ cookies, request }) => {
    const form = await request.formData();
    const email = form.get('email')?.toString().trim();
    const role = form.get('role')?.toString() || 'USER';
    if (!email) return fail(400, { invite: { error: 'Enter an email address.' } });
    if (!ROLES.includes(role)) return fail(400, { invite: { error: 'Pick a valid role.' } });

    try {
      await inviteUser({ cookies }, { email, role });
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        invite: {
          error:
            err?.status === 403
              ? 'Only an admin can invite people.'
              : readableError(err, 'Could not send that invite.')
        }
      });
    }
    return { invited: email };
  },

  /**
   * Change someone's role. The page only shows this control for another
   * person's row and never for the last admin, mirroring the server's rules,
   * but the server is what enforces them: a member cannot promote themselves
   * and nobody can change their own role here.
   */
  setRole: async ({ cookies, request }) => {
    const form = await request.formData();
    const userId = form.get('userId')?.toString();
    const role = form.get('role')?.toString();
    if (!userId || !role || !ROLES.includes(role)) {
      return fail(400, { error: 'Which person, and to what role?' });
    }
    try {
      await setRole({ cookies }, userId, role);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error:
          err?.status === 403
            ? 'That is not yours to change.'
            : readableError(err, 'Could not change that role.')
      });
    }
    return { roleChanged: userId };
  },

  /**
   * Activate or deactivate a member. The server refuses to deactivate the last
   * active admin (a 400), so the org can never be stranded without one.
   */
  setStatus: async ({ cookies, request }) => {
    const form = await request.formData();
    const userId = form.get('userId')?.toString();
    const status = form.get('status')?.toString();
    if (!userId || (status !== 'Active' && status !== 'Inactive')) {
      return fail(400, { error: 'Which person, and active or not?' });
    }
    try {
      await setStatus({ cookies }, userId, status);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error:
          err?.status === 403
            ? 'Only an admin can change who is active.'
            : readableError(err, 'Could not change that status.')
      });
    }
    return { statusChanged: userId };
  }
};
