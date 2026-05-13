import { error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const PRIORITIES = ['Low', 'Normal', 'High', 'Urgent'];

function buildQs(url) {
  const qs = new URLSearchParams();
  for (const k of ['from', 'to', 'priority', 'team', 'agent']) {
    const v = url.searchParams.get(k);
    if (v) qs.append(k, v);
  }
  return qs.toString();
}

/** @type {import('./$types').PageServerLoad} */
export async function load({ url, locals, cookies }) {
  if (!locals.org) throw error(401, 'Login required');

  const qs = buildQs(url);
  const suffix = qs ? `?${qs}` : '';

  try {
    const [frt, mttr, backlog, agents, sla, usersRes, teamsRes] = await Promise.all([
      apiRequest(`/cases/analytics/frt/${suffix}`, {}, { cookies, org: locals.org }),
      apiRequest(`/cases/analytics/mttr/${suffix}`, {}, { cookies, org: locals.org }),
      apiRequest(`/cases/analytics/backlog/${suffix}`, {}, { cookies, org: locals.org }),
      apiRequest(`/cases/analytics/agents/${suffix}`, {}, { cookies, org: locals.org }),
      apiRequest(`/cases/analytics/sla/${suffix}`, {}, { cookies, org: locals.org }),
      apiRequest('/users/', {}, { cookies, org: locals.org }).catch(() => ({})),
      apiRequest('/teams/', {}, { cookies, org: locals.org }).catch(() => ({}))
    ]);

    const users = (usersRes.active_users?.active_users || []).map(
      /** @param {any} u */ (u) => ({
        id: u.id,
        email: u.user_details?.email || u.email
      })
    );
    const teams = (teamsRes.teams || teamsRes.results || []).map(
      /** @param {any} t */ (t) => ({ id: t.id, name: t.name })
    );

    return {
      filters: {
        from: url.searchParams.get('from') || '',
        to: url.searchParams.get('to') || '',
        priority: url.searchParams.get('priority') || '',
        team: url.searchParams.get('team') || '',
        agent: url.searchParams.get('agent') || ''
      },
      priorities: PRIORITIES,
      metrics: { frt, mttr, backlog, agents, sla },
      formOptions: { users, teams }
    };
  } catch (err) {
    console.error('Failed to load analytics:', err);
    throw error(500, 'Failed to load analytics');
  }
}
