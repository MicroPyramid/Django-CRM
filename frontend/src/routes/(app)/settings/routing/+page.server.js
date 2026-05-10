import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const STRATEGIES = [
  { id: 'direct', label: 'Direct (single agent)' },
  { id: 'round_robin', label: 'Round-robin' },
  { id: 'least_busy', label: 'Least busy' },
  { id: 'by_team', label: 'Assign to team' }
];

const FIELDS = [
  { id: 'priority', label: 'Priority' },
  { id: 'case_type', label: 'Ticket type' },
  { id: 'account', label: 'Account' },
  { id: 'tags', label: 'Tag' },
  { id: 'from_email_domain', label: 'From email domain' },
  { id: 'mailbox_id', label: 'Mailbox' }
];

const OPS = [
  { id: 'eq', label: 'equals' },
  { id: 'in', label: 'is one of' },
  { id: 'contains', label: 'contains' },
  { id: 'regex', label: 'matches regex' }
];

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, locals }) {
  const profile = locals.profile;
  if (profile?.role !== 'ADMIN' && !profile?.is_organization_admin) {
    throw error(403, 'Only admins can manage routing rules');
  }

  try {
    const [rulesRes, usersRes, teamsRes, mailboxesRes] = await Promise.all([
      apiRequest('/cases/routing-rules/', {}, { cookies, org: locals?.org }),
      apiRequest('/users/', {}, { cookies, org: locals?.org }).catch(() => ({})),
      apiRequest('/teams/', {}, { cookies, org: locals?.org }).catch(() => ({})),
      apiRequest('/cases/mailboxes/', {}, { cookies, org: locals?.org }).catch(
        () => ({})
      )
    ]);

    return {
      strategies: STRATEGIES,
      fields: FIELDS,
      ops: OPS,
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
      })),
      mailboxes: (mailboxesRes.mailboxes || []).map((m) => ({
        id: m.id,
        address: m.address
      }))
    };
  } catch (err) {
    console.error('Failed to load routing rules:', err);
    throw error(500, 'Failed to load routing rules');
  }
}

function buildBody(formData) {
  /** @type {Record<string, unknown>} */
  const body = {
    name: String(formData.get('name') || '').trim(),
    priority_order: Number(formData.get('priority_order') || 100),
    is_active: formData.get('is_active') !== 'false',
    strategy: String(formData.get('strategy') || 'direct'),
    stop_processing: formData.get('stop_processing') !== 'false'
  };
  const rawConditions = String(formData.get('conditions') || '[]');
  try {
    body.conditions = JSON.parse(rawConditions);
  } catch {
    body.conditions = [];
  }
  const rawAssignees = String(formData.get('target_assignee_ids') || '[]');
  try {
    body.target_assignee_ids = JSON.parse(rawAssignees);
  } catch {
    body.target_assignee_ids = [];
  }
  const team = String(formData.get('target_team_id') || '');
  body.target_team_id = team || null;
  return body;
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const body = buildBody(formData);
    try {
      const created = await apiRequest(
        '/cases/routing-rules/',
        { method: 'POST', body },
        { cookies, org: locals?.org }
      );
      return { success: true, created };
    } catch (err) {
      console.error('Failed to create routing rule:', err);
      return fail(400, { error: err?.message || 'Failed to create routing rule' });
    }
  },

  update: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = String(formData.get('id') || '');
    if (!id) return fail(400, { error: 'Missing rule id' });
    const body = buildBody(formData);
    try {
      const updated = await apiRequest(
        `/cases/routing-rules/${id}/`,
        { method: 'PUT', body },
        { cookies, org: locals?.org }
      );
      return { success: true, updated };
    } catch (err) {
      console.error('Failed to update routing rule:', err);
      return fail(400, { error: err?.message || 'Failed to update routing rule' });
    }
  },

  delete: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = String(formData.get('id') || '');
    if (!id) return fail(400, { error: 'Missing rule id' });
    try {
      await apiRequest(
        `/cases/routing-rules/${id}/`,
        { method: 'DELETE' },
        { cookies, org: locals?.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Failed to delete routing rule:', err);
      return fail(400, { error: err?.message || 'Failed to delete routing rule' });
    }
  }
};
