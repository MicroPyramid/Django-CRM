import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const PRIORITIES = ['Low', 'Normal', 'High', 'Urgent'];
const CASE_TYPES = ['', 'Question', 'Incident', 'Problem'];

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, locals, url }) {
  const profile = locals.profile;
  if (profile?.role !== 'ADMIN' && !profile?.is_organization_admin) {
    throw error(403, 'Only admins can manage inbound mailboxes');
  }

  try {
    const [mailboxesRes, usersRes] = await Promise.all([
      apiRequest('/cases/mailboxes/', {}, { cookies, org: locals?.org }),
      apiRequest('/users/', {}, { cookies, org: locals?.org }).catch(() => ({}))
    ]);

    const origin = url.origin;
    return {
      priorities: PRIORITIES,
      ticketTypes: CASE_TYPES,
      origin,
      mailboxes: mailboxesRes.mailboxes || [],
      profiles: (usersRes.active_users?.active_users || []).map((u) => ({
        id: u.id,
        name:
          u.user_details?.first_name && u.user_details?.last_name
            ? `${u.user_details.first_name} ${u.user_details.last_name}`
            : u.user_details?.email || u.email
      }))
    };
  } catch (err) {
    console.error('Failed to load inbound mailboxes:', err);
    throw error(500, 'Failed to load inbound mailboxes');
  }
}

function buildBody(formData) {
  return {
    address: String(formData.get('address') || '').trim(),
    provider: String(formData.get('provider') || 'ses'),
    default_priority: String(formData.get('default_priority') || 'Normal'),
    default_case_type: String(formData.get('default_case_type') || '') || null,
    default_assignee_id: String(formData.get('default_assignee_id') || '') || null,
    is_active: formData.get('is_active') !== 'false'
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const body = buildBody(formData);
    try {
      const created = await apiRequest(
        '/cases/mailboxes/',
        { method: 'POST', body },
        { cookies, org: locals?.org }
      );
      return { success: true, created };
    } catch (err) {
      console.error('Failed to create mailbox:', err);
      return fail(400, { error: err?.message || 'Failed to create mailbox' });
    }
  },

  update: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = String(formData.get('id') || '');
    if (!id) return fail(400, { error: 'Missing mailbox id' });
    const body = buildBody(formData);
    try {
      const updated = await apiRequest(
        `/cases/mailboxes/${id}/`,
        { method: 'PUT', body },
        { cookies, org: locals?.org }
      );
      return { success: true, updated };
    } catch (err) {
      console.error('Failed to update mailbox:', err);
      return fail(400, { error: err?.message || 'Failed to update mailbox' });
    }
  },

  delete: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = String(formData.get('id') || '');
    if (!id) return fail(400, { error: 'Missing mailbox id' });
    try {
      await apiRequest(
        `/cases/mailboxes/${id}/`,
        { method: 'DELETE' },
        { cookies, org: locals?.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Failed to delete mailbox:', err);
      return fail(400, { error: err?.message || 'Failed to delete mailbox' });
    }
  }
};
