/**
 * Opportunities List Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/opportunities/
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies, url }) {
	const userId = locals.user?.id;
	const org = locals.org;

	if (!userId) {
		return {
			opportunities: [],
			stats: { total: 0, totalValue: 0, wonValue: 0, pipeline: 0 },
			options: { accounts: [], contacts: [], users: [], teams: [], tags: [] },
			filters: {}
		};
	}

	if (!org) {
		throw error(401, 'Organization context required');
	}

	// Parse pagination params from URL
	const page = parseInt(url.searchParams.get('page') || '1');
	const limit = parseInt(url.searchParams.get('limit') || '10');

	// Parse filter params from URL
	const filters = {
		search: url.searchParams.get('search') || '',
		stage: url.searchParams.get('stage') || '',
		account: url.searchParams.get('account') || '',
		assigned_to: url.searchParams.getAll('assigned_to'),
		tags: url.searchParams.getAll('tags'),
		created_at_gte: url.searchParams.get('created_at_gte') || '',
		created_at_lte: url.searchParams.get('created_at_lte') || '',
		closed_on_gte: url.searchParams.get('closed_on_gte') || '',
		closed_on_lte: url.searchParams.get('closed_on_lte') || ''
	};

	try {
		// Build query parameters for Django API
		const queryParams = buildQueryParams({});
		queryParams.append('limit', limit.toString());
		queryParams.append('offset', ((page - 1) * limit).toString());

		// Add filter params
		if (filters.search) queryParams.append('search', filters.search);
		if (filters.stage) queryParams.append('stage', filters.stage);
		if (filters.account) queryParams.append('account', filters.account);
		filters.assigned_to.forEach((id) => queryParams.append('assigned_to', id));
		filters.tags.forEach((id) => queryParams.append('tags', id));
		if (filters.created_at_gte) queryParams.append('created_at__gte', filters.created_at_gte);
		if (filters.created_at_lte) queryParams.append('created_at__lte', filters.created_at_lte);
		if (filters.closed_on_gte) queryParams.append('closed_on__gte', filters.closed_on_gte);
		if (filters.closed_on_lte) queryParams.append('closed_on__lte', filters.closed_on_lte);

		const queryString = queryParams.toString();

		// Fetch opportunities and teams/users from Django API in parallel
		const [response, teamsUsersResponse] = await Promise.all([
			apiRequest(`/opportunities/${queryString ? `?${queryString}` : ''}`, {}, { cookies, org }),
			apiRequest('/users/get-teams-and-users/', {}, { cookies, org }).catch((err) => {
				console.error('Failed to fetch teams/users:', err);
				return { teams: [], profiles: [] };
			})
		]);

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

		// Extract users (profiles) from teams/users response
		const users = (teamsUsersResponse.profiles || []).map((profile) => ({
			id: profile.id,
			name: profile.user_details?.email || profile.email || 'Unknown',
			email: profile.user_details?.email || profile.email
		}));

		// Extract teams from teams/users response
		const teams = (teamsUsersResponse.teams || []).map((team) => ({
			id: team.id,
			name: team.name
		}));

		// Transform Django opportunities with all fields
		const transformedOpportunities = opportunities.map((opp) => ({
			id: opp.id,
			name: opp.name,
			amount: opp.amount ? Number(opp.amount) : null,
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

		// Get total count from response
		const total = response.opportunities_count || response.count || transformedOpportunities.length;

		return {
			opportunities: transformedOpportunities,
			pagination: {
				page,
				limit,
				total,
				totalPages: Math.ceil(total / limit) || 1
			},
			stats,
			options: {
				accounts,
				contacts,
				tags,
				users,
				teams
			},
			filters
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

			// Build opportunity data only for fields that are present in the form
			// This prevents overwriting existing values with nulls during inline edits
			/** @type {Record<string, any>} */
			const opportunityData = {};

			// Simple string fields
			if (formData.has('name')) {
				opportunityData.name = formData.get('name')?.toString() || '';
			}
			if (formData.has('stage')) {
				opportunityData.stage = formData.get('stage')?.toString() || 'PROSPECTING';
			}
			if (formData.has('opportunityType')) {
				opportunityData.opportunity_type = formData.get('opportunityType')?.toString() || null;
			}
			if (formData.has('currency')) {
				opportunityData.currency = formData.get('currency')?.toString() || null;
			}
			if (formData.has('leadSource')) {
				opportunityData.lead_source = formData.get('leadSource')?.toString() || null;
			}
			if (formData.has('closedOn')) {
				opportunityData.closed_on = formData.get('closedOn')?.toString() || null;
			}
			if (formData.has('description')) {
				opportunityData.description = formData.get('description')?.toString() || '';
			}
			if (formData.has('accountId')) {
				opportunityData.account = formData.get('accountId')?.toString() || null;
			}

			// Number fields
			if (formData.has('amount')) {
				opportunityData.amount = formData.get('amount') ? Number(formData.get('amount')) : null;
			}
			if (formData.has('probability')) {
				opportunityData.probability = formData.get('probability')
					? Number(formData.get('probability'))
					: 0;
			}

			// Array fields (M2M relationships)
			if (formData.has('contacts')) {
				opportunityData.contacts = parseJsonArray(formData, 'contacts');
			}
			if (formData.has('assignedTo')) {
				opportunityData.assigned_to = parseJsonArray(formData, 'assignedTo');
			}
			if (formData.has('teams')) {
				opportunityData.teams = parseJsonArray(formData, 'teams');
			}
			if (formData.has('tags')) {
				opportunityData.tags = parseJsonArray(formData, 'tags');
			}

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
