/**
 * Opportunities List Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/opportunities/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
	const userId = locals.user?.id;
	const org = locals.org;

	if (!userId) {
		return {
			opportunities: [],
			stats: {
				total: 0,
				totalValue: 0,
				wonValue: 0,
				pipeline: 0
			}
		};
	}

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Fetch opportunities from Django API
		const response = await apiRequest(
			'/opportunities/',
			{},
			{ cookies, org }
		);

		// Handle Django response structure
		let opportunities = [];
		if (response.opportunities) {
			opportunities = response.opportunities;
		} else if (Array.isArray(response)) {
			opportunities = response;
		} else if (response.results) {
			opportunities = response.results;
		}

		// Transform Django opportunities to Prisma structure
		const transformedOpportunities = opportunities.map((opp) => ({
			id: opp.id,
			name: opp.name,
			amount: opp.amount ? Number(opp.amount) : null,
			expectedRevenue: opp.expected_revenue ? Number(opp.expected_revenue) : null,
			stage: opp.stage,
			probability: opp.probability,
			leadSource: opp.lead_source,
			description: opp.description,
			closedOn: opp.closed_on,
			createdAt: opp.created_at,
			updatedAt: opp.updated_at,

			// Account information
			account: opp.account ? {
				id: opp.account.id,
				name: opp.account.name,
				type: opp.account.type || opp.account.account_type
			} : null,

			// Owner information (assigned_to in Django)
			owner: opp.assigned_to && opp.assigned_to.length > 0
				? {
					id: opp.assigned_to[0].id,
					name: opp.assigned_to[0].user_details?.email || opp.assigned_to[0].email,
					email: opp.assigned_to[0].user_details?.email || opp.assigned_to[0].email
				}
				: opp.created_by
					? {
						id: opp.created_by.id,
						name: opp.created_by.email,
						email: opp.created_by.email
					}
					: null,

			// Contacts
			contacts: (opp.contacts || []).map((contact) => ({
				id: contact.id,
				firstName: contact.first_name,
				lastName: contact.last_name,
				email: contact.email
			})),

			// Counts
			_count: {
				tasks: opp.task_count || 0,
				events: opp.event_count || 0
			}
		}));

		// Calculate stats
		const stats = {
			total: transformedOpportunities.length,
			totalValue: transformedOpportunities.reduce((sum, opp) => sum + (opp.amount || 0), 0),
			wonValue: transformedOpportunities
				.filter(opp => opp.stage === 'CLOSED WON')
				.reduce((sum, opp) => sum + (opp.amount || 0), 0),
			pipeline: transformedOpportunities
				.filter(opp => !['CLOSED WON', 'CLOSED LOST'].includes(opp.stage))
				.reduce((sum, opp) => sum + (opp.amount || 0), 0)
		};

		return {
			opportunities: transformedOpportunities,
			stats
		};
	} catch (err) {
		console.error('Error loading opportunities from API:', err);
		throw error(500, `Failed to load opportunities: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	delete: async ({ request, locals, cookies }) => {
		try {
			const formData = await request.formData();
			const opportunityId = formData.get('opportunityId')?.toString();
			const userId = locals.user?.id;
			const org = locals.org;

			if (!opportunityId || !userId || !org) {
				return fail(400, { message: 'Missing required data' });
			}

			// Delete via API
			await apiRequest(
				`/opportunities/${opportunityId}/`,
				{ method: 'DELETE' },
				{ cookies, org }
			);

			return { success: true, message: 'Opportunity deleted successfully' };
		} catch (err) {
			console.error('Error deleting opportunity:', err);
			return fail(500, { message: 'Failed to delete opportunity' });
		}
	}
};
