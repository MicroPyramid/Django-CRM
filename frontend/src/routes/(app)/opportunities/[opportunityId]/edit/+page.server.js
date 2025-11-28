/**
 * Opportunity Edit Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: PUT/PATCH /api/opportunities/{id}/
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
			amount: oppData.amount ? parseFloat(oppData.amount) : null,
			expectedRevenue: oppData.expected_revenue ? parseFloat(oppData.expected_revenue) : null,
			stage: oppData.stage || 'PROSPECTING',
			probability: oppData.probability ? parseFloat(oppData.probability) : null,
			closeDate: oppData.closed_on || null,
			leadSource: oppData.lead_source || null,
			forecastCategory: oppData.forecast_category || null,
			type: oppData.opportunity_type || null,
			nextStep: oppData.next_step || null,
			description: oppData.description || null
		};

		// Extract account and owner info
		const account = oppData.account
			? {
					id: oppData.account.id,
					name: oppData.account.name
				}
			: null;

		const owner = oppData.assigned_to_details?.[0]
			? {
					id: oppData.assigned_to_details[0].id,
					name: oppData.assigned_to_details[0].user_details?.email || oppData.assigned_to_details[0].email
				}
			: null;

		return {
			opportunity,
			account,
			owner
		};
	} catch (err) {
		console.error('Error loading opportunity for edit:', err);
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

		const form = await request.formData();

		// Extract form fields
		const name = form.get('name')?.toString().trim();
		const amountStr = form.get('amount')?.toString();
		const amount = amountStr ? parseFloat(amountStr) : null;
		const expectedRevenueStr = form.get('expectedRevenue')?.toString();
		const expectedRevenue = expectedRevenueStr ? parseFloat(expectedRevenueStr) : null;
		const stage = form.get('stage')?.toString();
		const probabilityStr = form.get('probability')?.toString();
		const probability = probabilityStr ? parseFloat(probabilityStr) : null;
		const closeDateValue = form.get('closeDate')?.toString();
		const closeDate = closeDateValue || null;
		const leadSource = form.get('leadSource')?.toString() || null;
		const forecastCategory = form.get('forecastCategory')?.toString() || null;
		const type = form.get('type')?.toString() || null;
		const nextStep = form.get('nextStep')?.toString() || null;
		const description = form.get('description')?.toString() || null;

		// Validation
		const errors = {};

		if (!name || name.length === 0) {
			errors.name = 'Opportunity name is required';
		}

		if (!stage) {
			errors.stage = 'Stage is required';
		}

		// Validate stage is a valid enum value
		const validStages = [
			'PROSPECTING',
			'QUALIFICATION',
			'PROPOSAL',
			'NEGOTIATION',
			'CLOSED_WON',
			'CLOSED_LOST'
		];
		if (stage && !validStages.includes(stage)) {
			errors.stage = 'Invalid stage selected';
		}

		// Validate probability range
		if (probability !== null && (probability < 0 || probability > 100)) {
			errors.probability = 'Probability must be between 0 and 100';
		}

		// Validate amounts are not negative
		if (amount !== null && amount < 0) {
			errors.amount = 'Amount cannot be negative';
		}

		if (expectedRevenue !== null && expectedRevenue < 0) {
			errors.expectedRevenue = 'Expected revenue cannot be negative';
		}

		if (Object.keys(errors).length > 0) {
			return fail(400, {
				errors,
				values: {
					name,
					amount,
					expectedRevenue,
					stage,
					probability,
					closeDate,
					leadSource,
					forecastCategory,
					type,
					nextStep,
					description
				}
			});
		}

		try {
			// Transform to Django field names
			const djangoData = {
				name: name,
				amount: amount,
				expected_revenue: expectedRevenue,
				stage: stage,
				probability: probability,
				closed_on: closeDate,
				lead_source: leadSource,
				forecast_category: forecastCategory,
				opportunity_type: type,
				next_step: nextStep,
				description: description
			};

			// Update opportunity via API
			await apiRequest(
				`/opportunities/${params.opportunityId}/`,
				{
					method: 'PUT',
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

			console.error('Error updating opportunity:', err);
			return fail(500, {
				error:
					'Failed to update opportunity: ' + (err instanceof Error ? err.message : 'Unknown error'),
				values: {
					name,
					amount,
					expectedRevenue,
					stage,
					probability,
					closeDate,
					leadSource,
					forecastCategory,
					type,
					nextStep,
					description
				}
			});
		}
	}
};
