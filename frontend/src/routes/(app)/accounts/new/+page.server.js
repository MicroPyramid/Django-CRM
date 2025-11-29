/**
 * Account Create Page - Modern CRM Version
 *
 * Streamlined account creation based on Twenty CRM and Salesforce patterns.
 * Django endpoint: POST /api/accounts/
 */

import { fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';
import { validatePhoneNumber, formatPhoneForStorage } from '$lib/utils/phone.js';
import { industries, countries } from '$lib/data/index.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
	const user = locals.user;
	const org = locals.org;

	try {
		// Fetch users and teams for assignment dropdowns
		const [usersResponse, teamsResponse] = await Promise.all([
			apiRequest('/users/', {}, { cookies, org }),
			apiRequest('/teams/', {}, { cookies, org })
		]);

		// Extract active users
		const activeUsersList = usersResponse.active_users?.active_users || [];
		const users = activeUsersList.map((profile) => ({
			id: profile.id,
			name: profile.user_details?.email?.split('@')[0] || 'Unknown',
			email: profile.user_details?.email || ''
		}));

		// Extract teams
		const teams = (teamsResponse.teams || teamsResponse.results || []).map((team) => ({
			id: team.id,
			name: team.name
		}));

		return {
			data: {
				industries,
				countries,
				users,
				teams
			}
		};
	} catch (err) {
		console.error('Error loading account form data:', err);
		return {
			data: {
				industries,
				countries,
				users: [],
				teams: []
			}
		};
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ request, locals, cookies }) => {
		const user = locals.user;
		const org = locals.org;

		const formData = await request.formData();

		// Extract and validate required fields
		const name = formData.get('name')?.toString().trim();

		if (!name) {
			return fail(400, { error: 'Account name is required' });
		}

		// Validate phone number if provided
		let formattedPhone = null;
		const phone = formData.get('phone')?.toString();
		if (phone && phone.trim().length > 0) {
			const phoneValidation = validatePhoneNumber(phone.trim());
			if (!phoneValidation.isValid) {
				return fail(400, { error: phoneValidation.error || 'Please enter a valid phone number' });
			}
			formattedPhone = formatPhoneForStorage(phone.trim());
		}

		// Build Django data object
		const djangoData = {
			// Core Account Information
			name,
			email: formData.get('email')?.toString().trim() || null,
			phone: formattedPhone,
			website: formData.get('website')?.toString().trim() || null,

			// Business Information
			industry: formData.get('industry')?.toString() || null,
			number_of_employees: formData.get('number_of_employees')
				? parseInt(formData.get('number_of_employees')?.toString() || '0')
				: null,
			annual_revenue: formData.get('annual_revenue')
				? parseFloat(formData.get('annual_revenue')?.toString() || '0')
				: null,

			// Address
			address_line: formData.get('address_line')?.toString().trim() || null,
			city: formData.get('city')?.toString().trim() || null,
			state: formData.get('state')?.toString().trim() || null,
			postcode: formData.get('postcode')?.toString().trim() || null,
			country: formData.get('country')?.toString() || null,

			// Assignment
			assigned_to: formData.getAll('assigned_to').map((id) => id.toString()),
			teams: formData.getAll('teams').map((id) => id.toString()),

			// Notes
			description: formData.get('description')?.toString().trim() || null
		};

		try {
			const response = await apiRequest(
				'/accounts/',
				{
					method: 'POST',
					body: djangoData
				},
				{ cookies, org }
			);

			return {
				status: 'success',
				message: 'Account created successfully',
				account: {
					id: response.id || response.account_obj?.id,
					name: response.name || response.account_obj?.name
				}
			};
		} catch (err) {
			console.error('Error creating account:', err);
			return fail(500, {
				error: 'Failed to create account: ' + (err instanceof Error ? err.message : 'Unknown error')
			});
		}
	}
};
