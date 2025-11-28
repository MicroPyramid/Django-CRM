/**
 * Task Detail Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/tasks/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { fail, error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const { task_id } = params;
	const org = locals.org;
	const user = locals.user;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Fetch task details from Django
		const response = await apiRequest(
			`/tasks/${task_id}/`,
			{},
			{ cookies, org }
		);

		if (!response.task_obj) {
			return fail(404, { message: 'Task not found or you do not have permission to view it.' });
		}

		const taskData = response.task_obj;

		// Transform task data
		const task = {
			id: taskData.id,
			title: taskData.title,
			status: taskData.status,
			priority: taskData.priority,
			dueDate: taskData.due_date ? new Date(taskData.due_date).toISOString().split('T')[0] : null,
			createdAt: taskData.created_at,
			updatedAt: taskData.updated_at,

			// Owner
			owner: taskData.assigned_to && taskData.assigned_to.length > 0
				? {
					id: taskData.assigned_to[0].id,
					name: taskData.assigned_to[0].user_details?.email || taskData.assigned_to[0].email,
					profilePhoto: taskData.assigned_to[0].profile_photo || null
				}
				: null,

			// Account
			account: taskData.account ? {
				id: taskData.account.id,
				name: taskData.account.name
			} : null,

			// Comments
			comments: (response.comments || []).map(comment => ({
				id: comment.id,
				body: comment.comment,
				createdAt: comment.created_at,
				author: comment.commented_by ? {
					id: comment.commented_by.id,
					name: comment.commented_by.user_details?.email || comment.commented_by.email,
					profilePhoto: comment.commented_by.profile_photo || null
				} : null
			}))
		};

		// Transform users list
		const users = (response.users || []).map(user => ({
			id: user.id,
			name: user.user_details?.email || user.email,
			profilePhoto: user.profile_photo || null
		}));

		// Transform accounts list
		let accounts = [];
		if (response.accounts_list) {
			accounts = response.accounts_list;
		} else if (response.accounts) {
			accounts = response.accounts;
		}

		const transformedAccounts = accounts.map(account => ({
			id: account.id,
			name: account.name
		}));

		// Logged in user info
		const loggedInUser = user ? {
			id: user.id,
			name: user.name,
			profilePhoto: user.profilePhoto || null
		} : null;

		return {
			task,
			users,
			accounts: transformedAccounts,
			loggedInUser
		};
	} catch (err) {
		console.error('Error loading task data:', err);
		throw error(500, `Failed to load task: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	addComment: async ({ request, params, locals, cookies }) => {
		const org = locals.org;
		const formData = await request.formData();
		const commentBody = formData.get('commentBody')?.toString();
		const { task_id } = params;

		if (!commentBody || commentBody.trim() === '') {
			return fail(400, { error: true, message: 'Comment body cannot be empty.', commentBody });
		}

		try {
			// Add comment via API - comments are added via TaskDetailView.post()
			await apiRequest(
				`/tasks/${task_id}/`,
				{
					method: 'POST',
					body: { comment: commentBody }
				},
				{ cookies, org }
			);

			return { success: true, message: 'Comment added successfully.' };
		} catch (err) {
			console.error('Error adding comment:', err);
			return fail(500, { error: true, message: 'Failed to add comment.' });
		}
	}
};
