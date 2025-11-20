/**
 * Case Create Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: POST /api/cases/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, url, cookies }) {
	const org = locals.org;
	const preSelectedAccountId = url.searchParams.get('accountId');

	try {
		// Fetch accounts and users in parallel
		const [accountsResponse, usersResponse] = await Promise.all([
			apiRequest('/accounts/', {}, { cookies, org }),
			apiRequest('/users/', {}, { cookies, org })
		]);

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

		// Transform users
		// Django UsersListView returns { active_users: { active_users: [...] }, ... }
		const activeUsersList = usersResponse.active_users?.active_users || [];
		const users = activeUsersList.map((user) => ({
			user: {
				id: user.id,
				name: user.user_details?.email || user.email
			}
		}));

		return {
			accounts: transformedAccounts,
			users,
			preSelectedAccountId
		};
	} catch (err) {
		console.error('Error loading case create page:', err);
		return {
			accounts: [],
			users: [],
			preSelectedAccountId
		};
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	create: async ({ request, locals, cookies }) => {
		const org = locals.org;
		const form = await request.formData();

		const subject = form.get('title')?.toString().trim();
		const description = form.get('description')?.toString().trim();
		const accountId = form.get('accountId')?.toString();
		const dueDateValue = form.get('dueDate');
		const dueDate = dueDateValue ? dueDateValue.toString() : null;
		const priority = form.get('priority')?.toString() || 'Normal';
		const ownerId = form.get('assignedId')?.toString();

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
				values: {
					subject,
					description,
					accountId,
					dueDate,
					priority,
					ownerId
				}
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
				assigned_to: [ownerId],
				status: 'New'
			};

			// Create case via API
			const response = await apiRequest(
				'/cases/',
				{
					method: 'POST',
					body: djangoData
				},
				{ cookies, org }
			);

			const caseId = response.id || response.cases_obj?.id;

			if (caseId) {
				throw redirect(303, `/app/cases/${caseId}`);
			} else {
				throw redirect(303, '/app/cases');
			}
		} catch (err) {
			// Check if this is a redirect
			if (err?.status === 303) {
				throw err;
			}

			console.error('Error creating case:', err);
			return fail(500, {
				error: 'Failed to create case: ' + (err instanceof Error ? err.message : 'Unknown error'),
				values: {
					subject,
					description,
					accountId,
					dueDate,
					priority,
					ownerId
				}
			});
		}
	}
};
