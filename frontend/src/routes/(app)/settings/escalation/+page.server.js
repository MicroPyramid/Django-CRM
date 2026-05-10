import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const PRIORITIES = ['Low', 'Normal', 'High', 'Urgent'];
const ACTIONS = ['notify', 'reassign', 'notify_and_reassign'];

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, locals }) {
  const profile = locals.profile;
  if (profile?.role !== 'ADMIN' && !profile?.is_organization_admin) {
    throw error(403, 'Only admins can manage escalation policies');
  }

  try {
    const [policiesRes, usersRes, teamsRes] = await Promise.all([
      apiRequest('/cases/escalation-policies/', {}, { cookies, org: locals?.org }),
      apiRequest('/users/', {}, { cookies, org: locals?.org }).catch(() => ({})),
      apiRequest('/teams/', {}, { cookies, org: locals?.org }).catch(() => ({}))
    ]);

    return {
      priorities: PRIORITIES,
      actions: ACTIONS,
      policies: policiesRes.policies || [],
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
    console.error('Failed to load escalation policies:', err);
    throw error(500, 'Failed to load escalation policies');
  }
}

function buildBody(formData, { includePriority }) {
  const body = {
    first_response_action: String(formData.get('first_response_action') || 'notify'),
    resolution_action: String(formData.get('resolution_action') || 'notify'),
    is_active: formData.get('is_active') !== 'false'
  };
  if (includePriority) {
    body.priority = String(formData.get('priority') || '');
  }
  const frt = String(formData.get('first_response_target_id') || '');
  const rt = String(formData.get('resolution_target_id') || '');
  const nt = String(formData.get('notify_team_id') || '');
  body.first_response_target_id = frt || null;
  body.resolution_target_id = rt || null;
  body.notify_team_id = nt || null;
  return body;
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const body = buildBody(formData, { includePriority: true });
    try {
      const created = await apiRequest(
        '/cases/escalation-policies/',
        { method: 'POST', body },
        { cookies, org: locals?.org }
      );
      return { success: true, created };
    } catch (err) {
      console.error('Failed to create escalation policy:', err);
      return fail(400, { error: err?.message || 'Failed to create escalation policy' });
    }
  },

  update: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = String(formData.get('id') || '');
    if (!id) return fail(400, { error: 'Missing policy id' });
    // priority is the natural key — frozen post-create. The API strips it,
    // but we strip client-side too so a stale form can't bump it.
    const body = buildBody(formData, { includePriority: false });
    try {
      const updated = await apiRequest(
        `/cases/escalation-policies/${id}/`,
        { method: 'PUT', body },
        { cookies, org: locals?.org }
      );
      return { success: true, updated };
    } catch (err) {
      console.error('Failed to update escalation policy:', err);
      return fail(400, { error: err?.message || 'Failed to update escalation policy' });
    }
  },

  delete: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = String(formData.get('id') || '');
    if (!id) return fail(400, { error: 'Missing policy id' });
    try {
      await apiRequest(
        `/cases/escalation-policies/${id}/`,
        { method: 'DELETE' },
        { cookies, org: locals?.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Failed to delete escalation policy:', err);
      return fail(400, { error: err?.message || 'Failed to delete escalation policy' });
    }
  }
};
