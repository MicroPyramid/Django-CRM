/**
 * Dashboard Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/dashboard/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
	const userId = locals.user?.id;
	const org = locals.org;

	if (!userId || !org) {
		return {
			error: 'User not authenticated'
		};
	}

	try {
		// Fetch dashboard data from Django API
		const dashboardResponse = await apiRequest('/dashboard/', {}, { cookies, org });

		// Django returns:
		// {
		//   accounts_count, contacts_count, leads_count, opportunities_count,
		//   accounts: [], contacts: [], leads: [], opportunities: []
		// }

		// Transform recent leads
		const recentLeads = (dashboardResponse.leads || []).slice(0, 5).map((lead) => ({
			id: lead.id,
			firstName: lead.first_name,
			lastName: lead.last_name,
			company: lead.account_name,
			status: lead.status,
			createdAt: lead.created_on
		}));

		// Transform recent opportunities
		const recentOpportunities = (dashboardResponse.opportunities || []).slice(0, 5).map((opp) => ({
			id: opp.id,
			name: opp.name,
			amount: opp.amount ? parseFloat(opp.amount) : null,
			stage: opp.stage,
			probability: opp.probability ? parseFloat(opp.probability) : null,
			createdAt: opp.created_on,
			account: opp.account
				? {
						name: opp.account.name
					}
				: null
		}));

		// Calculate opportunity revenue (sum of all opportunity amounts)
		const opportunityRevenue = (dashboardResponse.opportunities || []).reduce(
			(sum, opp) => sum + (opp.amount ? parseFloat(opp.amount) : 0),
			0
		);

			// Fetch tasks and activities separately
		let upcomingTasks = [];
		let recentActivities = [];

		try {
			// Fetch tasks separately - filter for current user's pending tasks
			const tasksResponse = await apiRequest('/tasks/', {}, { cookies, org });
			// Django TaskListView returns { tasks: [...], tasks_count: ..., ... }
			const allTasks = tasksResponse.tasks || tasksResponse.results || [];

			// Filter for user's pending tasks with due dates
			upcomingTasks = allTasks
				.filter((task) => {
					const isAssignedToUser =
						task.assigned_to && task.assigned_to.some((id) => id === userId);
					const isNotCompleted = task.status !== 'Completed';
					const hasDueDate = task.due_date;
					return isAssignedToUser && isNotCompleted && hasDueDate;
				})
				.sort((a, b) => {
					const dateA = new Date(a.due_date);
					const dateB = new Date(b.due_date);
					return dateA - dateB;
				})
				.slice(0, 5)
				.map((task) => ({
					id: task.id,
					subject: task.title,
					status: task.status,
					priority: task.priority,
					dueDate: task.due_date
				}));
		} catch (err) {
			console.error('Error fetching tasks for dashboard:', err);
		}

		try {
			// Fetch recent activities from Django API
			const activitiesResponse = await apiRequest('/activities/?limit=10', {}, { cookies, org });

			// Transform activities to match frontend format
			// Django returns: { error: false, count: N, activities: [...] }
			recentActivities = (activitiesResponse.activities || []).map((activity) => ({
				id: activity.id,
				user: {
					name: activity.user?.name || activity.user?.email?.split('@')[0] || 'Unknown'
				},
				action: activity.action,
				entityType: activity.entity_type,
				entityId: activity.entity_id,
				entityName: activity.entity_name,
				description: activity.description || `${activity.action_display} ${activity.entity_type}: ${activity.entity_name}`,
				timestamp: activity.timestamp,
				humanizedTime: activity.humanized_time
			}));
		} catch (err) {
			console.error('Error fetching activities for dashboard:', err);
		}

		// Count pending tasks for the user
		const pendingTasks = upcomingTasks.length;

		return {
			metrics: {
				totalLeads: dashboardResponse.leads_count || 0,
				totalOpportunities: dashboardResponse.opportunities_count || 0,
				totalAccounts: dashboardResponse.accounts_count || 0,
				totalContacts: dashboardResponse.contacts_count || 0,
				pendingTasks: pendingTasks,
				opportunityRevenue: opportunityRevenue
			},
			recentData: {
				leads: recentLeads,
				opportunities: recentOpportunities,
				tasks: upcomingTasks,
				activities: recentActivities
			}
		};
	} catch (error) {
		console.error('Dashboard load error:', error);
		return {
			error: 'Failed to load dashboard data'
		};
	}
}
