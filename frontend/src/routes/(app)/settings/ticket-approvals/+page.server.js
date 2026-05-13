import { error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/**
 * Admin-only loader for the approval-rules CRUD page.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, locals }) {
  const profile = locals.profile;
  if (profile?.role !== 'ADMIN' && !profile?.is_organization_admin) {
    throw error(403, 'Only admins can manage approval rules');
  }

  try {
    const [rulesRes, usersRes, teamsRes] = await Promise.all([
      apiRequest(
        '/cases/approval-rules/',
        {},
        { cookies, org: locals?.org }
      ),
      apiRequest('/users/', {}, { cookies, org: locals?.org }).catch(() => ({})),
      apiRequest('/teams/', {}, { cookies, org: locals?.org }).catch(() => ({}))
    ]);

    return {
      rules: rulesRes.rules || [],
      profiles: (usersRes.active_users?.active_users || []).map((u) => ({
        id: u.id,
        name:
          u.user_details?.first_name && u.user_details?.last_name
            ? `${u.user_details.first_name} ${u.user_details.last_name}`
            : u.user_details?.email || u.email
      })),
      teams: (teamsRes.teams || teamsRes.results || []).map((t) => ({
        id: t.id,
        name: t.name
      }))
    };
  } catch (err) {
    console.error('Failed to load approval rules:', err);
    throw error(500, 'Failed to load approval rules');
  }
}
