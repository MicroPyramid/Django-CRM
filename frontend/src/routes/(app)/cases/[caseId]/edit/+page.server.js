/**
 * Case Edit Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: PUT/PATCH /api/cases/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { fail, redirect, error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Fetch case, users, and accounts in parallel
		const [caseResponse, usersResponse, accountsResponse] = await Promise.all([
			apiRequest(`/cases/${params.caseId}/`, {}, { cookies, org }),
			apiRequest('/users/', {}, { cookies, org }),
			apiRequest('/accounts/', {}, { cookies, org })
		]);

		if (!caseResponse.cases_obj) {
			throw error(404, 'Case not found');
		}

		const caseData = caseResponse.cases_obj;

		// Transform case to Prisma structure
		const caseItem = {
			id: caseData.id,
			subject: caseData.name,
			description: caseData.description,
			accountId: caseData.account?.id || null,
			dueDate: caseData.closed_on || null,
			priority: caseData.priority || 'Normal',
			ownerId: caseData.assigned_to?.[0]?.id || caseData.assigned_to?.[0] || null,
			status: caseData.status || 'New',
			closedAt: caseData.closed_on || null,
			caseType: caseData.case_type || null,
			// Include related data
			owner: caseData.assigned_to_details?.[0]
				? {
						id: caseData.assigned_to_details[0].id,
						name:
							caseData.assigned_to_details[0].user_details?.email ||
							caseData.assigned_to_details[0].email
					}
				: null,
			account: caseData.account
				? {
						id: caseData.account.id,
						name: caseData.account.name
					}
				: null
		};

		// Transform users
		// Django UsersListView returns { active_users: { active_users: [...] }, ... }
		const activeUsersList = usersResponse.active_users?.active_users || [];
		const users = activeUsersList.map((user) => ({
			id: user.id,
			name: user.user_details?.email || user.email
		}));

		// Transform accounts
		let accounts = [];
		if (accountsResponse.results) {
			accounts = accountsResponse.results;
		} else if (accountsResponse.active_accounts?.open_accounts) {
			accounts = accountsResponse.active_accounts.open_accounts;
		}

		const transformedAccounts = accounts.map((acc) => ({
			id: acc.id,
			name: acc.name
		}));

		return {
			caseItem,
			users,
			accounts: transformedAccounts
		};
	} catch (err) {
		console.error('Error loading case for edit:', err);
		throw error(500, `Failed to load case: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	update: async ({ request, params, locals, cookies }) => {
		const org = locals.org;
		const form = await request.formData();

		// Extract form fields
		const subject = form.get('title')?.toString().trim();
		const description = form.get('description')?.toString().trim();
		const accountId = form.get('accountId')?.toString();
		const dueDateRaw = form.get('dueDate');
		const dueDate = dueDateRaw ? dueDateRaw.toString() : null;
		const priority = form.get('priority')?.toString() || 'Normal';
		const ownerId = form.get('assignedId')?.toString();
		const status = form.get('status')?.toString() || 'New';

		// Validation
		const errors = {};

		if (!subject || subject.length === 0) {
			errors.subject = 'Subject is required';
		}

		if (!accountId) {
			errors.accountId = 'Account is required';
		}

		if (!ownerId) {
			errors.ownerId = 'Owner is required';
		}

		if (Object.keys(errors).length > 0) {
			return fail(400, {
				errors,
				values: { subject, description, accountId, dueDate, priority, ownerId }
			});
		}

		try {
			// Transform to Django field names
			const djangoData = {
				name: subject,
				description: description || null,
				account: accountId,
				closed_on: dueDate,
				priority: priority,
				status: status,
				assigned_to: [ownerId]
			};

			// Update case via API
			await apiRequest(
				`/cases/${params.caseId}/`,
				{
					method: 'PUT',
					body: djangoData
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error updating case:', err);
			return fail(500, {
				error: 'Failed to update case: ' + (err instanceof Error ? err.message : 'Unknown error'),
				values: { subject, description, accountId, dueDate, priority, ownerId }
			});
		}
	},

	close: async ({ params, locals, cookies }) => {
		const org = locals.org;

		try {
			// Close case via API
			await apiRequest(
				`/cases/${params.caseId}/`,
				{
					method: 'PATCH',
					body: {
						status: 'Closed',
						closed_on: new Date().toISOString()
					}
				},
				{ cookies, org }
			);

			throw redirect(303, `/cases/${params.caseId}`);
		} catch (err) {
			// Check if this is a redirect
			if (err?.status === 303) {
				throw err;
			}

			console.error('Error closing case:', err);
			return fail(500, {
				error: 'Failed to close case: ' + (err instanceof Error ? err.message : 'Unknown error')
			});
		}
	},

	reopen: async ({ params, locals, cookies }) => {
		const org = locals.org;

		try {
			// Reopen case via API
			await apiRequest(
				`/cases/${params.caseId}/`,
				{
					method: 'PATCH',
					body: {
						status: 'New',
						closed_on: null
					}
				},
				{ cookies, org }
			);

			throw redirect(303, `/cases/${params.caseId}`);
		} catch (err) {
			// Check if this is a redirect
			if (err?.status === 303) {
				throw err;
			}

			console.error('Error reopening case:', err);
			return fail(500, {
				error: 'Failed to reopen case: ' + (err instanceof Error ? err.message : 'Unknown error')
			});
		}
	}
};
