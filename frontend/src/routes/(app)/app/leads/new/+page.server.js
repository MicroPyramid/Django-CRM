/**
 * Lead Create Page - Modern CRM Version
 *
 * Streamlined lead creation based on Twenty CRM and Salesforce patterns.
 * Django endpoint: POST /api/leads/
 */

import { fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';
import { validatePhoneNumber, formatPhoneForStorage } from '$lib/utils/phone.js';
import { industries, leadSources, leadStatuses, countries } from '$lib/data/index.js';

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
				industries,
				statuses: leadStatuses,
				sources: leadSources,
				countries,
				users,
				teams
			}
		};
	} catch (err) {
		console.error('Error loading lead form data:', err);
		return {
			data: {
				industries,
				statuses: leadStatuses,
				sources: leadSources,
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
		const title = formData.get('title')?.toString().trim();
		const firstName = formData.get('first_name')?.toString().trim();
		const lastName = formData.get('last_name')?.toString().trim();

		if (!title) {
			return fail(400, { error: 'Lead title is required' });
		}

		if (!firstName) {
			return fail(400, { error: 'First name is required' });
		}

		if (!lastName) {
			return fail(400, { error: 'Last name is required' });
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
			// Core Lead Information
			title,
			first_name: firstName,
			last_name: lastName,
			email: formData.get('email')?.toString().trim() || null,
			phone: formattedPhone,
			account_name: formData.get('account_name')?.toString().trim() || null,
			contact_title: formData.get('contact_title')?.toString().trim() || null,
			website: formData.get('website')?.toString().trim() || null,
			linkedin_url: formData.get('linkedin_url')?.toString().trim() || null,

			// Sales Pipeline
			status: formData.get('status')?.toString() || 'assigned',
			source: formData.get('source')?.toString() || null,
			industry: formData.get('industry')?.toString() || null,
			rating: formData.get('rating')?.toString() || null,
			opportunity_amount: formData.get('opportunity_amount')
				? parseFloat(formData.get('opportunity_amount')?.toString() || '0')
				: null,
			probability: formData.get('probability')
				? parseInt(formData.get('probability')?.toString() || '0')
				: null,
			close_date: formData.get('close_date')?.toString() || null,

			// Address
			address_line: formData.get('address_line')?.toString().trim() || null,
			city: formData.get('city')?.toString().trim() || null,
			state: formData.get('state')?.toString().trim() || null,
			postcode: formData.get('postcode')?.toString().trim() || null,
			country: formData.get('country')?.toString() || null,

			// Assignment
			assigned_to: formData.getAll('assigned_to').map(id => id.toString()),
			teams: formData.getAll('teams').map(id => id.toString()),

			// Activity
			last_contacted: formData.get('last_contacted')?.toString() || null,
			next_follow_up: formData.get('next_follow_up')?.toString() || null,
			description: formData.get('description')?.toString().trim() || null
		};

		try {
			const response = await apiRequest(
				'/leads/',
				{
					method: 'POST',
					body: djangoData
				},
				{ cookies, org }
			);

			return {
				status: 'success',
				message: 'Lead created successfully',
				lead: {
					id: response.id || response.lead_obj?.id,
					name: `${firstName} ${lastName}`
				}
			};
		} catch (err) {
			console.error('Error creating lead:', err);
			return fail(500, {
				error: 'Failed to create lead: ' + (err instanceof Error ? err.message : 'Unknown error')
			});
		}
	}
};
