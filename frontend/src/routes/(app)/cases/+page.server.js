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

	try {
		// Get filters from query params
		const status = url.searchParams.get('status') || undefined;
		const assigned = url.searchParams.get('assigned') || undefined;
		const account = url.searchParams.get('account') || undefined;

		// Build query parameters
		const queryParams = buildQueryParams({
			page: 1,
			limit: 1000, // Django doesn't paginate list by default
			sort: 'created_at',
			order: 'desc'
		});

		// Add filters
		if (status) queryParams.append('status', status);
		if (account) queryParams.append('account', account);
		// Django doesn't have direct owner name filter, we'd need to filter by assigned_to ID

		// Fetch cases, users, and accounts in parallel
		const [casesResponse, usersResponse, accountsResponse] = await Promise.all([
			apiRequest(`/cases/?${queryParams.toString()}`, {}, { cookies, org }),
			apiRequest('/users/', {}, { cookies, org }),
			apiRequest('/accounts/', {}, { cookies, org })
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

		// Transform Django cases to Prisma structure
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

			// Owner (first assigned user)
			owner: caseItem.assigned_to && caseItem.assigned_to.length > 0
				? {
					id: caseItem.assigned_to[0].id,
					name: caseItem.assigned_to[0].user_details?.email || caseItem.assigned_to[0].email
				}
				: null,

			// Account
			account: caseItem.account ? {
				id: caseItem.account.id,
				name: caseItem.account.name
			} : null,

			// Comments (Django might not return by default)
			comments: (caseItem.comments || []).map((comment) => ({
				id: comment.id,
				body: comment.comment,
				createdAt: comment.created_at,
				author: comment.commented_by ? {
					id: comment.commented_by.id,
					name: comment.commented_by.user_details?.email || comment.commented_by.email
				} : null
			}))
		}));

		// Transform users list
		// Django UsersListView returns { active_users: { active_users: [...] }, ... }
		const activeUsersList = usersResponse.active_users?.active_users || [];
		const allUsers = activeUsersList.map((user) => ({
			id: user.id,
			name: user.user_details?.email || user.email
		}));

		// Transform accounts list
		let allAccounts = [];
		if (accountsResponse.active_accounts?.open_accounts) {
			allAccounts = accountsResponse.active_accounts.open_accounts;
		} else if (accountsResponse.results) {
			allAccounts = accountsResponse.results;
		} else if (Array.isArray(accountsResponse)) {
			allAccounts = accountsResponse;
		}

		const transformedAccounts = allAccounts.map((account) => ({
			id: account.id,
			name: account.name
		}));

		// Status options from Django
		const statusOptions = ['New', 'Assigned', 'In Progress', 'Closed'];

		return {
			cases: transformedCases,
			allUsers,
			allAccounts: transformedAccounts,
			statusOptions
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
			const ownerId = form.get('assignedId')?.toString();

			if (!name || !accountId || !ownerId) {
				return fail(400, { error: 'Missing required fields.' });
			}

			// Create case via API
			const caseData = {
				name,
				description,
				account: accountId,
				closed_on: closedOn,
				priority,
				assigned_to: [ownerId],
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

			throw redirect(303, `/cases/${newCase.id}`);
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
			const accountId = form.get('accountId')?.toString();
			const dueDateValue = form.get('dueDate');
			const closedOn = dueDateValue ? dueDateValue.toString() : null;
			const priority = form.get('priority')?.toString() || 'Normal';
			const ownerId = form.get('assignedId')?.toString();
			const caseId = form.get('caseId')?.toString();

			if (!name || !accountId || !ownerId || !caseId) {
				return fail(400, { error: 'Missing required fields.' });
			}

			// Update case via API
			const caseData = {
				name,
				description,
				account: accountId,
				closed_on: closedOn,
				priority,
				assigned_to: [ownerId]
			};

			await apiRequest(
				`/cases/${caseId}/`,
				{
					method: 'PUT',
					body: caseData
				},
				{ cookies, org: locals.org }
			);

			throw redirect(303, `/cases/${caseId}`);
		} catch (err) {
			console.error('Error updating case:', err);
			return fail(500, { error: 'Failed to update case' });
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
			await apiRequest(
				`/cases/${caseId}/`,
				{ method: 'DELETE' },
				{ cookies, org: locals.org }
			);

			throw redirect(303, '/cases');
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
