/**
 * Tasks List Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/tasks/
 *
 * Task API fields:
 * - title, status, priority, due_date, description, account
 * - contacts (M2M), teams (M2M), assigned_to (M2M)
 * - created_by, created_at, updated_at
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

		// Fetch tasks, users, accounts, contacts, and teams in parallel
		const [tasksResponse, usersResponse, accountsResponse, contactsResponse, teamsResponse] =
			await Promise.all([
				apiRequest(`/tasks/?${queryParams.toString()}`, {}, { cookies, org }),
				apiRequest('/users/', {}, { cookies, org }),
				apiRequest('/accounts/', {}, { cookies, org }),
				apiRequest('/contacts/', {}, { cookies, org }),
				apiRequest('/teams/', {}, { cookies, org })
			]);

		// Handle Django response structure
		// Django TaskListView returns { tasks: [...], tasks_count: ..., ... }
		let tasks = [];
		if (tasksResponse.tasks) {
			tasks = tasksResponse.tasks;
		} else if (Array.isArray(tasksResponse)) {
			tasks = tasksResponse;
		} else if (tasksResponse.results) {
			tasks = tasksResponse.results;
		}

		// Transform Django tasks to frontend structure
		const transformedTasks = tasks.map((task) => ({
			id: task.id,
			subject: task.title,
			description: task.description,
			status: task.status,
			priority: task.priority,
			dueDate: task.due_date,
			createdAt: task.created_at,
			updatedAt: task.updated_at,

			// All assigned users (M2M)
			assignedTo: (task.assigned_to || []).map((u) => ({
				id: u.id,
				name: u.user_details?.email || u.user?.email || u.email || 'Unknown'
			})),

			// Contacts (M2M)
			contacts: (task.contacts || []).map((c) => ({
				id: c.id,
				name: c.first_name
					? `${c.first_name} ${c.last_name || ''}`.trim()
					: c.email || 'Unknown'
			})),

			// Teams (M2M)
			teams: (task.teams || []).map((t) => ({
				id: t.id,
				name: t.name
			})),

			// Account (FK)
			account: task.account
				? {
						id: task.account.id || task.account,
						name: task.account.name || task.account
					}
				: null,

			// Created by
			createdBy: task.created_by
				? {
						id: task.created_by.id,
						name: task.created_by.email
					}
				: null
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

		// Transform contacts list
		let allContacts = [];
		if (contactsResponse.contact_obj_list) {
			allContacts = contactsResponse.contact_obj_list;
		} else if (contactsResponse.results) {
			allContacts = contactsResponse.results;
		} else if (Array.isArray(contactsResponse)) {
			allContacts = contactsResponse;
		}

		const transformedContacts = allContacts.map((contact) => ({
			id: contact.id,
			name: contact.first_name
				? `${contact.first_name} ${contact.last_name || ''}`.trim()
				: contact.email || 'Unknown'
		}));

		// Transform teams list
		let allTeamsList = [];
		if (teamsResponse.teams) {
			allTeamsList = teamsResponse.teams;
		} else if (teamsResponse.results) {
			allTeamsList = teamsResponse.results;
		} else if (Array.isArray(teamsResponse)) {
			allTeamsList = teamsResponse;
		}

		const allTeams = allTeamsList.map((team) => ({
			id: team.id,
			name: team.name
		}));

		return {
			tasks: transformedTasks,
			allUsers,
			allAccounts: transformedAccounts,
			allContacts: transformedContacts,
			allTeams
		};
	} catch (err) {
		console.error('Error loading tasks from API:', err);
		throw error(500, `Failed to load tasks: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	create: async ({ request, locals, cookies }) => {
		const org = locals.org;

		try {
			const form = await request.formData();
			const subject = form.get('subject')?.toString().trim();
			const description = form.get('description')?.toString().trim();
			const status = form.get('status')?.toString() || 'New';
			const priority = form.get('priority')?.toString() || 'Medium';
			const dueDate = form.get('dueDate')?.toString() || null;
			const accountId = form.get('accountId')?.toString() || null;

			// Parse array fields (sent as JSON strings)
			const assignedToJson = form.get('assignedTo')?.toString() || '[]';
			const contactsJson = form.get('contacts')?.toString() || '[]';
			const teamsJson = form.get('teams')?.toString() || '[]';

			const assignedTo = JSON.parse(assignedToJson);
			const contacts = JSON.parse(contactsJson);
			const teams = JSON.parse(teamsJson);

			if (!subject) {
				return { success: false, error: 'Subject is required' };
			}

			// Transform to Django field names
			const djangoData = {
				title: subject,
				description: description || null,
				status: status,
				priority: priority,
				due_date: dueDate,
				assigned_to: assignedTo,
				contacts: contacts,
				teams: teams,
				account: accountId || null
			};

			await apiRequest(
				'/tasks/',
				{
					method: 'POST',
					body: djangoData
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error creating task:', err);
			return { success: false, error: 'Failed to create task' };
		}
	},

	update: async ({ request, locals, cookies }) => {
		const org = locals.org;

		try {
			const form = await request.formData();
			const taskId = form.get('taskId')?.toString();
			const subject = form.get('subject')?.toString().trim();
			const description = form.get('description')?.toString().trim();
			const status = form.get('status')?.toString() || 'New';
			const priority = form.get('priority')?.toString() || 'Medium';
			const dueDate = form.get('dueDate')?.toString() || null;
			const accountId = form.get('accountId')?.toString() || null;

			// Parse array fields (sent as JSON strings)
			const assignedToJson = form.get('assignedTo')?.toString() || '[]';
			const contactsJson = form.get('contacts')?.toString() || '[]';
			const teamsJson = form.get('teams')?.toString() || '[]';

			const assignedTo = JSON.parse(assignedToJson);
			const contacts = JSON.parse(contactsJson);
			const teams = JSON.parse(teamsJson);

			if (!taskId || !subject) {
				return { success: false, error: 'Task ID and subject are required' };
			}

			// Transform to Django field names
			const djangoData = {
				title: subject,
				description: description || null,
				status: status,
				priority: priority,
				due_date: dueDate,
				assigned_to: assignedTo,
				contacts: contacts,
				teams: teams,
				account: accountId || null
			};

			await apiRequest(
				`/tasks/${taskId}/`,
				{
					method: 'PUT',
					body: djangoData
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error updating task:', err);
			return { success: false, error: 'Failed to update task' };
		}
	},

	complete: async ({ request, locals, cookies }) => {
		const org = locals.org;

		try {
			const form = await request.formData();
			const taskId = form.get('taskId')?.toString();

			if (!taskId) {
				return { success: false, error: 'Task ID is required' };
			}

			// First fetch the task to get current data
			const taskData = await apiRequest(`/tasks/${taskId}/`, { method: 'GET' }, { cookies, org });
			const task = taskData.task_obj;

			// Update with PUT, changing only status to Completed
			await apiRequest(
				`/tasks/${taskId}/`,
				{
					method: 'PUT',
					body: {
						title: task.title,
						status: 'Completed',
						priority: task.priority,
						due_date: task.due_date,
						account: task.account?.id || null,
						assigned_to: (task.assigned_to || []).map((/** @type {any} */ u) => u.id),
						contacts: (task.contacts || []).map((/** @type {any} */ c) => c.id),
						teams: (task.teams || []).map((/** @type {any} */ t) => t.id)
					}
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error completing task:', err);
			return { success: false, error: 'Failed to complete task' };
		}
	},

	reopen: async ({ request, locals, cookies }) => {
		const org = locals.org;

		try {
			const form = await request.formData();
			const taskId = form.get('taskId')?.toString();

			if (!taskId) {
				return { success: false, error: 'Task ID is required' };
			}

			// First fetch the task to get current data
			const taskData = await apiRequest(`/tasks/${taskId}/`, { method: 'GET' }, { cookies, org });
			const task = taskData.task_obj;

			// Update with PUT, changing only status to New
			await apiRequest(
				`/tasks/${taskId}/`,
				{
					method: 'PUT',
					body: {
						title: task.title,
						status: 'New',
						priority: task.priority,
						due_date: task.due_date,
						account: task.account?.id || null,
						assigned_to: (task.assigned_to || []).map((/** @type {any} */ u) => u.id),
						contacts: (task.contacts || []).map((/** @type {any} */ c) => c.id),
						teams: (task.teams || []).map((/** @type {any} */ t) => t.id)
					}
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error reopening task:', err);
			return { success: false, error: 'Failed to reopen task' };
		}
	},

	delete: async ({ request, locals, cookies }) => {
		const org = locals.org;

		try {
			const form = await request.formData();
			const taskId = form.get('taskId')?.toString();

			if (!taskId) {
				return { success: false, error: 'Task ID is required' };
			}

			await apiRequest(`/tasks/${taskId}/`, { method: 'DELETE' }, { cookies, org });

			return { success: true };
		} catch (err) {
			console.error('Error deleting task:', err);
			return { success: false, error: 'Failed to delete task' };
		}
	}
};
