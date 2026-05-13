import { error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/**
 * Approver inbox loader. Defaults to ``state=pending`` and (when the caller
 * doesn't override) ``mine=true``, so an approver lands directly on the
 * actionable rows.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ url, cookies, locals }) {
  if (!locals.org) throw error(401, 'Organization context required');

  const tab = url.searchParams.get('tab') || 'mine'; // 'mine' | 'all'
  const state = url.searchParams.get('state') || 'pending';

  const qs = new URLSearchParams({ state });
  if (tab === 'mine') qs.set('mine', 'true');

  try {
    const data = await apiRequest(
      `/cases/approvals/?${qs.toString()}`,
      {},
      { cookies, org: locals.org }
    );
    return {
      approvals: data?.approvals || [],
      tab,
      stateFilter: state,
      currentProfileId: /** @type {any} */ (locals).profile?.id || null,
      isAdmin: /** @type {any} */ (locals).profile?.role === 'ADMIN'
    };
  } catch (err) {
    console.error('Approval inbox load failed:', err);
    return {
      approvals: [],
      tab,
      stateFilter: state,
      currentProfileId: /** @type {any} */ (locals).profile?.id || null,
      isAdmin: /** @type {any} */ (locals).profile?.role === 'ADMIN',
      loadError: err?.message || 'Could not load approvals'
    };
  }
}
