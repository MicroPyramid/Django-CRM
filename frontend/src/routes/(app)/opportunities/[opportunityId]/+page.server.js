/**
 * Opportunity Detail Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/opportunities/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Fetch opportunity details from Django
		const response = await apiRequest(
			`/opportunities/${params.opportunityId}/`,
			{},
			{ cookies, org }
		);

		if (!response.opportunity_obj) {
			throw error(404, 'Opportunity not found');
		}

		const oppData = response.opportunity_obj;

		// Transform opportunity data
		const opportunity = {
			id: oppData.id,
			name: oppData.name,
			amount: oppData.amount ? Number(oppData.amount) : null,
			expectedRevenue: oppData.expected_revenue ? Number(oppData.expected_revenue) : null,
			stage: oppData.stage,
			probability: oppData.probability,
			leadSource: oppData.lead_source,
			description: oppData.description,
			closedOn: oppData.closed_on,
			createdAt: oppData.created_at,
			updatedAt: oppData.updated_at,

			// Account
			account: oppData.account
				? {
						id: oppData.account.id,
						name: oppData.account.name,
						email: oppData.account.email,
						phone: oppData.account.phone,
						industry: oppData.account.industry
					}
				: null,

			// Owner
			owner:
				oppData.assigned_to && oppData.assigned_to.length > 0
					? {
							id: oppData.assigned_to[0].id,
							name: oppData.assigned_to[0].user_details?.email || oppData.assigned_to[0].email,
							email: oppData.assigned_to[0].user_details?.email || oppData.assigned_to[0].email
						}
					: oppData.created_by
						? {
								id: oppData.created_by.id,
								name: oppData.created_by.email,
								email: oppData.created_by.email
							}
						: null
		};

		// Account data (for compatibility)
		const account = opportunity.account;
		const owner = opportunity.owner;

		return {
			opportunity,
			account,
			owner
		};
	} catch (err) {
		console.error('Error loading opportunity data:', err);
		throw error(500, `Failed to load opportunity: ${err.message}`);
	}
}
