/**
 * Opportunity Delete Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: DELETE /api/opportunities/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const userId = locals.user?.id;
	const org = locals.org;

	if (!userId || !org) {
		throw error(401, 'Unauthorized');
	}

	try {
		const response = await apiRequest(
			`/opportunities/${params.opportunityId}/`,
			{},
			{ cookies, org }
		);

		if (!response.opportunity_obj) {
			throw error(404, 'Opportunity not found');
		}

		const oppData = response.opportunity_obj;

		// Transform to Prisma structure
		const opportunity = {
			id: oppData.id,
			name: oppData.name,
			amount: oppData.amount ? parseFloat(oppData.amount) : null,
			stage: oppData.stage,
			account: oppData.account
				? {
						id: oppData.account.id,
						name: oppData.account.name
					}
				: null,
			owner: oppData.assigned_to_details?.[0]
				? {
						id: oppData.assigned_to_details[0].id,
						name: oppData.assigned_to_details[0].user_details?.email || oppData.assigned_to_details[0].email,
						email: oppData.assigned_to_details[0].user_details?.email || oppData.assigned_to_details[0].email
					}
				: null
		};

		return { opportunity };
	} catch (err) {
		console.error('Error loading opportunity for delete:', err);
		throw error(500, `Failed to load opportunity: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ params, locals, cookies }) => {
		try {
			const userId = locals.user?.id;
			const org = locals.org;

			if (!userId || !org) {
				return fail(401, { message: 'Unauthorized' });
			}

			// Delete the opportunity via API
			await apiRequest(
				`/opportunities/${params.opportunityId}/`,
				{
					method: 'DELETE'
				},
				{ cookies, org }
			);

			// Return success response - let client handle redirect
			return { success: true, message: 'Opportunity deleted successfully' };
		} catch (err) {
			console.error('Error deleting opportunity:', err);
			return fail(500, {
				message: 'Failed to delete opportunity: ' + (err instanceof Error ? err.message : 'Unknown error')
			});
		}
	}
};
