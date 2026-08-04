/**
 * Tags: the wiring behind `/settings/tags`.
 *
 * Server-only. Reads `GET /tags/?include_archived=true`, which returns every
 * tag in the org (active and archived. The page shows the "Off" ones so an
 * admin can see what's been retired), each carrying a `usage` block
 * `{ accounts, leads, opportunities, cases }` and a `totals` summary
 * `{ count, active, unused }` for the stat cards. Both are computed server-side
 * (the usage counts are org-scoped subqueries, not a client tally over rows).
 *
 * "New tag" is wired: `createTag` below posts the name and the page's action
 * calls it. The duplicate-merge banner is still deferred; its "Merge" button
 * has no backing endpoint yet, see the comment on it in `+page.svelte`.
 *
 * CREATE IS ADMIN-ONLY, LIST IS NOT
 * `/settings` is deliberately member-readable (see the comment in
 * `$lib/v2/components/Sidebar.svelte`), and `TagsListView.get` has no role
 * check, so every member reads the full tag list. `TagsListView.post`
 * (`backend/common/views/tags_views.py:143-149`) does gate: it 403s anyone
 * whose `profile.role` is not `ADMIN`. `can_edit` below mirrors that split so
 * the page can hide "New tag" for a member instead of letting them submit a
 * form the backend was always going to refuse. It is a display hint only,
 * decoded from the JWT and never verified; the backend re-derives the role
 * from the same token and is the check that actually matters. `viewerRole` is
 * imported from `organization.js`, where it is exported for exactly this
 * reuse, rather than redefined here: a role check is exactly the kind of
 * thing that should not exist in one more private copy per module.
 * `goals.js` and `products.js` still carry their own pre-existing private
 * copies of the same decode; not touched here, worth consolidating later.
 */
import { apiRequest } from '$lib/api-helpers.js';
import { viewerRole } from './organization.js';

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ tags: any[], totals: any, can_edit: boolean }>}
 */
export async function getTags({ cookies }) {
  const resp = await apiRequest('/tags/?include_archived=true', {}, { cookies });
  return {
    tags: resp.tags ?? [],
    totals: resp.totals ?? { count: 0, active: 0, unused: 0 },
    can_edit: viewerRole(cookies) === 'ADMIN'
  };
}

/**
 * Create a tag.
 *
 * Only `name` is sent. `org` comes from the JWT on the backend, and `usage`
 * and `totals` are computed, never submitted. The empty-name guard is a fast
 * fail for an obvious mistake, not a security control: `TagsListView.post`
 * (`backend/common/views/tags_views.py`) runs its own `if not name:` check
 * after stripping the param, and that is the real authority. `TagsSerializer`
 * is not in this path at all; the view only uses it to shape the response.
 *
 * `TagsListView.post` wraps its result in an envelope,
 * `{ error, message, tag }`, on both the create branch and the reactivation
 * branch (an archived tag with the same slug is revived instead of
 * duplicated). This unwraps to `.tag` deliberately rather than just fixing
 * the doc comment: a function named `createTag` that resolves to the
 * envelope is a trap the next caller will fall into blind, exactly like
 * `createLead` does today, `LeadListView.post` returns no id at all, so
 * `leads/new/+page.server.js`'s `created?.id` is always undefined and every
 * lead creation redirects to `/leads` instead of the new record. Not every
 * create endpoint in this codebase gives you a record back; the seven
 * settings pages that copy this function will want to link to or highlight
 * the tag they just made, so this one hands back the real thing.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {{ name?: string, [key: string]: any }} values callers may pass extra
 *   keys (a hostile `org`, say); the index signature lets TypeScript accept
 *   the object literal without widening what this function actually reads,
 *   which stays just `name`.
 * @returns {Promise<any>} the created (or reactivated) tag record: `{ id, name,
 *   slug, color, description, is_active, created_at }`.
 */
export async function createTag({ cookies }, values) {
  const name = (values.name ?? '').trim();
  if (!name) throw new Error('A tag needs a name.');

  const resp = await apiRequest('/tags/', { method: 'POST', body: { name } }, { cookies });
  return resp.tag ?? resp;
}
