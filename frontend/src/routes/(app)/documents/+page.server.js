import { listDocuments, FILTER_FIELDS } from '$lib/server/v2/documents.js';
import { readFilters, buildFilterQuery } from '$lib/server/v2/filter-params.js';

/**
 * The documents list.
 *
 * Read-only here: the backend has already scoped the rows to the org and, for a
 * non-admin, to the documents they may open (`_visible_to`), so this just
 * flattens the two paginated envelopes into one list. Uploading, editing and
 * deleting live on their own routes (`/new`, `/[id]/edit`) so the destructive
 * paths are deliberate, never a mis-click in a table.
 *
 * `status` is the only filter this endpoint honours; see the note on
 * `FILTER_FIELDS` in `documents.js`. The old page fetched every document and
 * filtered archived ones out client-side, which is wrong once pagination is
 * in play: it returns fewer rows than the page size and understates the count.
 * The API narrows the set now.
 *
 * Active-only is the default, applied here rather than by an empty-params
 * preset, which is the same shape `/contacts` uses for `inactive` and
 * `/tasks` uses for `all`. Archiving a document is how you get it out of the
 * way, so a default that showed archived ones back alongside the live ones
 * would undo the only thing archiving does. `?archived=1` opts in, and an
 * explicit `?status=` from the Status field beats the default outright, the
 * same rule the tasks queue follows.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, url }) {
  const filters = readFilters(url, 'documents');
  const params = buildFilterQuery(FILTER_FIELDS, filters);
  const includeArchived = url.searchParams.get('archived') === '1';
  if (!includeArchived && !params.has('status')) params.set('status', 'active');
  return await listDocuments({ cookies }, params);
}
