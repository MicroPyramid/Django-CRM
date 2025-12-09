/**
 * Cases List Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/cases/
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
		created_at_lte: url.searchParams.get('created_at_lte') || ''
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

		// Fetch cases and dropdown options in parallel
		const [casesResponse, accountsRes, usersRes, contactsRes, teamsRes, tagsRes] = await Promise.all([
			apiRequest(`/cases/?${queryParams.toString()}`, {}, { cookies, org }),
			apiRequest('/accounts/', {}, { cookies, org }).catch(() => ({})),
			apiRequest('/users/', {}, { cookies, org }).catch(() => ({})),
			apiRequest('/contacts/', {}, { cookies, org }).catch(() => ({})),
			apiRequest('/teams/', {}, { cookies, org }).catch(() => ({})),
			apiRequest('/tags/', {}, { cookies, org }).catch(() => ({}))
		]);

		// Extract cases from response
		let cases = [];
		if (casesResponse.cases) {
			cases = casesResponse.cases;
		} else if (Array.isArray(casesResponse)) {
			cases = casesResponse;
		} else if (casesResponse.results) {
			cases = casesResponse.results;
		}

		// Transform Django cases to frontend structure
		const transformedCases = cases.map((caseItem) => ({
			id: caseItem.id,
			subject: caseItem.name,
			description: caseItem.description,
			status: caseItem.status,
			priority: caseItem.priority,
			caseType: caseItem.case_type,
			closedOn: caseItem.closed_on,
			createdAt: caseItem.created_at,
			updatedAt: caseItem.updated_at,
			isActive: caseItem.is_active,

			// Created by
			createdBy: caseItem.created_by
				? {
						id: caseItem.created_by.id,
						name:
							caseItem.created_by.first_name && caseItem.created_by.last_name
								? `${caseItem.created_by.first_name} ${caseItem.created_by.last_name}`
								: caseItem.created_by.email
					}
				: null,

			// Assigned to (multiple profiles)
			assignedTo: (caseItem.assigned_to || []).map((profile) => ({
				id: profile.id,
				name:
					profile.user_details?.first_name && profile.user_details?.last_name
						? `${profile.user_details.first_name} ${profile.user_details.last_name}`
						: profile.user_details?.email || profile.email
			})),

			// Owner (first assigned user for backwards compatibility)
			owner:
				caseItem.assigned_to && caseItem.assigned_to.length > 0
					? {
							id: caseItem.assigned_to[0].id,
							name:
								caseItem.assigned_to[0].user_details?.first_name &&
								caseItem.assigned_to[0].user_details?.last_name
									? `${caseItem.assigned_to[0].user_details.first_name} ${caseItem.assigned_to[0].user_details.last_name}`
									: caseItem.assigned_to[0].user_details?.email || caseItem.assigned_to[0].email
						}
					: null,

			// Account
			account: caseItem.account
				? {
						id: caseItem.account.id,
						name: caseItem.account.name
					}
				: null,

			// Contacts (M2M)
			contacts: (caseItem.contacts || []).map((contact) => ({
				id: contact.id,
				name:
					contact.first_name && contact.last_name
						? `${contact.first_name} ${contact.last_name}`
						: contact.email,
				email: contact.email
			})),

			// Teams (M2M)
			teams: (caseItem.teams || []).map((team) => ({
				id: team.id,
				name: team.name
			})),

			// Tags (M2M)
			tags: (caseItem.tags || []).map((tag) => ({
				id: tag.id,
				name: tag.name
			})),

			// Comments (from detail endpoint)
			comments: (caseItem.comments || []).map((comment) => ({
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

		// Status options from Django (matching backend CASE_TYPE choices)
		const statusOptions = ['New', 'Assigned', 'Pending', 'Closed', 'Rejected', 'Duplicate'];
		const caseTypeOptions = ['Question', 'Incident', 'Problem'];

		// Get total count from response
		const total = casesResponse.cases_count || casesResponse.count || transformedCases.length;

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
			name: u.user_details?.first_name && u.user_details?.last_name
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
			name: c.first_name && c.last_name
				? `${c.first_name} ${c.last_name}`
				: c.email,
			email: c.email
		}));

		// Transform teams
		const teams = (teamsRes.teams || teamsRes.results || []).map((t) => ({ id: t.id, name: t.name }));

		// Transform tags (include color for TagFilter)
		const tags = (tagsRes.tags || tagsRes.results || []).map((t) => ({ id: t.id, name: t.name, color: t.color || 'blue' }));

		return {
			cases: transformedCases,
			pagination: {
				page,
				limit,
				total,
				totalPages: Math.ceil(total / limit) || 1
			},
			filters,
			statusOptions,
			caseTypeOptions,
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
		console.error('Error loading cases from API:', err);
		throw error(500, `Failed to load cases: ${err.message}`);
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
			const caseType = form.get('caseType')?.toString() || '';
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
				return fail(400, { error: 'Case name is required.' });
			}

			// Create case via API
			const caseData = {
				name,
				description,
				account: accountId || null,
				closed_on: closedOn,
				priority,
				case_type: caseType,
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
			console.error('Error creating case:', err);
			return fail(500, { error: 'Failed to create case' });
		}
	},

	update: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const name = form.get('title')?.toString().trim();
			const description = form.get('description')?.toString().trim();
			const dueDateValue = form.get('dueDate');
			const closedOn = dueDateValue ? dueDateValue.toString() : null;
			const priority = form.get('priority')?.toString() || 'Normal';
			const status = form.get('status')?.toString() || 'New';
			const caseType = form.get('caseType')?.toString() || '';
			const caseId = form.get('caseId')?.toString();
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

			if (!name || !caseId) {
				return fail(400, { error: 'Case name and ID are required.' });
			}

			// Update case via API (account is read-only, not included)
			const caseData = {
				name,
				description,
				closed_on: closedOn,
				priority,
				status,
				case_type: caseType,
				assigned_to: assignedTo,
				contacts,
				teams,
				tags
			};

			await apiRequest(
				`/cases/${caseId}/`,
				{
					method: 'PATCH',
					body: caseData
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error updating case:', err);
			return fail(500, { error: 'Failed to update case' });
		}
	},

	close: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const caseId = form.get('caseId')?.toString();

			if (!caseId) {
				return fail(400, { error: 'Case ID is required.' });
			}

			await apiRequest(
				`/cases/${caseId}/`,
				{
					method: 'PATCH',
					body: { status: 'Closed' }
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error closing case:', err);
			return fail(500, { error: 'Failed to close case' });
		}
	},

	reopen: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const caseId = form.get('caseId')?.toString();

			if (!caseId) {
				return fail(400, { error: 'Case ID is required.' });
			}

			await apiRequest(
				`/cases/${caseId}/`,
				{
					method: 'PATCH',
					body: { status: 'Assigned' }
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error reopening case:', err);
			return fail(500, { error: 'Failed to reopen case' });
		}
	},

	delete: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const caseId = form.get('caseId')?.toString();

			if (!caseId) {
				return fail(400, { error: 'Case ID is required.' });
			}

			// Delete via API
			await apiRequest(`/cases/${caseId}/`, { method: 'DELETE' }, { cookies, org: locals.org });

			return { success: true };
		} catch (err) {
			console.error('Error deleting case:', err);
			return fail(500, { error: 'Failed to delete case' });
		}
	},

	comment: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const body = form.get('body')?.toString().trim();
			const caseId = form.get('caseId')?.toString();

			if (!body || !caseId) {
				return fail(400, { error: 'Comment and case ID are required.' });
			}

			// Create comment via API
			await apiRequest(
				`/cases/comment/${caseId}/`,
				{
					method: 'POST',
					body: { comment: body }
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error creating comment:', err);
			return fail(500, { error: 'Failed to create comment' });
		}
	}
};
