/**
 * Task Create Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: POST /api/tasks/
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
	const urlAccountId = url.searchParams.get('accountId');

	try {
		// Fetch users and accounts in parallel
		const [usersResponse, accountsResponse] = await Promise.all([
			apiRequest('/users/', {}, { cookies, org }),
			apiRequest('/accounts/', {}, { cookies, org })
		]);

		// Transform users
		// Django UsersListView returns { active_users: { active_users: [...] }, ... }
		const activeUsersList = usersResponse.active_users?.active_users || [];
		const users = activeUsersList.map((user) => ({
			id: user.id,
			name: user.user_details?.email || user.email,
			email: user.user_details?.email || user.email
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

		// If accountId is provided in URL, validate it exists
		if (urlAccountId) {
			const accountExists = transformedAccounts.some((account) => account.id === urlAccountId);
			if (!accountExists) {
				throw redirect(303, '/tasks/new');
			}
		}

		return {
			users,
			accounts: transformedAccounts
		};
	} catch (err) {
		// Check if this is a redirect
		if (err?.status === 303) {
			throw err;
		}

		console.error('Error loading task create page:', err);
		return {
			users: [],
			accounts: []
		};
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ request, locals, cookies }) => {
		const { user, org } = locals;

		const formData = await request.formData();

		const subject = formData.get('subject')?.toString();
		const status = formData.get('status')?.toString() || 'New';
		const priority = formData.get('priority')?.toString() || 'Medium';
		const dueDateStr = formData.get('dueDate')?.toString();
		const ownerId = formData.get('ownerId')?.toString();
		let accountId = formData.get('accountId')?.toString();
		const description = formData.get('description')?.toString();

		// Validation
		const errors = {};

		if (!subject || subject.trim().length === 0) {
			errors.subject = 'Subject is required';
		}

		if (!ownerId) {
			errors.ownerId = 'Owner is required';
		}

		// Clean up accountId
		if (accountId && (accountId === '' || accountId === 'null')) {
			accountId = null;
		}

		if (Object.keys(errors).length > 0) {
			return fail(400, {
				errors,
				values: {
					subject,
					status,
					priority,
					dueDate: dueDateStr,
					ownerId,
					accountId,
					description
				}
			});
		}

		try {
			// Transform to Django field names
			const djangoData = {
				title: subject,
				status: status,
				priority: priority,
				due_date: dueDateStr || null,
				description: description || null,
				assigned_to: ownerId ? [ownerId] : [],
				account: accountId || null
			};

			// Create task via API
			const response = await apiRequest(
				'/tasks/',
				{
					method: 'POST',
					body: djangoData
				},
				{ cookies, org }
			);

			const taskId = response.id || response.task_obj?.id;

			// Redirect based on where the task was created from
			if (accountId) {
				// If task was created from an account page, redirect back to that account
				throw redirect(303, `/accounts/${accountId}`);
			} else {
				// Otherwise, redirect to the tasks list or detail if we have taskId
				if (taskId) {
					throw redirect(303, `/tasks/${taskId}`);
				} else {
					throw redirect(303, '/tasks/list');
				}
			}
		} catch (err) {
			// Check if this is a redirect
			if (err?.status === 303) {
				throw err;
			}

			console.error('Error creating task:', err);
			return fail(500, {
				error: 'Failed to create task: ' + (err instanceof Error ? err.message : 'Unknown error'),
				values: {
					subject,
					status,
					priority,
					dueDate: dueDateStr,
					ownerId,
					accountId,
					description
				}
			});
		}
	}
};
