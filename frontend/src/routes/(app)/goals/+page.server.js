/**
 * Sales Goals Page - API Version
 *
 * Django endpoint: GET /api/opportunities/goals/
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

export async function load({ locals, cookies, url }) {
  const userId = locals.user?.id;
  const org = locals.org;

  if (!userId) {
    return {
      goals: [],
      leaderboard: [],
      pagination: { page: 1, limit: 10, total: 0, totalPages: 1 },
      options: { users: [], teams: [] }
    };
  }

  if (!org) {
    throw error(401, 'Organization context required');
  }

  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '10');

  const filters = {
    search: url.searchParams.get('search') || '',
    active: url.searchParams.get('active') || '',
    current: url.searchParams.get('current') || '',
    assigned_to: url.searchParams.get('assigned_to') || '',
    team: url.searchParams.get('team') || '',
    period_type: url.searchParams.get('period_type') || ''
  };

  try {
    const queryParams = buildQueryParams({});
    queryParams.append('limit', limit.toString());
    queryParams.append('offset', ((page - 1) * limit).toString());

    if (filters.search) queryParams.append('search', filters.search);
    if (filters.active) queryParams.append('active', filters.active);
    if (filters.current) queryParams.append('current', filters.current);
    if (filters.assigned_to) queryParams.append('assigned_to', filters.assigned_to);
    if (filters.team) queryParams.append('team', filters.team);
    if (filters.period_type) queryParams.append('period_type', filters.period_type);

    const queryString = queryParams.toString();

    const [goalsResponse, leaderboardResponse, teamsUsersResponse] = await Promise.all([
      apiRequest(`/opportunities/goals/${queryString ? `?${queryString}` : ''}`, {}, { cookies, org }),
      apiRequest('/opportunities/goals/leaderboard/', {}, { cookies, org }).catch(() => ({
        leaderboard: []
      })),
      apiRequest('/users/get-teams-and-users/', {}, { cookies, org }).catch(() => ({
        teams: [],
        profiles: []
      }))
    ]);

    const goals = (goalsResponse.goals || []).map((goal) => ({
      id: goal.id,
      name: goal.name,
      goalType: goal.goal_type,
      targetValue: goal.target_value ? Number(goal.target_value) : 0,
      periodType: goal.period_type,
      periodStart: goal.period_start,
      periodEnd: goal.period_end,
      assignedTo: goal.assigned_to_detail
        ? {
            id: goal.assigned_to_detail.id,
            name: goal.assigned_to_detail.user_details?.email || goal.assigned_to_detail.email
          }
        : null,
      assignedToId: goal.assigned_to || null,
      team: goal.team_detail
        ? {
            id: goal.team_detail.id,
            name: goal.team_detail.name
          }
        : null,
      teamId: goal.team || null,
      isActive: goal.is_active,
      progressValue: goal.progress_value || 0,
      progressPercent: goal.progress_percent || 0,
      status: goal.status || 'behind',
      createdAt: goal.created_at
    }));

    const leaderboard = (leaderboardResponse.leaderboard || []).map((entry) => ({
      rank: entry.rank,
      goalId: entry.goal_id,
      goalName: entry.goal_name,
      user: entry.user,
      target: entry.target,
      achieved: entry.achieved,
      percent: entry.percent
    }));

    const total = goalsResponse.goals_count || goals.length;

    const users = (teamsUsersResponse.profiles || []).map((u) => ({
      id: u.id,
      name: u.user_details?.email || u.email || 'Unknown',
      email: u.user_details?.email || u.email
    }));

    const teams = (teamsUsersResponse.teams || []).map((t) => ({
      id: t.id,
      name: t.name
    }));

    return {
      goals,
      leaderboard,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit) || 1
      },
      options: { users, teams },
      filters
    };
  } catch (err) {
    console.error('Error loading goals from API:', err);
    throw error(500, 'Failed to load goals');
  }
}

export const actions = {
  create: async ({ request, locals, cookies }) => {
    try {
      const formData = await request.formData();
      const org = locals.org;

      if (!org) {
        return fail(400, { message: 'Organization context required' });
      }

      const goalData = {
        name: formData.get('name')?.toString() || '',
        goal_type: formData.get('goalType')?.toString() || 'REVENUE',
        target_value: formData.get('targetValue') ? Number(formData.get('targetValue')) : 0,
        period_type: formData.get('periodType')?.toString() || 'MONTHLY',
        period_start: formData.get('periodStart')?.toString() || null,
        period_end: formData.get('periodEnd')?.toString() || null,
        assigned_to: formData.get('assignedTo')?.toString() || null,
        team: formData.get('team')?.toString() || null,
        is_active: true
      };

      await apiRequest('/opportunities/goals/', { method: 'POST', body: goalData }, { cookies, org });

      return { success: true, message: 'Goal created successfully' };
    } catch (err) {
      console.error('Error creating goal:', err);
      return fail(500, { message: `Failed to create goal: ${err.message}` });
    }
  },

  update: async ({ request, locals, cookies }) => {
    try {
      const formData = await request.formData();
      const goalId = formData.get('goalId')?.toString();
      const org = locals.org;

      if (!goalId || !org) {
        return fail(400, { message: 'Missing required data' });
      }

      /** @type {Record<string, any>} */
      const goalData = {};

      if (formData.has('name')) goalData.name = formData.get('name')?.toString() || '';
      if (formData.has('goalType')) goalData.goal_type = formData.get('goalType')?.toString();
      if (formData.has('targetValue'))
        goalData.target_value = Number(formData.get('targetValue')) || 0;
      if (formData.has('periodType')) goalData.period_type = formData.get('periodType')?.toString();
      if (formData.has('periodStart'))
        goalData.period_start = formData.get('periodStart')?.toString() || null;
      if (formData.has('periodEnd'))
        goalData.period_end = formData.get('periodEnd')?.toString() || null;
      if (formData.has('assignedTo'))
        goalData.assigned_to = formData.get('assignedTo')?.toString() || null;
      if (formData.has('team')) goalData.team = formData.get('team')?.toString() || null;
      if (formData.has('isActive')) goalData.is_active = formData.get('isActive') === 'true';

      await apiRequest(
        `/opportunities/goals/${goalId}/`,
        { method: 'PUT', body: goalData },
        { cookies, org }
      );

      return { success: true, message: 'Goal updated successfully' };
    } catch (err) {
      console.error('Error updating goal:', err);
      return fail(500, { message: `Failed to update goal: ${err.message}` });
    }
  },

  delete: async ({ request, locals, cookies }) => {
    try {
      const formData = await request.formData();
      const goalId = formData.get('goalId')?.toString();
      const org = locals.org;

      if (!goalId || !org) {
        return fail(400, { message: 'Missing required data' });
      }

      await apiRequest(
        `/opportunities/goals/${goalId}/`,
        { method: 'DELETE' },
        { cookies, org }
      );

      return { success: true, message: 'Goal deleted successfully' };
    } catch (err) {
      console.error('Error deleting goal:', err);
      return fail(500, { message: `Failed to delete goal: ${err.message}` });
    }
  }
};
