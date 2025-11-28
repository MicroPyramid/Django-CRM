/**
 * Accounts List Page - API Version
 *
 * This is the migrated version that uses Django REST API instead of Prisma.
 * Once tested and working, activate by:
 *   1. mv +page.server.js +page.server.prisma.js
 *   2. mv +page.server.api.js +page.server.js
 *
 * Migration completed: 2025-11-19
 * Django endpoint: GET /api/accounts/
 */

import { error } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, url, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	// Extract URL parameters (same as Prisma version)
	const page = parseInt(url.searchParams.get('page') || '1');
	const limit = parseInt(url.searchParams.get('limit') || '10');
	const sort = url.searchParams.get('sort') || 'name';
	const order = url.searchParams.get('order') || 'asc';
	const status = url.searchParams.get('status'); // 'open' or 'closed'

	try {
		// Build query parameters for Django
		const queryParams = buildQueryParams({
			page,
			limit,
			sort,
			order
		});

		// Add filters
		const nameFilter = url.searchParams.get('name');
		const cityFilter = url.searchParams.get('city');
		const industryFilter = url.searchParams.get('industry');
		const tagsFilter = url.searchParams.get('tags');

		if (nameFilter) queryParams.append('name', nameFilter);
		if (cityFilter) queryParams.append('city', cityFilter);
		if (industryFilter) queryParams.append('industry', industryFilter);
		if (tagsFilter) queryParams.append('tags', tagsFilter);

		// Make API request
		const response = await apiRequest(
			`/accounts/?${queryParams.toString()}`,
			{},
			{ cookies, org }
		);

		// Django returns complex structure with active_accounts and closed_accounts
		// We need to extract based on status filter
		let accounts = [];
		let total = 0;

		if (response.active_accounts && response.closed_accounts) {
			// Django endpoint returns separate lists
			if (status === 'open' || !status) {
				accounts = response.active_accounts.open_accounts || [];
				total = accounts.length; // Django doesn't provide count in this format
			} else if (status === 'closed') {
				accounts = response.closed_accounts.close_accounts || [];
				total = accounts.length;
			}
		} else if (response.results) {
			// Standard Django pagination response
			accounts = response.results;
			total = response.count || 0;
		}

		// Transform Django accounts to match SvelteKit expectations
		const transformedAccounts = accounts.map((account) => {
			// Calculate counts from related data
			const opportunityCount = account.opportunities?.length || 0;
			const contactCount = account.contacts?.length || 0;
			const taskCount = account.tasks?.length || 0;

			const openOpportunities = account.opportunities?.filter(
				(opp) => !['CLOSED_WON', 'CLOSED_LOST'].includes(opp.stage)
			).length || 0;

			const totalOpportunityValue = account.opportunities?.reduce(
				(sum, opp) => sum + (parseFloat(opp.amount) || 0),
				0
			) || 0;

			return {
				id: account.id,
				name: account.name,
				email: account.email,
				phone: account.phone,
				website: account.website,
				industry: account.industry,
				description: account.description,
				isActive: account.status === 'open' || account.is_active === true,
				createdAt: account.created_at,
				updatedAt: account.updated_at || account.created_at,

				// Address fields (Django uses separate fields)
				billingAddressLine: account.billing_address_line,
				billingStreet: account.billing_street,
				billingCity: account.billing_city,
				billingState: account.billing_state,
				billingPostcode: account.billing_postcode,
				billingCountry: account.billing_country,

				// Owner - Django returns assigned_to array
				owner: account.assigned_to && account.assigned_to.length > 0
					? {
							id: account.assigned_to[0].id,
							name: account.assigned_to[0].user_details?.email || 'Unknown',
							email: account.assigned_to[0].user_details?.email,
							profilePhoto: account.assigned_to[0].user_details?.profile_pic
						}
					: account.created_by
						? {
								id: account.created_by.id,
								name: account.created_by.email,
								email: account.created_by.email,
								profilePhoto: account.created_by.profile_pic
							}
						: null,

				// Aggregated data
				opportunityCount,
				contactCount,
				taskCount,
				openOpportunities,
				totalOpportunityValue,

				// Top contacts for display
				topContacts: account.contacts?.slice(0, 3).map((contact) => ({
					id: contact.id,
					name: `${contact.first_name || ''} ${contact.last_name || ''}`.trim()
				})) || [],

				// Tags
				tags: account.tags || []
			};
		});

		return {
			accounts: transformedAccounts,
			pagination: {
				page,
				limit,
				total,
				totalPages: Math.ceil(total / limit) || 1
			}
		};
	} catch (err) {
		console.error('Error fetching accounts from API:', err);
		throw error(500, `Failed to fetch accounts: ${err.message}`);
	}
}
