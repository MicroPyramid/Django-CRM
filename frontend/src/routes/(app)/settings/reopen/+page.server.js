import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, locals }) {
  const profile = locals.profile;
  if (profile?.role !== 'ADMIN' && !profile?.is_organization_admin) {
    throw error(403, 'Only admins can manage the reopen policy');
  }

  try {
    const policy = await apiRequest(
      '/cases/reopen-policy/',
      {},
      { cookies, org: locals?.org }
    );
    return { policy };
  } catch (err) {
    console.error('Failed to load reopen policy:', err);
    throw error(500, 'Failed to load reopen policy');
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  update: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const days = Number(formData.get('reopen_window_days'));
    const data = {
      is_enabled: formData.get('is_enabled') === 'true',
      reopen_window_days: Number.isFinite(days) ? days : 7,
      reopen_to_status: formData.get('reopen_to_status') || 'Pending',
      notify_assigned: formData.get('notify_assigned') === 'true'
    };

    try {
      const policy = await apiRequest(
        '/cases/reopen-policy/',
        { method: 'PUT', body: data },
        { cookies, org: locals?.org }
      );
      return { success: true, policy };
    } catch (err) {
      console.error('Failed to update reopen policy:', err);
      return fail(400, { error: err?.message || 'Failed to update policy' });
    }
  }
};
