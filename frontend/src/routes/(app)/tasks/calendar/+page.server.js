/**
 * Calendar Page (Tasks with Due Dates) - API Version
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
		// Build query parameters - filter tasks with due dates
		const queryParams = buildQueryParams({
			page: 1,
			limit: 1000,
			sort: 'due_date',
			order: 'asc'
		});

		// Fetch tasks from Django API
		const response = await apiRequest(
			`/tasks/?${queryParams.toString()}`,
			{},
			{ cookies, org }
		);

		// Handle Django response structure
		// Django TaskListView returns { tasks: [...], tasks_count: ..., ... }
		let allTasks = [];
		if (response.tasks) {
			allTasks = response.tasks;
		} else if (Array.isArray(response)) {
			allTasks = response;
		} else if (response.results) {
			allTasks = response.results;
		}

		// Filter tasks with due dates only (Django might return all tasks)
		const tasksWithDueDates = allTasks.filter(task => task.due_date !== null);

		// Transform Django tasks to Prisma structure
		const transformedTasks = tasksWithDueDates.map((task) => ({
			id: task.id,
			subject: task.title,
			description: task.description || '',
			dueDate: task.due_date,
			status: task.status,
			priority: task.priority,
			createdAt: task.created_at,
			updatedAt: task.updated_at
		}));

		return {
			tasks: transformedTasks
		};
	} catch (err) {
		console.error('Error loading calendar tasks from API:', err);
		throw error(500, `Failed to load calendar tasks: ${err.message}`);
	}
}
