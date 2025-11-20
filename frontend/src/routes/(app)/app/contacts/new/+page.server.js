/**
 * Contact Create Page - Modern CRM Version
 *
 * Streamlined contact creation based on Twenty CRM and Salesforce patterns.
 * Django endpoint: POST /api/contacts/
 */

import { fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';
import { validatePhoneNumber, formatPhoneForStorage } from '$lib/utils/phone.js';
import { countries } from '$lib/data/index.js';

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
		const users = activeUsersList.map(profile => ({
			id: profile.id,
			name: profile.user_details?.email?.split('@')[0] || 'Unknown',
			email: profile.user_details?.email || ''
		}));

		// Extract teams
		const teams = (teamsResponse.teams || teamsResponse.results || []).map(team => ({
			id: team.id,
			name: team.name
		}));

		return {
			data: {
				countries,
				users,
				teams
			}
		};
	} catch (err) {
		console.error('Error loading contact form data:', err);
		return {
			data: {
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
		const firstName = formData.get('first_name')?.toString().trim();
		const lastName = formData.get('last_name')?.toString().trim();

		if (!firstName) {
			return fail(400, { error: 'First name is required' });
		}

		if (!lastName) {
			return fail(400, { error: 'Last name is required' });
		}

		// Validate phone number if provided
		let formattedPhone = null;
		const phone = formData.get('mobile_number')?.toString();
		if (phone && phone.trim().length > 0) {
			const phoneValidation = validatePhoneNumber(phone.trim());
			if (!phoneValidation.isValid) {
				return fail(400, { error: phoneValidation.error || 'Please enter a valid phone number' });
			}
			formattedPhone = formatPhoneForStorage(phone.trim());
		}

		// Build Django data object
		const djangoData = {
			// Core Contact Information
			first_name: firstName,
			last_name: lastName,
			primary_email: formData.get('primary_email')?.toString().trim() || null,
			mobile_number: formattedPhone,

			// Professional Information
			organization: formData.get('organization')?.toString().trim() || null,
			title: formData.get('title')?.toString().trim() || null,
			department: formData.get('department')?.toString().trim() || null,

			// Communication Preferences
			do_not_call: formData.get('do_not_call') === 'on',
			linked_in_url: formData.get('linked_in_url')?.toString().trim() || null,

			// Address
			address_line: formData.get('address_line')?.toString().trim() || null,
			city: formData.get('city')?.toString().trim() || null,
			state: formData.get('state')?.toString().trim() || null,
			postcode: formData.get('postcode')?.toString().trim() || null,
			country: formData.get('country')?.toString() || null,

			// Assignment
			assigned_to: formData.getAll('assigned_to').map(id => id.toString()),
			teams: formData.getAll('teams').map(id => id.toString()),

			// Notes
			description: formData.get('description')?.toString().trim() || null
		};

		try {
			const response = await apiRequest(
				'/contacts/',
				{
					method: 'POST',
					body: djangoData
				},
				{ cookies, org }
			);

			return {
				status: 'success',
				message: 'Contact created successfully',
				contact: {
					id: response.id || response.contact_obj?.id,
					name: `${firstName} ${lastName}`
				}
			};
		} catch (err) {
			console.error('Error creating contact:', err);
			return fail(500, {
				error: 'Failed to create contact: ' + (err instanceof Error ? err.message : 'Unknown error')
			});
		}
	}
};
