/**
 * Organization settings — the eleventh v2 module wired to the real API.
 *
 * Lives under `$lib/server` like the ten before it: the JWT cookie stays
 * server-side and org is a token claim, never a parameter. `GET/PATCH
 * /api/org/settings/` always acts on `request.profile.org` — there is no org id
 * in the URL, so a caller can only ever read or edit their OWN org. That is the
 * tenant barrier; there is nothing to scope by hand.
 *
 * WHAT THE SETTINGS PAGE READS, AND WHAT IT CANNOT
 * The company profile (printed on invoices), locale defaults, and two org-wide
 * case-handling switches. It never touches the org API key: that credential
 * authenticates as the org's first admin, so it is excluded from
 * `OrgSettingsSerializer` entirely and rotated only through `OrgApiKeyView`.
 * `is_active` (the org kill switch) is likewise not editable here.
 *
 * THE BACKEND GAP THIS WIRING CLOSED
 * `csat_enabled` and `auto_close_children_on_parent_close` are real `Org`
 * columns that had no write path through ANY serializer — the settings page
 * displayed them but nothing could change them. They are now in the writable
 * allow-list. (A second, older `OrgUpdateView` at `/api/org/<id>/` writes only
 * `name` and silently drops every other field; this page deliberately uses
 * `/api/org/settings/`, the serializer-based endpoint, and not that one.)
 *
 * ADMIN-ONLY EDIT, MEMBER-VISIBLE READ
 * GET is open to any member — the company profile is not a secret, and members
 * legitimately see their org's address and currency. PATCH is admin-only,
 * enforced by the backend (403 for a non-admin). `can_edit` here is a display
 * hint decoded from the JWT `role` claim; the server is what actually refuses.
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * The fields the edit form may submit. An allow-list, so a hand-crafted POST
 * cannot smuggle in a field the page never offered — and so `org`, `api_key`,
 * `is_active`, `id` and the read-only header fields are never sent from the
 * client even if someone adds them to the request body.
 */
export const EDITABLE_FIELDS = [
  'name',
  'company_name',
  'address_line',
  'city',
  'state',
  'postcode',
  'country',
  'phone',
  'email',
  'website',
  'tax_id',
  'default_currency',
  'default_country'
];

/**
 * The two org-wide behaviour switches. Kept separate from EDITABLE_FIELDS
 * because they are booleans: the form always submits them as the strings
 * 'true'/'false', and the action coerces them, so "unchecked" is a real value
 * and not the "field absent → leave alone" convention the text fields use.
 */
export const BOOLEAN_FIELDS = ['csat_enabled', 'auto_close_children_on_parent_close'];

/**
 * The signed-in user's role, read from the `role` claim of the access token.
 *
 * A display hint only — it decides whether the page shows the "Edit details"
 * affordance. It is never the authorization decision: `PATCH /api/org/settings/`
 * re-derives the role from the same token server-side and is the thing that
 * actually refuses a non-admin. Decoded, not verified; verifying our own
 * freshly-read cookie would buy nothing.
 *
 * @param {import('@sveltejs/kit').Cookies} cookies
 * @returns {string | null}
 */
export function viewerRole(cookies) {
  const token = cookies.get('jwt_access');
  if (!token) return null;
  try {
    const payload = token.split('.')[1];
    const json = Buffer.from(payload, 'base64url').toString('utf-8');
    return JSON.parse(json).role ?? null;
  } catch {
    return null;
  }
}

/**
 * The org as the settings page reads it. `/api/org/settings/` returns the bare
 * serialized object (no envelope), so this passes it straight through and adds
 * `can_edit` — the admin display hint.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 */
export async function getOrgSettings({ cookies }) {
  const org = await apiRequest('/org/settings/', {}, { cookies });
  return { org, can_edit: viewerRole(cookies) === 'ADMIN' };
}

/**
 * Save org settings: `PATCH /api/org/settings/`. Admin-only and org-scoped
 * server-side. Partial — only the fields in `body` are touched.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {Record<string, unknown>} body
 */
export function updateOrgSettings({ cookies }, body) {
  return apiRequest('/org/settings/', { method: 'PATCH', body }, { cookies });
}

/**
 * Vertical-pack label overrides for this org — read via the same
 * `/api/org/settings/` endpoint the settings page uses, not a second
 * endpoint. `terminology` and `vertical` are `read_only_fields` on
 * `OrgSettingsSerializer`: the pack applier writes them server-side, so
 * there is nothing to validate or scope on the way out.
 *
 * Called from the `(app)` shell load on *every* page (see
 * `routes/(app)/+layout.server.js`), not just the settings page, so it must
 * never be the reason the shell fails to render — callers are expected to
 * fold a rejection into an empty/undefined result the same way the shell's
 * badge-count fetches already do, rather than let it propagate.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ terminology?: Record<string, string>, vertical?: string }>}
 */
export async function getOrgTerminology({ cookies }) {
  const org = await apiRequest('/org/settings/', {}, { cookies });
  return { terminology: org?.terminology, vertical: org?.vertical };
}
