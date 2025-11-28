/**
 * Opportunity Close Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: PATCH /api/opportunities/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(403, 'Organization access required');
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
			stage: oppData.stage,
			account: oppData.account
				? {
						id: oppData.account.id,
						name: oppData.account.name
					}
				: null
		};

		return { opportunity };
	} catch (err) {
		console.error('Error loading opportunity for close:', err);
		throw error(500, `Failed to load opportunity: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ request, params, locals, cookies }) => {
		const org = locals.org;

		if (!org) {
			return fail(403, { error: 'Organization access required' });
		}

		const formData = await request.formData();
		const status = formData.get('status')?.toString();
		const closeDate = formData.get('closeDate')?.toString();
		const closeReason = formData.get('closeReason')?.toString();

		// Validation
		const errors = {};

		if (!status) {
			errors.status = 'Status is required';
		}

		if (!closeDate) {
			errors.closeDate = 'Close date is required';
		}

		// Validate status
		const validCloseStatuses = ['CLOSED_WON', 'CLOSED_LOST'];
		if (status && !validCloseStatuses.includes(status)) {
			errors.status = 'Invalid status selected';
		}

		if (Object.keys(errors).length > 0) {
			return fail(400, { errors, values: { status, closeDate, closeReason } });
		}

		try {
			// First, get the current opportunity
			const currentResponse = await apiRequest(
				`/opportunities/${params.opportunityId}/`,
				{},
				{ cookies, org }
			);

			if (!currentResponse.opportunity_obj) {
				return fail(404, { error: 'Opportunity not found' });
			}

			const currentOpp = currentResponse.opportunity_obj;

			// Prepare description with close reason appended
			let updatedDescription = currentOpp.description || '';
			if (closeReason) {
				updatedDescription = updatedDescription
					? `${updatedDescription}\n\nClose Reason: ${closeReason}`
					: `Close Reason: ${closeReason}`;
			}

			// Transform to Django field names
			const djangoData = {
				stage: status, // CLOSED_WON or CLOSED_LOST
				closed_on: closeDate,
				description: updatedDescription
			};

			// Update opportunity via API
			await apiRequest(
				`/opportunities/${params.opportunityId}/`,
				{
					method: 'PATCH',
					body: djangoData
				},
				{ cookies, org }
			);

			throw redirect(303, `/opportunities/${params.opportunityId}`);
		} catch (err) {
			// Check if this is a redirect
			if (err?.status === 303) {
				throw err;
			}

			console.error('Error closing opportunity:', err);
			return fail(500, {
				error: 'Failed to close opportunity: ' + (err instanceof Error ? err.message : 'Unknown error'),
				values: { status, closeDate, closeReason }
			});
		}
	}
};
