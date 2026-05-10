/**
 * Tickets List Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/cases/ (URL preserved for backend compatibility)
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { fail, redirect, error } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ url, locals, cookies }) {
  const org = locals.org;
  const user = locals.user;

  if (!org) {
    throw error(401, 'Organization context required');
  }

  // Parse view mode (list or kanban)
  const viewMode = url.searchParams.get('view') || 'list';
  // Tier 2: when ?watching=true, swap the source endpoint to the
  // per-recipient watching list. Frontend filters/pagination still apply
  // client-side to keep the page shape simple in v1.
  const watchingOnly = url.searchParams.get('watching') === 'true';

  // Parse pagination params from URL
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '10');

  // Parse filter params from URL
  const filters = {
    search: url.searchParams.get('search') || '',
    status: url.searchParams.get('status') || '',
    priority: url.searchParams.get('priority') || '',
    case_type: url.searchParams.get('case_type') || '',
    assigned_to: url.searchParams.getAll('assigned_to'),
    tags: url.searchParams.getAll('tags'),
    created_at_gte: url.searchParams.get('created_at_gte') || '',
    created_at_lte: url.searchParams.get('created_at_lte') || '',
    show_merged: url.searchParams.get('show_merged') === 'true'
  };

  try {
    // Build query parameters
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
    if (filters.case_type) queryParams.append('case_type', filters.case_type);
    filters.assigned_to.forEach((id) => queryParams.append('assigned_to', id));
    filters.tags.forEach((id) => queryParams.append('tags', id));
    if (filters.created_at_gte) queryParams.append('created_at__gte', filters.created_at_gte);
    if (filters.created_at_lte) queryParams.append('created_at__lte', filters.created_at_lte);
    if (filters.show_merged) queryParams.append('show_merged', 'true');

    // Build kanban query params (reuse filter params)
    const kanbanQueryParams = new URLSearchParams();
    if (filters.search) kanbanQueryParams.append('search', filters.search);
    if (filters.priority) kanbanQueryParams.append('priority', filters.priority);
    if (filters.case_type) kanbanQueryParams.append('case_type', filters.case_type);
    filters.assigned_to.forEach((id) => kanbanQueryParams.append('assigned_to', id));
    if (filters.show_merged) kanbanQueryParams.append('show_merged', 'true');

    // Fetch tickets, kanban data, and dropdown options in parallel
    const ticketsEndpoint = watchingOnly
      ? '/cases/watching/'
      : `/cases/?${queryParams.toString()}`;
    const [ticketsResponse, kanbanResponse, accountsRes, usersRes, contactsRes, teamsRes, tagsRes] =
      await Promise.all([
        apiRequest(ticketsEndpoint, {}, { cookies, org }),
        viewMode === 'kanban'
          ? apiRequest(
              `/cases/kanban/${kanbanQueryParams.toString() ? '?' + kanbanQueryParams.toString() : ''}`,
              {},
              { cookies, org }
            )
          : Promise.resolve(null),
        apiRequest('/accounts/', {}, { cookies, org }).catch(() => ({})),
        apiRequest('/users/', {}, { cookies, org }).catch(() => ({})),
        apiRequest('/contacts/', {}, { cookies, org }).catch(() => ({})),
        apiRequest('/teams/', {}, { cookies, org }).catch(() => ({})),
        apiRequest('/tags/', {}, { cookies, org }).catch(() => ({}))
      ]);

    // Extract tickets from response (backend wire-format key: cases)
    let cases = [];
    if (ticketsResponse.cases) {
      cases = ticketsResponse.cases;
    } else if (Array.isArray(ticketsResponse)) {
      cases = ticketsResponse;
    } else if (ticketsResponse.results) {
      cases = ticketsResponse.results;
    }

    // Transform Django tickets to frontend structure
    const transformedTickets = cases.map((ticketItem) => ({
      id: ticketItem.id,
      subject: ticketItem.name,
      description: ticketItem.description,
      status: ticketItem.status,
      priority: ticketItem.priority,
      ticketType: ticketItem.case_type,
      closedOn: ticketItem.closed_on,
      createdAt: ticketItem.created_at,
      updatedAt: ticketItem.updated_at,
      isActive: ticketItem.is_active,
      escalationCount: ticketItem.escalation_count || 0,
      lastEscalationFiredAt: ticketItem.last_escalation_fired_at,
      isProblem: !!ticketItem.is_problem,
      childCount: ticketItem.child_count || 0,

      // Created by
      createdBy: ticketItem.created_by
        ? {
            id: ticketItem.created_by.id,
            name:
              ticketItem.created_by.first_name && ticketItem.created_by.last_name
                ? `${ticketItem.created_by.first_name} ${ticketItem.created_by.last_name}`
                : ticketItem.created_by.email
          }
        : null,

      // Assigned to (multiple profiles)
      assignedTo: (ticketItem.assigned_to || []).map((profile) => ({
        id: profile.id,
        name:
          profile.user_details?.first_name && profile.user_details?.last_name
            ? `${profile.user_details.first_name} ${profile.user_details.last_name}`
            : profile.user_details?.email || profile.email
      })),

      // Owner (first assigned user for backwards compatibility)
      owner:
        ticketItem.assigned_to && ticketItem.assigned_to.length > 0
          ? {
              id: ticketItem.assigned_to[0].id,
              name:
                ticketItem.assigned_to[0].user_details?.first_name &&
                ticketItem.assigned_to[0].user_details?.last_name
                  ? `${ticketItem.assigned_to[0].user_details.first_name} ${ticketItem.assigned_to[0].user_details.last_name}`
                  : ticketItem.assigned_to[0].user_details?.email || ticketItem.assigned_to[0].email
            }
          : null,

      // Account
      account: ticketItem.account
        ? {
            id: ticketItem.account.id,
            name: ticketItem.account.name
          }
        : null,

      // Contacts (M2M)
      contacts: (ticketItem.contacts || []).map((contact) => ({
        id: contact.id,
        name:
          contact.first_name && contact.last_name
            ? `${contact.first_name} ${contact.last_name}`
            : contact.email,
        email: contact.email
      })),

      // Teams (M2M)
      teams: (ticketItem.teams || []).map((team) => ({
        id: team.id,
        name: team.name
      })),

      // Tags (M2M)
      tags: (ticketItem.tags || []).map((tag) => ({
        id: tag.id,
        name: tag.name
      })),

      // Comments (from detail endpoint)
      comments: (ticketItem.comments || []).map((comment) => ({
        id: comment.id,
        body: comment.comment,
        createdAt: comment.created_at,
        author: comment.commented_by
          ? {
              id: comment.commented_by.id,
              name: comment.commented_by.user_details?.email || comment.commented_by.email
            }
          : null
      }))
    }));

    // Status options from Django (matching backend ticket status choices)
    const statusOptions = ['New', 'Assigned', 'Pending', 'Closed', 'Rejected', 'Duplicate'];
    const ticketTypeOptions = ['Question', 'Incident', 'Problem'];

    // Get total count from response
    const total = ticketsResponse.cases_count || ticketsResponse.count || transformedTickets.length;

    // Transform accounts for dropdown/lookup
    let accountsList = [];
    if (accountsRes.active_accounts?.open_accounts) {
      accountsList = accountsRes.active_accounts.open_accounts;
    } else if (accountsRes.results) {
      accountsList = accountsRes.results;
    } else if (Array.isArray(accountsRes)) {
      accountsList = accountsRes;
    }
    const accounts = accountsList.map((a) => ({ id: a.id, name: a.name }));

    // Transform users
    const users = (usersRes.active_users?.active_users || []).map((u) => ({
      id: u.id,
      name:
        u.user_details?.first_name && u.user_details?.last_name
          ? `${u.user_details.first_name} ${u.user_details.last_name}`
          : u.user_details?.email || u.email
    }));

    // Transform contacts
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
      name: c.first_name && c.last_name ? `${c.first_name} ${c.last_name}` : c.email,
      email: c.email
    }));

    // Transform teams
    const teams = (teamsRes.teams || teamsRes.results || []).map((t) => ({
      id: t.id,
      name: t.name
    }));

    // Transform tags (include color for TagFilter)
    const tags = (tagsRes.tags || tagsRes.results || []).map((t) => ({
      id: t.id,
      name: t.name,
      color: t.color || 'blue'
    }));

    return {
      tickets: transformedTickets,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit) || 1
      },
      filters,
      viewMode,
      watchingOnly,
      kanbanData: kanbanResponse,
      statusOptions,
      ticketTypeOptions,
      // Dropdown options loaded server-side
      formOptions: {
        accounts,
        users,
        contacts,
        teams,
        tags
      }
    };
  } catch (err) {
    console.error('Error loading tickets from API:', err);
    throw error(500, `Failed to load tickets: ${err.message}`);
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const name = form.get('title')?.toString().trim();
      const description = form.get('description')?.toString().trim();
      const accountId = form.get('accountId')?.toString();
      const dueDateValue = form.get('dueDate');
      const closedOn = dueDateValue ? dueDateValue.toString() : null;
      const priority = form.get('priority')?.toString() || 'Normal';
      const ticketType = form.get('ticketType')?.toString() || '';
      const assignedToJson = form.get('assignedTo')?.toString();
      const contactsJson = form.get('contacts')?.toString();
      const teamsJson = form.get('teams')?.toString();
      const tagsJson = form.get('tags')?.toString();

      // Parse JSON arrays
      let assignedTo = [];
      let contacts = [];
      let teams = [];
      let tags = [];

      try {
        assignedTo = assignedToJson ? JSON.parse(assignedToJson) : [];
        contacts = contactsJson ? JSON.parse(contactsJson) : [];
        teams = teamsJson ? JSON.parse(teamsJson) : [];
        tags = tagsJson ? JSON.parse(tagsJson) : [];
      } catch {
        // Fallback for single ID format
        const ownerId = form.get('assignedId')?.toString();
        if (ownerId) assignedTo = [ownerId];
      }

      if (!name) {
        return fail(400, { error: 'Ticket name is required.' });
      }

      // Create ticket via API
      const caseData = {
        name,
        description,
        account: accountId || null,
        closed_on: closedOn,
        priority,
        case_type: ticketType,
        assigned_to: assignedTo,
        contacts,
        teams,
        tags,
        status: 'New'
      };

      const newCase = await apiRequest(
        '/cases/',
        {
          method: 'POST',
          body: caseData
        },
        { cookies, org: locals.org }
      );

      return { success: true, case: newCase };
    } catch (err) {
      console.error('Error creating ticket:', err);
      return fail(500, { error: 'Failed to create ticket' });
    }
  },

  // Used by the list page's inline cell-edit flow (CrmTable onRowChange).
  update: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const name = form.get('title')?.toString().trim();
      const description = form.get('description')?.toString().trim();
      const dueDateValue = form.get('dueDate');
      const closedOn = dueDateValue ? dueDateValue.toString() : null;
      const priority = form.get('priority')?.toString() || 'Normal';
      const status = form.get('status')?.toString() || 'New';
      const ticketType = form.get('ticketType')?.toString() || '';
      const ticketId = form.get('ticketId')?.toString();
      const assignedToJson = form.get('assignedTo')?.toString();
      const contactsJson = form.get('contacts')?.toString();
      const teamsJson = form.get('teams')?.toString();
      const tagsJson = form.get('tags')?.toString();

      let assignedTo = [];
      let contacts = [];
      let teams = [];
      let tags = [];

      try {
        assignedTo = assignedToJson ? JSON.parse(assignedToJson) : [];
        contacts = contactsJson ? JSON.parse(contactsJson) : [];
        teams = teamsJson ? JSON.parse(teamsJson) : [];
        tags = tagsJson ? JSON.parse(tagsJson) : [];
      } catch {
        const ownerId = form.get('assignedId')?.toString();
        if (ownerId) assignedTo = [ownerId];
      }

      if (!name || !ticketId) {
        return fail(400, { error: 'Ticket name and ID are required.' });
      }

      const caseData = {
        name,
        description,
        closed_on: closedOn,
        priority,
        status,
        case_type: ticketType,
        assigned_to: assignedTo,
        contacts,
        teams,
        tags
      };

      await apiRequest(
        `/cases/${ticketId}/`,
        { method: 'PATCH', body: caseData },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error updating ticket:', err);
      return fail(500, { error: 'Failed to update ticket' });
    }
  },

  moveTicket: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const form = await request.formData();
      const ticketId = form.get('ticketId')?.toString();
      const status = form.get('status')?.toString();
      const stageId = form.get('stageId')?.toString() || null;
      const aboveTicketId = form.get('aboveTicketId')?.toString() || null;
      const belowTicketId = form.get('belowTicketId')?.toString() || null;

      if (!ticketId) {
        return fail(400, { error: 'Ticket ID is required' });
      }

      /** @type {Record<string, unknown>} */
      const moveData = {};
      if (status) moveData.status = status;
      if (stageId) moveData.stage_id = stageId;
      if (aboveTicketId) moveData.above_case_id = aboveTicketId;
      if (belowTicketId) moveData.below_case_id = belowTicketId;

      await apiRequest(
        `/cases/${ticketId}/move/`,
        { method: 'PATCH', body: moveData },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error moving ticket:', err);
      return fail(500, { error: 'Failed to move ticket' });
    }
  },

  bulkUpdate: async ({ request, locals, cookies }) => {
    const form = await request.formData();
    const ids = JSON.parse(form.get('ids')?.toString() || '[]');
    const fields = JSON.parse(form.get('fields')?.toString() || '{}');
    if (!ids.length) return fail(400, { error: 'No tickets selected' });
    try {
      await apiRequest(
        '/cases/bulk/update/',
        { method: 'POST', body: { ids, fields } },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Bulk update error:', err);
      return fail(500, { error: 'Bulk update failed' });
    }
  },

  bulkDelete: async ({ request, locals, cookies }) => {
    const form = await request.formData();
    const ids = JSON.parse(form.get('ids')?.toString() || '[]');
    if (!ids.length) return fail(400, { error: 'No tickets selected' });
    try {
      await apiRequest(
        '/cases/bulk/delete/',
        { method: 'POST', body: { ids } },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Bulk delete error:', err);
      return fail(500, { error: 'Bulk delete failed' });
    }
  }
};
