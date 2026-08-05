import { fail } from '@sveltejs/kit';
import { listOrgTokens, createToken, revokeToken } from '$lib/server/v2/tokens.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * API tokens (admin oversight).
 *
 * Server load, so the JWT cookie stays server-side and the raw token value.
 * Returned once on create, is handled here, never fetched from the browser.
 * The list is admin-only; a non-admin gets `forbidden` back, not a broken page.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return await listOrgTokens({ cookies });
}

/**
 * Turn a coarse expiry choice into an ISO datetime the API will accept, or null
 * for "never". Kept coarse on purpose. A date picker is more precision than a
 * token expiry needs, and "never" is named rather than left as an empty field
 * so the riskiest choice is a deliberate one.
 *
 * @param {string | undefined} choice
 * @returns {string | null}
 */
function expiryFromChoice(choice) {
  const days = { 30: 30, 90: 90, 365: 365 }[choice ?? ''];
  if (!days) return null;
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString();
}

/**
 * Turn the access choice into the scope list the API enforces.
 *
 * `common/scopes.py` reads `<resource>:<action>` and treats an empty list as
 * unrestricted, which is what every token issued before enforcement carries.
 * The backend understands per-resource scopes too; this form deliberately
 * offers only the two choices that are worth a radio button, because a picker
 * listing thirty resources is a worse question than "may it change anything?".
 * A caller who wants `leads:read` can create the token through the API.
 *
 * @param {string | undefined} choice
 * @returns {string[]}
 */
function scopesFromChoice(choice) {
  return choice === 'read' ? ['*:read'] : [];
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Create a token for the signed-in admin. The server owns the owner (from the
   * JWT) and returns the raw value once. The page shows it a single time and
   * it is unrecoverable after. We never log it.
   */
  create: async ({ cookies, request }) => {
    const form = await request.formData();
    const name = form.get('name')?.toString().trim();
    const expires_at = expiryFromChoice(form.get('expiry')?.toString());
    const scopes = scopesFromChoice(form.get('access')?.toString());
    if (!name) return fail(400, { create: { error: 'Give the token a name.' } });

    try {
      const res = await createToken({ cookies }, { name, expires_at, scopes });
      // Shown once. `token` is the raw value; the list will only ever have the
      // prefix after this response is gone.
      return {
        created: {
          name: res.name ?? name,
          token_prefix: res.token_prefix,
          token: res.token,
          expires_at: res.expires_at ?? null
        }
      };
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        create: {
          error:
            err?.status === 403
              ? 'You do not have permission to create tokens here.'
              : readableError(err, 'Could not create that token.')
        }
      });
    }
  },

  /** Revoke one token by id. Admin + org-scoped server-side. */
  revoke: async ({ cookies, request }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'Which token?' });
    try {
      await revokeToken({ cookies }, id);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error:
          err?.status === 403
            ? 'Only an admin can revoke tokens.'
            : readableError(err, 'Could not revoke that token.')
      });
    }
    return { revoked: id };
  },

  /**
   * Revoke every live token on a deactivated owner in one go. The id list is
   * re-derived from the server, not read from the form. The page cannot ask us
   * to revoke an arbitrary set, only the orphaned rows the API itself reports.
   */
  revokeOrphaned: async ({ cookies }) => {
    let ids;
    try {
      ({ orphaned_ids: ids } = await listOrgTokens({ cookies }));
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error:
          err?.status === 403
            ? 'Only an admin can revoke tokens.'
            : readableError(err, 'Could not load tokens to revoke.')
      });
    }
    if (!ids?.length) return { revokedOrphaned: 0 };

    let done = 0;
    for (const id of ids) {
      try {
        await revokeToken({ cookies }, id);
        done += 1;
      } catch {
        // Best effort: one failure should not strand the rest. The reload
        // reflects whatever actually got revoked.
      }
    }
    return { revokedOrphaned: done };
  }
};
