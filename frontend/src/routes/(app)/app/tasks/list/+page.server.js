/**
 * Tasks List Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/tasks/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
	const user = locals.user;
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Build query parameters for tasks
		const queryParams = buildQueryParams({
			page: 1,
			limit: 1000, // Get all tasks without pagination
			sort: 'created_at',
			order: 'desc'
		});

		// Fetch tasks from Django API
		const response = await apiRequest(
			`/tasks/?${queryParams.toString()}`,
			{},
			{ cookies, org }
		);

		// Handle Django response structure
		// Django TaskListView returns { tasks: [...], tasks_count: ..., ... }
		let tasks = [];
		if (response.tasks) {
			tasks = response.tasks;
		} else if (Array.isArray(response)) {
			tasks = response;
		} else if (response.results) {
			tasks = response.results;
		}

		// Transform Django tasks to Prisma structure
		const transformedTasks = tasks.map((task) => ({
			id: task.id,
			subject: task.title,
			description: task.description,
			status: task.status,
			priority: task.priority,
			dueDate: task.due_date,
			createdAt: task.created_at,
			updatedAt: task.updated_at,

			// Owner (first assigned user)
			owner: task.assigned_to && task.assigned_to.length > 0
				? {
					id: task.assigned_to[0].id,
					name: task.assigned_to[0].user_details?.email || task.assigned_to[0].email
				}
				: task.created_by
					? {
						id: task.created_by.id,
						name: task.created_by.email
					}
					: null,

			// Account
			account: task.account ? {
				id: task.account.id,
				name: task.account.name
			} : null
		}));

		return {
			tasks: transformedTasks
		};
	} catch (err) {
		console.error('Error loading tasks from API:', err);
		throw error(500, `Failed to load tasks: ${err.message}`);
	}
}
