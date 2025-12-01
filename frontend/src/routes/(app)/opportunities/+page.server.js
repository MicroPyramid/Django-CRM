/**
 * Opportunities List Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/opportunities/
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
	const userId = locals.user?.id;
	const org = locals.org;

	if (!userId) {
		return {
			opportunities: [],
			stats: { total: 0, totalValue: 0, wonValue: 0, pipeline: 0 },
			options: { accounts: [], contacts: [], users: [], teams: [], tags: [] }
		};
	}

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Fetch opportunities from Django API
		const response = await apiRequest('/opportunities/', {}, { cookies, org });

		// Handle Django response structure
		let opportunities = [];
		if (response.opportunities) {
			opportunities = response.opportunities;
		} else if (Array.isArray(response)) {
			opportunities = response;
		} else if (response.results) {
			opportunities = response.results;
		}

		// Extract options from API response
		const accounts = (response.accounts_list || []).map((acc) => ({
			id: acc.id,
			name: acc.name
		}));

		const contacts = (response.contacts_list || []).map((contact) => ({
			id: contact.id,
			name: `${contact.first_name || ''} ${contact.last_name || ''}`.trim(),
			email: contact.email
		}));

		const tags = (response.tags || []).map((tag) => ({
			id: tag.id,
			name: tag.name,
			slug: tag.slug
		}));

		// Transform Django opportunities with all fields
		const transformedOpportunities = opportunities.map((opp) => ({
			id: opp.id,
			name: opp.name,
			amount: opp.amount ? Number(opp.amount) : null,
			expectedRevenue: opp.expected_revenue ? Number(opp.expected_revenue) : null,
			stage: opp.stage,
			opportunityType: opp.opportunity_type,
			currency: opp.currency,
			probability: opp.probability,
			leadSource: opp.lead_source,
			description: opp.description,
			closedOn: opp.closed_on,
			createdAt: opp.created_at,
			updatedAt: opp.updated_at,
			isActive: opp.is_active,
			createdOnArrow: opp.created_on_arrow,

			// Account
			account: opp.account
				? {
						id: opp.account.id,
						name: opp.account.name,
						type: opp.account.type || opp.account.account_type
					}
				: null,

			// Assigned users (multi)
			assignedTo: (opp.assigned_to || []).map((profile) => ({
				id: profile.id,
				name: profile.user_details?.email || profile.email || 'Unknown',
				email: profile.user_details?.email || profile.email
			})),

			// Owner (first assigned user or created_by)
			owner:
				opp.assigned_to && opp.assigned_to.length > 0
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

			// Teams
			teams: (opp.teams || []).map((team) => ({
				id: team.id,
				name: team.name
			})),

			// Contacts
			contacts: (opp.contacts || []).map((contact) => ({
				id: contact.id,
				firstName: contact.first_name,
				lastName: contact.last_name,
				email: contact.email
			})),

			// Tags
			tags: (opp.tags || []).map((tag) => ({
				id: tag.id,
				name: tag.name,
				slug: tag.slug
			})),

			// Closed by
			closedBy: opp.closed_by
				? {
						id: opp.closed_by.id,
						name: opp.closed_by.user_details?.email || opp.closed_by.email
					}
				: null,

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
				.filter((opp) => opp.stage === 'CLOSED_WON')
				.reduce((sum, opp) => sum + (opp.amount || 0), 0),
			pipeline: transformedOpportunities
				.filter((opp) => !['CLOSED_WON', 'CLOSED_LOST'].includes(opp.stage))
				.reduce((sum, opp) => sum + (opp.amount || 0), 0)
		};

		return {
			opportunities: transformedOpportunities,
			stats,
			options: {
				accounts,
				contacts,
				tags,
				users: [], // Users are fetched from teams API if needed
				teams: []
			}
		};
	} catch (err) {
		console.error('Error loading opportunities from API:', err);
		throw error(500, `Failed to load opportunities: ${err.message}`);
	}
}

/**
 * Parse JSON array from form data
 * @param {FormData} formData
 * @param {string} key
 * @returns {string[]}
 */
