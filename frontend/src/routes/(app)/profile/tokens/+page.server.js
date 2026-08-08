import { fail } from '@sveltejs/kit';
import { listMyTokens, createToken, revokeMyToken } from '$lib/server/v2/tokens.js';
import { readableError } from '$lib/server/v2/form-errors.js';
import { expiryFromChoice, scopesFromChoice } from '$lib/v2/token-rules.js';

/**
 * Your own API tokens: issue one, see what you have, revoke one.
 *
 * Deliberately NOT the admin oversight page under /settings/api-tokens. That
 * one reads `/api/org/tokens/` and 403s a member, which is why a member had no
 * way to issue themselves a token in either client even though
 * `/api/profile/tokens/` has always been open to them. This page reads and
 * writes only the self-scoped endpoints, which filter on
 * `profile=request.profile` server-side.
 *
 * No role check here, and none is wanted: every member may hold their own
 * token, and the backend already answers only their rows. Adding a gate would
 * invent a rule the API does not have.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return await listMyTokens({ cookies });
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Issue one for yourself. The server sets the owner from the JWT, so there
   * is no "create on behalf of" to guard against. The raw value comes back
   * once, is rendered once, and is never logged or stored.
   */
  create: async ({ cookies, request }) => {
    const form = await request.formData();
    const name = form.get('name')?.toString().trim();
    const expires_at = expiryFromChoice(form.get('expiry')?.toString());
    const scopes = scopesFromChoice(form.get('access')?.toString());
    if (!name) return fail(400, { create: { error: 'Give the token a name.' } });

    try {
      const res = await createToken({ cookies }, { name, expires_at, scopes });
      return {
        created: {
          name: res.name ?? name,
          token_prefix: res.token_prefix,
          token: res.token,
          expires_at: res.expires_at ?? null
        }
      };
    } catch (/** @type {any} */ err) {
      return fail(400, {
        create: { error: readableError(err, 'Could not create that token.') }
      });
    }
  },

  /**
   * Revoke one of your own. A 404 means the id is not yours, which the
   * self-scoped endpoint answers rather than revealing that it exists.
   */
  revoke: async ({ cookies, request }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'Which token?' });
    try {
      await revokeMyToken({ cookies }, id);
    } catch (/** @type {any} */ err) {
      if (err?.status === 404) {
        return fail(404, { error: 'That token is not one of yours.' });
      }
      return fail(400, { error: readableError(err, 'Could not revoke that token.') });
    }
    return { revoked: id };
  }
};
