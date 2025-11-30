/**
 * Contacts List Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/contacts/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ url, locals, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		const page = parseInt(url.searchParams.get('page') || '1');
		const limit = parseInt(url.searchParams.get('limit') || '20');
		const search = url.searchParams.get('search') || '';
		const ownerId = url.searchParams.get('owner') || '';

		// Build query parameters for Django
		const queryParams = buildQueryParams({
			page,
			limit,
			sort: 'created_at',
			order: 'desc'
		});

		// Add search filter (Django typically uses 'search' param)
		if (search) {
			queryParams.append('search', search);
		}

		// Add owner filter (Django uses assigned_to)
		if (ownerId) {
			queryParams.append('assigned_to', ownerId);
		}

		// Fetch contacts and owners in parallel
		const [contactsResponse, ownersResponse] = await Promise.all([
			apiRequest(`/contacts/?${queryParams.toString()}`, {}, { cookies, org }),
			// Get users for owner filter dropdown
			apiRequest('/users/', {}, { cookies, org })
		]);

		// Handle Django response format
		let contacts = [];
		let totalCount = 0;

		if (contactsResponse.results) {
			// Standard Django pagination
			contacts = contactsResponse.results;
			totalCount = contactsResponse.count || 0;
		} else if (Array.isArray(contactsResponse)) {
			// Direct array response
			contacts = contactsResponse;
			totalCount = contacts.length;
		}

		// Transform Django contacts to match frontend structure
		const transformedContacts = contacts.map((contact) => ({
			id: contact.id,
			// Core fields
			firstName: contact.first_name,
			lastName: contact.last_name,
			email: contact.email,
			phone: contact.phone,
			// Professional info
			organization: contact.organization,
			title: contact.title,
			department: contact.department,
			// Communication preferences
			doNotCall: contact.do_not_call || false,
			linkedInUrl: contact.linked_in_url,
			// Address fields
			addressLine: contact.address_line,
			city: contact.city,
			state: contact.state,
			postcode: contact.postcode,
			country: contact.country,
			// Notes
			description: contact.description,
			// Timestamps
			createdAt: contact.created_at,
			updatedAt: contact.updated_at,

			// Owner info - Django returns assigned_to array
			owner:
				contact.assigned_to && contact.assigned_to.length > 0
					? {
							id: contact.assigned_to[0].id,
							name: contact.assigned_to[0].user_details?.email || 'Unknown',
							email: contact.assigned_to[0].user_details?.email
						}
					: contact.created_by
						? {
								id: contact.created_by.id,
								name: contact.created_by.email,
								email: contact.created_by.email
							}
						: null,

			// Teams
			teams:
				contact.teams?.map((team) => ({
					id: team.id,
					name: team.name
				})) || [],

			// Tags
			tags:
				contact.tags?.map((tag) => ({
					id: tag.id,
					name: tag.name
				})) || [],

			// Related accounts
			relatedAccounts:
				contact.accounts?.map((account) => ({
					account: {
						id: account.id,
						name: account.name
					}
				})) || [],

			// Counts - Django may not provide _count, use 0 as default
			_count: {
				tasks: contact.task_count || 0,
				events: contact.event_count || 0,
				opportunities: contact.opportunity_count || 0,
				cases: contact.case_count || 0
			}
		}));

		// Transform owners list
		// Django UsersListView returns { active_users: { active_users: [...] }, inactive_users: { ... } }
		const activeUsers = ownersResponse.active_users?.active_users || [];
		const owners = activeUsers.map((user) => ({
			id: user.id,
			name: user.user_details?.email || user.email,
			email: user.user_details?.email || user.email
		}));

		return {
			contacts: transformedContacts,
			totalCount,
			currentPage: page,
			totalPages: Math.ceil(totalCount / limit),
			limit,
			search,
			ownerId,
			owners
		};
	} catch (err) {
		console.error('Error loading contacts from API:', err);
		throw error(500, `Failed to load contacts: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	create: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			// Core fields
			const firstName = form.get('firstName')?.toString().trim();
			const lastName = form.get('lastName')?.toString().trim();
			const email = form.get('email')?.toString().trim() || '';
			const phone = form.get('phone')?.toString().trim() || '';
			// Professional info
			const organization = form.get('organization')?.toString().trim() || '';
			const title = form.get('title')?.toString().trim() || '';
			const department = form.get('department')?.toString().trim() || '';
			// Communication preferences
			const doNotCall = form.get('doNotCall') === 'true';
			const linkedInUrl = form.get('linkedInUrl')?.toString().trim() || '';
			// Address fields
			const addressLine = form.get('addressLine')?.toString().trim() || '';
			const city = form.get('city')?.toString().trim() || '';
			const state = form.get('state')?.toString().trim() || '';
			const postcode = form.get('postcode')?.toString().trim() || '';
			const country = form.get('country')?.toString().trim() || '';
			// Notes
			const description = form.get('description')?.toString().trim() || '';
			// Assignment
			const ownerId = form.get('ownerId')?.toString();

			if (!firstName || !lastName) {
				return fail(400, { error: 'First name and last name are required.' });
			}

			const contactData = {
				first_name: firstName,
				last_name: lastName,
				email: email || null,
				phone: phone || null,
				organization: organization || null,
				title: title || null,
				department: department || null,
				do_not_call: doNotCall,
				linked_in_url: linkedInUrl || null,
				address_line: addressLine || null,
				city: city || null,
				state: state || null,
				postcode: postcode || null,
				country: country || null,
				description: description || null,
				assigned_to: ownerId ? [ownerId] : []
			};

			await apiRequest(
				'/contacts/',
				{
					method: 'POST',
					body: contactData
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error creating contact:', err);
			return fail(500, { error: 'Failed to create contact' });
		}
	},

	update: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const contactId = form.get('contactId')?.toString();
			// Core fields
			const firstName = form.get('firstName')?.toString().trim();
			const lastName = form.get('lastName')?.toString().trim();
			const email = form.get('email')?.toString().trim() || '';
			const phone = form.get('phone')?.toString().trim() || '';
			// Professional info
			const organization = form.get('organization')?.toString().trim() || '';
			const title = form.get('title')?.toString().trim() || '';
			const department = form.get('department')?.toString().trim() || '';
			// Communication preferences
			const doNotCall = form.get('doNotCall') === 'true';
			const linkedInUrl = form.get('linkedInUrl')?.toString().trim() || '';
			// Address fields
			const addressLine = form.get('addressLine')?.toString().trim() || '';
			const city = form.get('city')?.toString().trim() || '';
			const state = form.get('state')?.toString().trim() || '';
			const postcode = form.get('postcode')?.toString().trim() || '';
			const country = form.get('country')?.toString().trim() || '';
			// Notes
			const description = form.get('description')?.toString().trim() || '';
			// Assignment
			const ownerId = form.get('ownerId')?.toString();

			if (!contactId || !firstName || !lastName) {
				return fail(400, { error: 'Contact ID, first name, and last name are required.' });
			}

			const contactData = {
				first_name: firstName,
				last_name: lastName,
				email: email || null,
				phone: phone || null,
				organization: organization || null,
				title: title || null,
				department: department || null,
				do_not_call: doNotCall,
				linked_in_url: linkedInUrl || null,
				address_line: addressLine || null,
				city: city || null,
				state: state || null,
				postcode: postcode || null,
				country: country || null,
				description: description || null,
				assigned_to: ownerId ? [ownerId] : []
			};

			await apiRequest(
				`/contacts/${contactId}/`,
				{
					method: 'PUT',
					body: contactData
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error updating contact:', err);
			return fail(500, { error: 'Failed to update contact' });
		}
	},

	delete: async ({ request, locals, cookies }) => {
		try {
			const data = await request.formData();
			const contactId = data.get('contactId')?.toString();

			if (!contactId) {
				return fail(400, { error: 'Contact ID is required' });
			}

			// Delete via API
			await apiRequest(
				`/contacts/${contactId}/`,
				{ method: 'DELETE' },
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error deleting contact:', err);
			return fail(500, { error: 'Failed to delete contact' });
		}
	}
};
