import { listBoard, listDeals } from '$lib/server/v2/deals.js';

/**
 * The list and the board are two different queries, not two renderings of one
 * result: the table is paginated and the board is grouped and capped per
 * column. Only the one being shown is fetched.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  const view = event.url.searchParams.get('view') === 'board' ? 'board' : 'list';

  // Forward only the filters the API implements. An unknown key silently
  // doing nothing is how a filter bar starts lying.
  const params = new URLSearchParams();
  for (const key of ['search', 'account', 'assigned_to', 'tags', 'limit']) {
    const value = event.url.searchParams.get(key);
    if (value) params.set(key, value);
  }

  if (view === 'board') {
    const { lanes } = await listBoard(event, params);
    // The header totals stay the table's: they describe the whole open
    // pipeline, which is the same claim on either view.
    const { totals } = await listDeals(event, new URLSearchParams(params));
    return { view, lanes, totals, deals: [] };
  }

  const { results, totals } = await listDeals(event, params);
  return { view, deals: results, totals, lanes: [] };
}
