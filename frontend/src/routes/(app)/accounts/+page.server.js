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

import { error, fail } from '@sveltejs/kit';
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
		const response = await apiRequest(`/accounts/?${queryParams.toString()}`, {}, { cookies, org });

		// Django returns complex structure with active_accounts and closed_accounts
		// We need to extract based on status filter
		let accounts = [];
		let total = 0;

		if (response.active_accounts && response.closed_accounts) {
			// Django endpoint returns separate lists
			const activeAccounts = response.active_accounts.open_accounts || [];
			const closedAccounts = response.closed_accounts.close_accounts || [];

			if (status === 'open') {
				accounts = activeAccounts;
			} else if (status === 'closed') {
				accounts = closedAccounts;
			} else {
				// No filter - show all accounts (both active and closed)
				accounts = [...activeAccounts, ...closedAccounts];
			}
			total = accounts.length;
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

			const openOpportunities =
				account.opportunities?.filter((opp) => !['CLOSED_WON', 'CLOSED_LOST'].includes(opp.stage))
					.length || 0;

			const totalOpportunityValue =
				account.opportunities?.reduce((sum, opp) => sum + (parseFloat(opp.amount) || 0), 0) || 0;

			return {
				id: account.id,
				name: account.name,
				email: account.email,
				phone: account.phone,
				website: account.website,
				industry: account.industry,
				description: account.description,
				isActive: account.is_active === true,
				createdAt: account.created_at,
				updatedAt: account.updated_at || account.created_at,

				// Address fields (matching API field names)
				addressLine: account.address_line,
				city: account.city,
				state: account.state,
				postcode: account.postcode,
				country: account.country,

				// Business fields
				annualRevenue: account.annual_revenue ? parseFloat(account.annual_revenue) : null,
				numberOfEmployees: account.number_of_employees,

				// Owner - Django returns assigned_to array
				owner:
					account.assigned_to && account.assigned_to.length > 0
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
				topContacts:
					account.contacts?.slice(0, 3).map((contact) => ({
						id: contact.id,
						name: `${contact.first_name || ''} ${contact.last_name || ''}`.trim()
					})) || [],

				// Tags
				tags: account.tags || [],

				// Teams
				teams: account.teams || []
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

/** @type {import('./$types').Actions} */
export const actions = {
	create: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const name = form.get('name')?.toString().trim();
			const email = form.get('email')?.toString().trim() || null;
			const phone = form.get('phone')?.toString().trim() || null;
			const website = form.get('website')?.toString().trim() || null;
			const industry = form.get('industry')?.toString().trim() || null;
			const description = form.get('description')?.toString().trim() || null;
			const address_line = form.get('address_line')?.toString().trim() || null;
			const city = form.get('city')?.toString().trim() || null;
			const state = form.get('state')?.toString().trim() || null;
			const postcode = form.get('postcode')?.toString().trim() || null;
			const country = form.get('country')?.toString().trim() || null;
			const annual_revenue = form.get('annual_revenue')?.toString().trim() || null;
			const number_of_employees = form.get('number_of_employees')?.toString().trim() || null;

			if (!name) {
				return fail(400, { error: 'Account name is required.' });
			}

			const accountData = {
				name,
				email,
				phone,
				website,
				industry,
				description,
				address_line,
				city,
				state,
				postcode,
				country,
				annual_revenue: annual_revenue ? parseFloat(annual_revenue) : null,
				number_of_employees: number_of_employees ? parseInt(number_of_employees, 10) : null
			};

			await apiRequest(
				'/accounts/',
				{
					method: 'POST',
					body: accountData
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error creating account:', err);
			return fail(500, { error: 'Failed to create account' });
		}
	},

	update: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const accountId = form.get('accountId')?.toString();
			const name = form.get('name')?.toString().trim();
			const email = form.get('email')?.toString().trim() || null;
			const phone = form.get('phone')?.toString().trim() || null;
			const website = form.get('website')?.toString().trim() || null;
			const industry = form.get('industry')?.toString().trim() || null;
			const description = form.get('description')?.toString().trim() || null;
			const address_line = form.get('address_line')?.toString().trim() || null;
			const city = form.get('city')?.toString().trim() || null;
			const state = form.get('state')?.toString().trim() || null;
			const postcode = form.get('postcode')?.toString().trim() || null;
			const country = form.get('country')?.toString().trim() || null;
			const annual_revenue = form.get('annual_revenue')?.toString().trim() || null;
			const number_of_employees = form.get('number_of_employees')?.toString().trim() || null;

			if (!accountId || !name) {
				return fail(400, { error: 'Account ID and name are required.' });
			}

			const accountData = {
				name,
				email,
				phone,
				website,
				industry,
				description,
				address_line,
				city,
				state,
				postcode,
				country,
				annual_revenue: annual_revenue ? parseFloat(annual_revenue) : null,
				number_of_employees: number_of_employees ? parseInt(number_of_employees, 10) : null
			};

			await apiRequest(
				`/accounts/${accountId}/`,
				{
					method: 'PUT',
					body: accountData
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error updating account:', err);
			return fail(500, { error: 'Failed to update account' });
		}
	},

	deactivate: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const accountId = form.get('accountId')?.toString();

			if (!accountId) {
				return fail(400, { error: 'Account ID is required.' });
			}

			// First fetch the current account data
			const account = await apiRequest(`/accounts/${accountId}/`, {}, { cookies, org: locals.org });
			const accountData = account.account_obj;

			// Update with is_active set to false using PUT (PATCH not supported)
			await apiRequest(
				`/accounts/${accountId}/`,
				{
					method: 'PUT',
					body: {
						name: accountData.name,
						email: accountData.email || '',
						phone: accountData.phone || '',
						website: accountData.website || '',
						industry: accountData.industry || '',
						description: accountData.description || '',
						address_line: accountData.address_line || '',
						city: accountData.city || '',
						state: accountData.state || '',
						postcode: accountData.postcode || '',
						country: accountData.country || '',
						is_active: false
					}
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error deactivating account:', err);
			return fail(500, { error: 'Failed to deactivate account' });
		}
	},

	activate: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const accountId = form.get('accountId')?.toString();

			if (!accountId) {
				return fail(400, { error: 'Account ID is required.' });
			}

			// First fetch the current account data
			const account = await apiRequest(`/accounts/${accountId}/`, {}, { cookies, org: locals.org });
			const accountData = account.account_obj;

			// Update with is_active set to true using PUT (PATCH not supported)
			await apiRequest(
				`/accounts/${accountId}/`,
				{
					method: 'PUT',
					body: {
						name: accountData.name,
						email: accountData.email || '',
						phone: accountData.phone || '',
						website: accountData.website || '',
						industry: accountData.industry || '',
						description: accountData.description || '',
						address_line: accountData.address_line || '',
						city: accountData.city || '',
						state: accountData.state || '',
						postcode: accountData.postcode || '',
						country: accountData.country || '',
						is_active: true
					}
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error activating account:', err);
			return fail(500, { error: 'Failed to activate account' });
		}
	},

	delete: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const accountId = form.get('accountId')?.toString();

			if (!accountId) {
				return fail(400, { error: 'Account ID is required.' });
			}

			await apiRequest(
				`/accounts/${accountId}/`,
				{
					method: 'DELETE'
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error deleting account:', err);
			return fail(500, { error: 'Failed to delete account' });
		}
	}
};
