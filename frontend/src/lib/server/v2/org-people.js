/**
 * The in-org people and teams every picker needs.
 *
 * Server-only. `GET /users/get-teams-and-users/` filters profiles to
 * `is_active=True, org=request.profile.org` and teams to the same org, so a
 * picker built from this can only ever offer an active, in-org target.
 *
 * That is UX, not the boundary. Every consumer's own write path re-checks the
 * id against the caller's org, and they do it in three different ways, so do
 * not read one mechanism into all of them: the four `cases` settings
 * serializers scope their relational querysets to the caller's org in
 * `__init__` and reject a foreign id with a 400; `SalesGoalCreateSerializer`
 * raises a 400 from `validate_assigned_to` / `validate_team`; the document
 * views filter `Profile.objects.filter(id__in=..., org=..., is_active=True)`
 * inline and silently drop a foreign id rather than failing. All three close
 * the hole. None of them depend on what this list offered.
 *
 * This exists because four modules had grown their own private copy of the
 * same fetch. `documents.js` and `goals.js` were byte-identical in behaviour
 * and now import this. `deals.js` and `leads.js` keep theirs: they label a
 * person by email rather than name, and changing what their owner select
 * displays is not a refactor.
 *
 * A failed fetch resolves to empty lists rather than throwing. The pickers
 * are one part of a settings page, and taking the whole page down to a 500
 * because an optional list did not load is worse than rendering it with
 * nothing to choose.
 */
import { apiRequest } from '$lib/api-helpers.js';

/** A profile as the pickers label it. */
function personName(profile) {
  const d = profile?.user_details ?? {};
  return d.name || d.email || 'Unnamed';
}

/**
 * @param {import('@sveltejs/kit').Cookies} cookies
 * @returns {Promise<{ people: { id: string, name: string }[], teams: { id: string, name: string }[] }>}
 */
export async function getOrgPeopleAndTeams(cookies) {
  try {
    const resp = await apiRequest('/users/get-teams-and-users/', {}, { cookies });
    return {
      people: (resp?.profiles ?? []).map((/** @type {any} */ p) => ({
        id: p.id,
        name: personName(p)
      })),
      teams: (resp?.teams ?? []).map((/** @type {any} */ t) => ({ id: t.id, name: t.name }))
    };
  } catch {
    return { people: [], teams: [] };
  }
}