function parseJsonArray(formData, key) {
	const value = formData.get(key)?.toString();
	if (!value) return [];
	try {
		const parsed = JSON.parse(value);
		return Array.isArray(parsed) ? parsed : [];
	} catch {
		return [];
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	create: async ({ request, locals, cookies }) => {
		try {
			const formData = await request.formData();
			const org = locals.org;

			if (!org) {
				return fail(400, { message: 'Organization context required' });
			}

			// Build opportunity data for Django API with all fields
			const opportunityData = {
				name: formData.get('name')?.toString() || '',
				amount: formData.get('amount') ? Number(formData.get('amount')) : null,
				probability: formData.get('probability') ? Number(formData.get('probability')) : 0,
				stage: formData.get('stage')?.toString() || 'PROSPECTING',
				opportunity_type: formData.get('opportunityType')?.toString() || null,
				currency: formData.get('currency')?.toString() || null,
				lead_source: formData.get('leadSource')?.toString() || null,
				closed_on: formData.get('closedOn')?.toString() || null,
				description: formData.get('description')?.toString() || '',
				account: formData.get('accountId')?.toString() || null,
				contacts: parseJsonArray(formData, 'contacts'),
				assigned_to: parseJsonArray(formData, 'assignedTo'),
				teams: parseJsonArray(formData, 'teams'),
				tags: parseJsonArray(formData, 'tags')
			};

			// Create via API
			await apiRequest(
				'/opportunities/',
				{ method: 'POST', body: opportunityData },
				{ cookies, org }
			);

			return { success: true, message: 'Opportunity created successfully' };
		} catch (err) {
			console.error('Error creating opportunity:', err);
			return fail(500, { message: `Failed to create opportunity: ${err.message}` });
		}
	},

	update: async ({ request, locals, cookies }) => {
		try {
			const formData = await request.formData();
			const opportunityId = formData.get('opportunityId')?.toString();
			const org = locals.org;

			if (!opportunityId || !org) {
				return fail(400, { message: 'Missing required data' });
			}

			// Build opportunity data for Django API with all fields
			const opportunityData = {
				name: formData.get('name')?.toString() || '',
				amount: formData.get('amount') ? Number(formData.get('amount')) : null,
				probability: formData.get('probability') ? Number(formData.get('probability')) : 0,
				stage: formData.get('stage')?.toString() || 'PROSPECTING',
				opportunity_type: formData.get('opportunityType')?.toString() || null,
				currency: formData.get('currency')?.toString() || null,
				lead_source: formData.get('leadSource')?.toString() || null,
				closed_on: formData.get('closedOn')?.toString() || null,
				description: formData.get('description')?.toString() || '',
				account: formData.get('accountId')?.toString() || null,
				contacts: parseJsonArray(formData, 'contacts'),
				assigned_to: parseJsonArray(formData, 'assignedTo'),
				teams: parseJsonArray(formData, 'teams'),
				tags: parseJsonArray(formData, 'tags')
			};

			// Update via API
			await apiRequest(
				`/opportunities/${opportunityId}/`,
				{ method: 'PATCH', body: opportunityData },
				{ cookies, org }
			);

			return { success: true, message: 'Opportunity updated successfully' };
		} catch (err) {
			console.error('Error updating opportunity:', err);
			return fail(500, { message: `Failed to update opportunity: ${err.message}` });
		}
	},

	updateStage: async ({ request, locals, cookies }) => {
		try {
			const formData = await request.formData();
			const opportunityId = formData.get('opportunityId')?.toString();
			const newStage = formData.get('stage')?.toString();
			const org = locals.org;

			if (!opportunityId || !newStage || !org) {
				return fail(400, { message: 'Missing required data' });
			}

			// Update via API with PATCH (partial update)
			await apiRequest(
				`/opportunities/${opportunityId}/`,
				{ method: 'PATCH', body: { stage: newStage } },
				{ cookies, org }
			);

			return { success: true, message: `Stage updated to ${newStage}` };
		} catch (err) {
			console.error('Error updating opportunity stage:', err);
			return fail(500, { message: `Failed to update stage: ${err.message}` });
		}
	},

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
			await apiRequest(`/opportunities/${opportunityId}/`, { method: 'DELETE' }, { cookies, org });

			return { success: true, message: 'Opportunity deleted successfully' };
		} catch (err) {
			console.error('Error deleting opportunity:', err);
			return fail(500, { message: 'Failed to delete opportunity' });
		}
	}
};
