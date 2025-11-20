/**
 * Opportunity Create Page - Modern CRM Version
 *
 * Streamlined opportunity creation based on Twenty CRM and Salesforce patterns.
 * Django endpoint: POST /api/opportunities/
 */

import { fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, url, cookies }) {
	const org = locals.org;
	const preSelectedAccountId = url.searchParams.get('accountId');

	// Stages matching Django STAGES choices
	const stages = [
		{ value: 'PROSPECTING', label: 'Prospecting' },
		{ value: 'QUALIFICATION', label: 'Qualification' },
		{ value: 'PROPOSAL', label: 'Proposal' },
		{ value: 'NEGOTIATION', label: 'Negotiation' },
		{ value: 'CLOSED_WON', label: 'Closed Won' },
		{ value: 'CLOSED_LOST', label: 'Closed Lost' }
	];

	// Opportunity types matching Django OPPORTUNITY_TYPES choices
	const opportunityTypes = [
		{ value: 'NEW_BUSINESS', label: 'New Business' },
		{ value: 'EXISTING_BUSINESS', label: 'Existing Business' },
		{ value: 'RENEWAL', label: 'Renewal' },
		{ value: 'UPSELL', label: 'Upsell' },
		{ value: 'CROSS_SELL', label: 'Cross-sell' }
	];

	// Lead sources matching Django SOURCES choices
	const leadSources = [
		{ value: 'NONE', label: 'None' },
		{ value: 'CALL', label: 'Call' },
		{ value: 'EMAIL', label: 'Email' },
		{ value: 'EXISTING CUSTOMER', label: 'Existing Customer' },
		{ value: 'PARTNER', label: 'Partner' },
		{ value: 'PUBLIC RELATIONS', label: 'Public Relations' },
		{ value: 'CAMPAIGN', label: 'Campaign' },
		{ value: 'WEBSITE', label: 'Website' },
		{ value: 'OTHER', label: 'Other' }
	];

	try {
		// Fetch accounts, contacts, users, and teams in parallel
		const [accountsResponse, contactsResponse, usersResponse, teamsResponse] = await Promise.all([
			apiRequest('/accounts/', {}, { cookies, org }),
			apiRequest('/contacts/', {}, { cookies, org }),
			apiRequest('/users/', {}, { cookies, org }),
			apiRequest('/teams/', {}, { cookies, org })
		]);

		// Transform accounts
		let accountsList = [];
		if (accountsResponse.results) {
			accountsList = accountsResponse.results;
		} else if (accountsResponse.active_accounts?.open_accounts) {
			accountsList = accountsResponse.active_accounts.open_accounts;
		}

		const accounts = accountsList.map((acc) => ({
			id: acc.id,
			name: acc.name
		}));

		// Transform contacts
		const contacts = (contactsResponse.results || contactsResponse || []).map((contact) => ({
			id: contact.id,
			firstName: contact.first_name,
			lastName: contact.last_name,
			email: contact.email
		}));

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

		// Get pre-selected account details if provided
		let preSelectedAccount = null;
		if (preSelectedAccountId) {
			preSelectedAccount = accounts.find((account) => account.id === preSelectedAccountId);
		}

		return {
			data: {
				accounts,
				contacts,
				users,
				teams,
				stages,
				opportunityTypes,
				leadSources,
				preSelectedAccountId,
				preSelectedAccountName: preSelectedAccount?.name || null
			}
		};
	} catch (err) {
		console.error('Error loading opportunity form data:', err);
		return {
			data: {
				accounts: [],
				contacts: [],
				users: [],
				teams: [],
				stages,
				opportunityTypes,
				leadSources,
				preSelectedAccountId: null,
				preSelectedAccountName: null
			}
		};
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ request, locals, cookies }) => {
		const org = locals.org;

		const formData = await request.formData();

		// Extract and validate required fields
		const name = formData.get('name')?.toString().trim();
		const accountId = formData.get('account')?.toString();
		const stage = formData.get('stage')?.toString();

		if (!name) {
			return fail(400, { error: 'Opportunity name is required' });
		}

		if (!stage) {
			return fail(400, { error: 'Stage is required' });
		}

		// Validate probability
		const probabilityStr = formData.get('probability')?.toString();
		let probability = null;
		if (probabilityStr && probabilityStr.trim() !== '') {
			probability = parseInt(probabilityStr);
			if (isNaN(probability) || probability < 0 || probability > 100) {
				return fail(400, { error: 'Probability must be between 0 and 100' });
			}
		}

		// Validate amount
		const amountStr = formData.get('amount')?.toString();
		let amount = null;
		if (amountStr && amountStr.trim() !== '') {
			amount = parseFloat(amountStr);
			if (isNaN(amount) || amount < 0) {
				return fail(400, { error: 'Amount must be a valid positive number' });
			}
		}

		// Build Django data object
		const djangoData = {
			// Core Opportunity Information
			name,
			account: accountId || null,
			stage,
			opportunity_type: formData.get('opportunity_type')?.toString() || null,

			// Financial Information
			currency: formData.get('currency')?.toString() || null,
			amount,
			probability,
			closed_on: formData.get('closed_on')?.toString() || null,

			// Source & Context
			lead_source: formData.get('lead_source')?.toString() || null,

			// Relationships
			contacts: formData.getAll('contacts').map((id) => id.toString()),

			// Assignment
			assigned_to: formData.getAll('assigned_to').map((id) => id.toString()),
			teams: formData.getAll('teams').map((id) => id.toString()),

			// Notes
			description: formData.get('description')?.toString().trim() || null
		};

		try {
			const response = await apiRequest(
				'/opportunities/',
				{
					method: 'POST',
					body: djangoData
				},
				{ cookies, org }
			);

			return {
				status: 'success',
				message: 'Opportunity created successfully',
				opportunity: {
					id: response.id || response.opportunity_obj?.id,
					name: response.name || response.opportunity_obj?.name
				}
			};
		} catch (err) {
			console.error('Error creating opportunity:', err);
			return fail(500, {
				error:
					'Failed to create opportunity: ' +
					(err instanceof Error ? err.message : 'Unknown error')
			});
		}
	}
};
