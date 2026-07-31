import { listTickets, OPEN_STATUSES } from '$lib/server/v2/tickets.js';

/**
 * Only filters the API actually applies are forwarded. A parameter that
 * changes the URL and nothing else teaches people the filter bar is decorative.
 *
 * The queue defaults to open tickets, which is what the mock page claimed in a
 * chip it could not act on. `status` is repeatable and the API switches to
 * `status__in` when more than one arrives, so "open" is three values rather
 * than a fourth definition of the word.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, url }) {
  const params = new URLSearchParams();
  for (const key of ['search', 'priority', 'case_type', 'account', 'assigned_to', 'limit']) {
    const value = url.searchParams.get(key);
    if (value) params.set(key, value);
  }

  const status = url.searchParams.get('status') ?? '';
  const showAll = url.searchParams.get('all') === '1';
  if (status) {
    params.set('status', status);
  } else if (!showAll) {
    for (const open of OPEN_STATUSES) params.append('status', open);
  }

  const { results, totals } = await listTickets({ cookies }, params);
  return {
    tickets: results,
    totals,
    showAll,
    status,
    search: params.get('search') ?? '',
    priority: params.get('priority') ?? ''
  };
}
