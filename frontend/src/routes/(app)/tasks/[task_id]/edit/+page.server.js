/**
 * Task Edit Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: PUT/PATCH /api/tasks/{id}/
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
		// Fetch task, users, and accounts in parallel
		const [taskResponse, usersResponse, accountsResponse] = await Promise.all([
			apiRequest(`/tasks/${params.task_id}/`, {}, { cookies, org }),
			apiRequest('/users/', {}, { cookies, org }),
			apiRequest('/accounts/', {}, { cookies, org })
		]);

		if (!taskResponse.task_obj) {
			throw redirect(303, '/tasks/list');
		}

		const taskData = taskResponse.task_obj;

		// Format dueDate for input[type=date]
		let formattedDueDate = null;
		if (taskData.due_date) {
			try {
				formattedDueDate = new Date(taskData.due_date).toISOString().split('T')[0];
			} catch (e) {
				formattedDueDate = taskData.due_date;
			}
		}

		// Transform task to Prisma structure
		const task = {
			id: taskData.id,
			subject: taskData.title,
			description: taskData.description,
			status: taskData.status || 'New',
			priority: taskData.priority || 'Medium',
			dueDate: formattedDueDate,
			ownerId: taskData.assigned_to?.[0]?.id || null,
			accountId: taskData.account || null
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
			task,
			users,
			accounts: transformedAccounts
		};
	} catch (err) {
		// Check if this is a redirect
		if (err?.status === 303) {
			throw err;
		}

		console.error('Error loading task for edit:', err);
		throw error(500, `Failed to load task: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	update: async ({ request, params, locals, cookies }) => {
		const formData = await request.formData();
		const org = locals.org;

		const subject = formData.get('subject')?.toString();
		const description = formData.get('description')?.toString();
		const status = formData.get('status')?.toString();
		const priority = formData.get('priority')?.toString();
		let dueDate = formData.get('dueDate')?.toString();
		const ownerId = formData.get('ownerId')?.toString();
		let accountId = formData.get('accountId')?.toString();

		// Validation
		const errors = {};

		if (!subject || subject.trim().length === 0) {
			errors.subject = 'Subject is required';
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
					status,
					priority,
					dueDate,
					ownerId,
					accountId
				}
			});
		}

		try {
			// Clean up accountId
			if (accountId === '' || accountId === 'null') {
				accountId = null;
			}

			// Clean up dueDate
			if (!dueDate || dueDate.trim() === '') {
				dueDate = null;
			}

			// Transform to Django field names
			const djangoData = {
				title: subject.trim(),
				description: description ? description.trim() : null,
				status: status || 'New',
				priority: priority || 'Medium',
				due_date: dueDate,
				assigned_to: ownerId ? [ownerId] : [],
				account: accountId
			};

			// Update task via API
			await apiRequest(
				`/tasks/${params.task_id}/`,
				{
					method: 'PUT',
					body: djangoData
				},
				{ cookies, org }
			);

			throw redirect(303, `/tasks/${params.task_id}`);
		} catch (err) {
			// Check if this is a redirect
			if (err?.status === 303) {
				throw err;
			}

			console.error('Error updating task:', err);
			return fail(500, {
				error: 'Failed to update task: ' + (err instanceof Error ? err.message : 'Unknown error'),
				values: {
					subject,
					description,
					status,
					priority,
					dueDate,
					ownerId,
					accountId
				}
			});
		}
	}
};
