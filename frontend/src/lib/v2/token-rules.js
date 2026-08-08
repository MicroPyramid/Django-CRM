/**
 * What an oversight row says about one token, and what the create form sends.
 *
 * Its own module rather than inline in `+page.svelte` and `+page.server.js`,
 * because the harness cannot import a `.svelte` file and every rule here has a
 * right answer that lives in the backend: `OrgAccessTokenListView` for the
 * staleness rule, `common/scopes.py` for the grammar, and
 * `PersonalAccessTokenCreateSerializer` for what a create body may carry. The
 * routing, escalation and business-hours routes do the same with `rotation.js`,
 * `outcome.js` and `week.js`.
 *
 * `mobile/lib/data/models/access_token.dart` carries the same rules.
 *
 * In `$lib` rather than beside one route because two pages now ask these
 * questions: the admin oversight list under /settings/api-tokens, and the
 * self-service list under /profile/tokens. Every function here is pure, so it
 * is safe on either side of the network.
 */

import { daysSince } from '$lib/v2/format.js';

/**
 * When this token last did anything, falling back to when it was issued.
 *
 * **`last_used_at` being null does not mean "long ago".** It is null both for a
 * token issued three years ago and for one issued a minute ago, and the
 * "Unused 90+ days" figure used to count on null alone, so creating a token
 * through this page put the token you had just made into that count on the very
 * next reload. `OrgAccessTokenListView` now measures the same fallback, and this
 * is the row-level half of it: the card and the row have to agree about which
 * rows they are counting.
 *
 * @param {{ last_used_at?: string | null, created_at?: string | null }} token
 * @returns {string | null}
 */
export function lastActivityAt(token) {
  return token?.last_used_at ?? token?.created_at ?? null;
}

/**
 * The clay line under "Last used", or null when there is nothing to say.
 *
 * Only for a live token: a revoked or expired one is already not a credential,
 * and flagging it as neglected as well would bury the rows worth acting on.
 *
 * @param {any} token
 * @param {Date} [now]
 * @returns {string | null}
 */
export function staleness(token, now = new Date()) {
  if (!token?.is_live) return null;
  const days = daysSince(lastActivityAt(token), now);
  if (days === null || days <= 90) return null;
  return token.last_used_at ? `unused for ${days} days` : `never used, issued ${days} days ago`;
}

/**
 * Revoked and expired are different reasons for the same outcome, so they read
 * differently and tone the same. Neither is a live credential.
 *
 * @param {any} token
 * @returns {{ label: string, tone: 'ink'|'slate'|'clay'|'rust'|'moss' }}
 */
export function tokenStatus(token) {
  if (token?.revoked_at) return { label: 'Revoked', tone: 'slate' };
  if (!token?.is_live) return { label: 'Expired', tone: 'slate' };
  return { label: 'Live', tone: 'moss' };
}

/**
 * What this token may do, in the words the table uses.
 *
 * An empty scope list means unrestricted (see the `common.scopes` docstring for
 * why), which is what every token issued before enforcement carries, so those
 * rows say what they really are rather than being drawn as limited.
 *
 * `ownerLabel` exists because the self-service list has no `owner` block on
 * its rows (the endpoint is already scoped to you), and "Everything its owner
 * can" is a strange thing to read on a page about your own tokens.
 *
 * @param {any} token
 * @param {{ ownerLabel?: string }} [options]
 * @returns {string}
 */
export function scopeSummary(token, options = {}) {
  const scopes = token?.scopes ?? [];
  if (scopes.length === 0) {
    if (options.ownerLabel) return `Everything ${options.ownerLabel} can`;
    const first = (token?.owner?.name ?? '').split(' ')[0];
    return first ? `Everything ${first} can` : 'Everything its owner can';
  }
  if (scopes.every((/** @type {string} */ s) => s.endsWith(':read'))) return 'Read only';
  return scopes.join(', ');
}

/**
 * The coarse expiry choices the form offers, in the order it offers them.
 *
 * Coarse on purpose: a date picker is more precision than a token expiry needs,
 * and "never" is a named option rather than an empty field so the riskiest
 * choice is a deliberate one.
 */
export const EXPIRY_CHOICES = [
  { value: '90', label: 'In 90 days', days: 90 },
  { value: '30', label: 'In 30 days', days: 30 },
  { value: '365', label: 'In 1 year', days: 365 },
  { value: 'never', label: 'Never', days: null }
];

/**
 * Turn a coarse expiry choice into an ISO datetime the API will accept, or null
 * for "never". Anything unrecognised is "never" rather than an error, matching
 * the serializer, which treats an absent `expires_at` the same way.
 *
 * @param {string | undefined | null} choice
 * @param {Date} [now]
 * @returns {string | null}
 */
export function expiryFromChoice(choice, now = new Date()) {
  const days = EXPIRY_CHOICES.find((c) => c.value === choice)?.days ?? null;
  if (!days) return null;
  const d = new Date(now.getTime());
  d.setDate(d.getDate() + days);
  return d.toISOString();
}

/**
 * Turn the access choice into the scope list the API enforces.
 *
 * The backend understands per-resource scopes (`leads:read`), but this form
 * deliberately offers only the two choices worth a radio button, because a
 * picker listing thirty resources is a worse question than "may it change
 * anything?". A caller who wants finer scopes creates the token through the API.
 *
 * @param {string | undefined | null} choice
 * @returns {string[]}
 */
export function scopesFromChoice(choice) {
  return choice === 'read' ? ['*:read'] : [];
}
