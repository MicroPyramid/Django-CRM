import { listDocuments } from '$lib/server/v2/documents.js';

/**
 * The documents list.
 *
 * Read-only here: the backend has already scoped the rows to the org and, for a
 * non-admin, to the documents they may open (`_visible_to`), so this just
 * flattens the two paginated envelopes into one list. Uploading, editing and
 * deleting live on their own routes (`/new`, `/[id]/edit`) so the destructive
 * paths are deliberate, never a mis-click in a table.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  return await listDocuments(event);
}
