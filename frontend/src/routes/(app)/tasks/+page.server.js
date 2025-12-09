/**
 * Tasks List Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/tasks/
 *
 * Task API fields:
 * - title, status, priority, due_date, description, account
 * - contacts (M2M), teams (M2M), assigned_to (M2M)
 * - created_by, created_at, updated_at
 */

import { error } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies, url }) {
  const user = locals.user;
  const org = locals.org;

  if (!org) {
    throw error(401, 'Organization context required');
  }

  // Parse view mode from URL
  const viewMode = url.searchParams.get('view') || 'list';

  // Parse pagination params from URL
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '10');

  // Parse filter params from URL
  const filters = {
    search: url.searchParams.get('search') || '',
    status: url.searchParams.get('status') || '',
    priority: url.searchParams.get('priority') || '',
    assigned_to: url.searchParams.getAll('assigned_to'),
    tags: url.searchParams.getAll('tags'),
    due_date_gte: url.searchParams.get('due_date_gte') || '',
    due_date_lte: url.searchParams.get('due_date_lte') || ''
  };

  try {
    // Build query parameters for tasks
    const queryParams = buildQueryParams({
      sort: 'created_at',
      order: 'desc'
    });
    queryParams.append('limit', limit.toString());
    queryParams.append('offset', ((page - 1) * limit).toString());

    // Add filter params
    if (filters.search) queryParams.append('search', filters.search);
    if (filters.status) queryParams.append('status', filters.status);
    if (filters.priority) queryParams.append('priority', filters.priority);
    filters.assigned_to.forEach((id) => queryParams.append('assigned_to', id));
    filters.tags.forEach((id) => queryParams.append('tags', id));
    if (filters.due_date_gte) queryParams.append('due_date__gte', filters.due_date_gte);
    if (filters.due_date_lte) queryParams.append('due_date__lte', filters.due_date_lte);

    // Build kanban query params (similar filters)
    const kanbanQueryParams = new URLSearchParams();
    if (filters.search) kanbanQueryParams.append('search', filters.search);
    if (filters.priority) kanbanQueryParams.append('priority', filters.priority);
    filters.assigned_to.forEach((id) => kanbanQueryParams.append('assigned_to', id));
    if (filters.due_date_gte) kanbanQueryParams.append('due_date__gte', filters.due_date_gte);
    if (filters.due_date_lte) kanbanQueryParams.append('due_date__lte', filters.due_date_lte);

    // Fetch tasks (or kanban data) and dropdown options in parallel
    const kanbanQueryString = kanbanQueryParams.toString();
    const [
      tasksResponse,
      kanbanResponse,
      usersRes,
      accountsRes,
      contactsRes,
      teamsRes,
      opportunitiesRes,
      casesRes,
      leadsRes,
      tagsRes
    ] = await Promise.all([
      apiRequest(`/tasks/?${queryParams.toString()}`, {}, { cookies, org }),
      viewMode === 'kanban'
        ? apiRequest(
            `/tasks/kanban/${kanbanQueryString ? '?' + kanbanQueryString : ''}`,
            {},
            { cookies, org }
          )
        : Promise.resolve(null),
      apiRequest('/users/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/accounts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/contacts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/teams/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/opportunities/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/cases/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/leads/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/tags/', {}, { cookies, org }).catch(() => ({}))
    ]);

    // Handle Django response structure
    // Django TaskListView returns { tasks: [...], tasks_count: ..., ... }
    let tasks = [];
    if (tasksResponse.tasks) {
      tasks = tasksResponse.tasks;
    } else if (Array.isArray(tasksResponse)) {
      tasks = tasksResponse;
    } else if (tasksResponse.results) {
      tasks = tasksResponse.results;
    }

    // Transform accounts first (needed for task account name lookup)
    let accountsList = [];
    if (accountsRes.active_accounts?.open_accounts) {
      accountsList = accountsRes.active_accounts.open_accounts;
    } else if (accountsRes.results) {
      accountsList = accountsRes.results;
    } else if (Array.isArray(accountsRes)) {
      accountsList = accountsRes;
    }
    const accounts = accountsList.map((a) => ({ id: a.id, name: a.name }));

    // Transform cases, opportunities, leads early (needed for task field name lookups)
    const cases = (casesRes.cases || casesRes.results || []).map((c) => ({
      id: c.id,
      name: c.name
    }));
    const opportunities = (opportunitiesRes.opportunities || opportunitiesRes.results || []).map(
      (o) => ({ id: o.id, name: o.name })
    );
    const leads = (leadsRes.leads || leadsRes.results || []).map((l) => ({
      id: l.id,
      name:
        l.first_name || l.last_name
          ? `${l.first_name || ''} ${l.last_name || ''}`.trim()
          : l.title || 'Lead'
    }));

    // Helper to look up related entity name from list
    const getRelatedName = (data, list, fallback) => {
      if (!data) return null;
      // If it's an object with name, use it
      if (typeof data === 'object' && data.name) {
        return { id: data.id, name: data.name };
      }
      // If it's just an ID (string), look up from list
      const id = typeof data === 'object' ? data.id : data;
      const found = list.find((item) => item.id === id);
      return { id, name: found?.name || fallback };
    };

    // Transform Django tasks to frontend structure
    const transformedTasks = tasks.map((task) => ({
      id: task.id,
      subject: task.title,
      description: task.description,
      status: task.status,
      priority: task.priority,
      dueDate: task.due_date,
      createdAt: task.created_at,
      updatedAt: task.updated_at,

      // All assigned users (M2M)
      assignedTo: (task.assigned_to || []).map((u) => ({
        id: u.id,
        name: u.user_details?.email || u.user?.email || u.email || 'Unknown'
      })),

      // Contacts (M2M)
      contacts: (task.contacts || []).map((c) => ({
        id: c.id,
        name: c.first_name ? `${c.first_name} ${c.last_name || ''}`.trim() : c.email || 'Unknown'
      })),

      // Teams (M2M)
      teams: (task.teams || []).map((t) => ({
        id: t.id,
        name: t.name
      })),

      // Tags (M2M)
      tags: (task.tags || []).map((t) => ({
        id: t.id,
        name: t.name
      })),

      // Account (FK) - lookup name from accounts list if needed
      account: getRelatedName(task.account, accounts, 'Unknown Account'),

      // Opportunity (FK) - lookup name from opportunities list if needed
      opportunity: getRelatedName(task.opportunity, opportunities, 'Unknown Opportunity'),

      // Case (FK) - lookup name from cases list if needed
      case_: getRelatedName(task.case, cases, 'Unknown Case'),

      // Lead (FK) - lookup name from leads list if needed
      lead: getRelatedName(task.lead, leads, 'Unknown Lead'),

      // Created by
      createdBy: task.created_by
        ? {
            id: task.created_by.id,
            name: task.created_by.email
          }
        : null
    }));

    // Get total count from response
    const total = tasksResponse.tasks_count || tasksResponse.count || transformedTasks.length;

    // Transform dropdown options
    const users = (usersRes.active_users?.active_users || []).map((u) => ({
      id: u.id,
      name: u.user_details?.email || u.email
    }));

    // accounts already transformed above for task account name lookup

    let contactsList = [];
    if (contactsRes.contact_obj_list) {
      contactsList = contactsRes.contact_obj_list;
    } else if (contactsRes.results) {
      contactsList = contactsRes.results;
    } else if (Array.isArray(contactsRes)) {
      contactsList = contactsRes;
    }
    const contacts = contactsList.map((c) => ({
      id: c.id,
      name: c.first_name ? `${c.first_name} ${c.last_name || ''}`.trim() : c.email || 'Unknown'
    }));

    const teams = (teamsRes.teams || teamsRes.results || []).map((t) => ({
      id: t.id,
      name: t.name
    }));

    // opportunities, cases, leads already transformed above for task field name lookups

    // Transform tags (include color for TagFilter)
    const tags = (tagsRes.tags || tagsRes.results || []).map((t) => ({
      id: t.id,
      name: t.name,
      color: t.color || 'blue'
    }));

    return {
      tasks: transformedTasks,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit) || 1
      },
      filters,
      viewMode,
      kanbanData: kanbanResponse,
      // Dropdown options for drawer form
      formOptions: {
        users,
        accounts,
        contacts,
        teams,
        opportunities,
        cases,
        leads,
        tags
      }
    };
  } catch (err) {
    console.error('Error loading tasks from API:', err);
    throw error(500, `Failed to load tasks: ${err.message}`);
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const form = await request.formData();
      const subject = form.get('subject')?.toString().trim();
      const description = form.get('description')?.toString().trim();
      const status = form.get('status')?.toString() || 'New';
      const priority = form.get('priority')?.toString() || 'Medium';
      const dueDate = form.get('dueDate')?.toString() || null;
      const accountId = form.get('accountId')?.toString() || null;
      const opportunityId = form.get('opportunityId')?.toString() || null;
      const caseId = form.get('caseId')?.toString() || null;
      const leadId = form.get('leadId')?.toString() || null;

      // Parse array fields (sent as JSON strings)
      const assignedToJson = form.get('assignedTo')?.toString() || '[]';
      const contactsJson = form.get('contacts')?.toString() || '[]';
      const teamsJson = form.get('teams')?.toString() || '[]';
      const tagsJson = form.get('tags')?.toString() || '[]';

      const assignedTo = JSON.parse(assignedToJson);
      const contacts = JSON.parse(contactsJson);
      const teams = JSON.parse(teamsJson);
      const tags = JSON.parse(tagsJson);

      if (!subject) {
        return { success: false, error: 'Subject is required' };
      }

      // Transform to Django field names
      const djangoData = {
        title: subject,
        description: description || null,
        status: status,
        priority: priority,
        due_date: dueDate,
        assigned_to: assignedTo,
        contacts: contacts,
        teams: teams,
        tags: tags,
        account: accountId || null,
        opportunity: opportunityId || null,
        case: caseId || null,
        lead: leadId || null
      };

      await apiRequest(
        '/tasks/',
        {
          method: 'POST',
          body: djangoData
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error creating task:', err);
      return { success: false, error: 'Failed to create task' };
    }
  },

  update: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const form = await request.formData();
      const taskId = form.get('taskId')?.toString();
      const subject = form.get('subject')?.toString().trim();
      const description = form.get('description')?.toString().trim();
      const status = form.get('status')?.toString() || 'New';
      const priority = form.get('priority')?.toString() || 'Medium';
      const dueDate = form.get('dueDate')?.toString() || null;
      const accountId = form.get('accountId')?.toString() || null;
      const opportunityId = form.get('opportunityId')?.toString() || null;
      const caseId = form.get('caseId')?.toString() || null;
      const leadId = form.get('leadId')?.toString() || null;

      // Parse array fields (sent as JSON strings)
      const assignedToJson = form.get('assignedTo')?.toString() || '[]';
      const contactsJson = form.get('contacts')?.toString() || '[]';
      const teamsJson = form.get('teams')?.toString() || '[]';
      const tagsJson = form.get('tags')?.toString() || '[]';

      const assignedTo = JSON.parse(assignedToJson);
      const contacts = JSON.parse(contactsJson);
      const teams = JSON.parse(teamsJson);
      const tags = JSON.parse(tagsJson);

      if (!taskId || !subject) {
        return { success: false, error: 'Task ID and subject are required' };
      }

      // Transform to Django field names
      const djangoData = {
        title: subject,
        description: description || null,
        status: status,
        priority: priority,
        due_date: dueDate,
        assigned_to: assignedTo,
        contacts: contacts,
        teams: teams,
        tags: tags,
        account: accountId || null,
        opportunity: opportunityId || null,
        case: caseId || null,
        lead: leadId || null
      };

      await apiRequest(
        `/tasks/${taskId}/`,
        {
          method: 'PATCH',
          body: djangoData
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error updating task:', err);
      return { success: false, error: 'Failed to update task' };
    }
  },

  complete: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const form = await request.formData();
      const taskId = form.get('taskId')?.toString();

      if (!taskId) {
        return { success: false, error: 'Task ID is required' };
      }

      // Update with PATCH, changing only status to Completed
      await apiRequest(
        `/tasks/${taskId}/`,
        {
          method: 'PATCH',
          body: { status: 'Completed' }
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error completing task:', err);
      return { success: false, error: 'Failed to complete task' };
    }
  },

  reopen: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const form = await request.formData();
      const taskId = form.get('taskId')?.toString();

      if (!taskId) {
        return { success: false, error: 'Task ID is required' };
      }

      // Update with PATCH, changing only status to New
      await apiRequest(
        `/tasks/${taskId}/`,
        {
          method: 'PATCH',
          body: { status: 'New' }
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error reopening task:', err);
      return { success: false, error: 'Failed to reopen task' };
    }
  },

  delete: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const form = await request.formData();
      const taskId = form.get('taskId')?.toString();

      if (!taskId) {
        return { success: false, error: 'Task ID is required' };
      }

      await apiRequest(`/tasks/${taskId}/`, { method: 'DELETE' }, { cookies, org });

      return { success: true };
    } catch (err) {
      console.error('Error deleting task:', err);
      return { success: false, error: 'Failed to delete task' };
    }
  },

  moveTask: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const form = await request.formData();
      const taskId = form.get('taskId')?.toString();
      const status = form.get('status')?.toString();
      const stageId = form.get('stageId')?.toString() || null;
      const aboveTaskId = form.get('aboveTaskId')?.toString() || null;
      const belowTaskId = form.get('belowTaskId')?.toString() || null;

      if (!taskId) {
        return { success: false, error: 'Task ID is required' };
      }

      if (!status && !stageId) {
        return { success: false, error: 'Either status or stageId is required' };
      }

      /** @type {Record<string, string>} */
      const moveData = {};
      if (status) moveData.status = status;
      if (stageId) moveData.stage_id = stageId;
      if (aboveTaskId) moveData.above_task_id = aboveTaskId;
      if (belowTaskId) moveData.below_task_id = belowTaskId;

      await apiRequest(
        `/tasks/${taskId}/move/`,
        {
          method: 'PATCH',
          body: moveData
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error moving task:', err);
      return { success: false, error: 'Failed to move task' };
    }
  }
};
