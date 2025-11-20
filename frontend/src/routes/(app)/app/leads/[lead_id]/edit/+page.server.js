/**
 * Lead Edit Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: PUT/PATCH /api/leads/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';
import { validatePhoneNumber, formatPhoneForStorage } from '$lib/utils/phone.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Fetch lead and users in parallel
		const [leadResponse, usersResponse] = await Promise.all([
			apiRequest(`/leads/${params.lead_id}/`, {}, { cookies, org }),
			apiRequest('/users/', {}, { cookies, org })
		]);

		if (!leadResponse.lead_obj) {
			throw error(404, 'Lead not found');
		}

		const leadData = leadResponse.lead_obj;

		// Transform lead to form structure
		// Note: assigned_to is an array of ProfileSerializer objects
		const assignedTo = leadData.assigned_to || [];
		const firstAssigned = assignedTo[0];

		const lead = {
			id: leadData.id,
			firstName: leadData.first_name || '',
			lastName: leadData.last_name || '',
			email: leadData.email,
			phone: leadData.phone,
			company: leadData.company?.name || null,
			title: leadData.title,
			industry: leadData.industry,
			rating: leadData.rating || null,
			description: leadData.description,
			status: leadData.status || 'assigned', // Django default status
			leadSource: leadData.source || null,
			ownerId: firstAssigned?.id || null, // Profile ID
			// Include owner info if available
			owner: firstAssigned
				? {
						id: firstAssigned.id,
						name: firstAssigned.user_details?.email || 'Unknown',
						email: firstAssigned.user_details?.email
					}
				: null
		};

		// Transform users
		// Django UsersListView returns { active_users: { active_users: [...] }, ... }
		const activeUsersList = usersResponse.active_users?.active_users || [];
		const users = activeUsersList.map((user) => ({
			id: user.id,
			user: {
				id: user.id,
				name: user.user_details?.email || user.email,
				email: user.user_details?.email || user.email
			}
		}));

		return {
			lead,
			users
		};
	} catch (err) {
		console.error('Error loading lead for edit:', err);
		throw error(500, `Failed to load lead: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ request, params, locals, cookies }) => {
		const org = locals.org;
		const formData = await request.formData();

		// Extract form fields
		const firstName = formData.get('firstName')?.toString().trim();
		const lastName = formData.get('lastName')?.toString().trim();
		const email = formData.get('email')?.toString().trim();
		const phone = formData.get('phone')?.toString().trim();
		const company = formData.get('company')?.toString().trim();
		const title = formData.get('title')?.toString().trim();
		const industry = formData.get('industry')?.toString().trim();
		const rating = formData.get('rating')?.toString().trim();
		const description = formData.get('description')?.toString().trim();
		const ownerId = formData.get('ownerId')?.toString();
		const status = formData.get('status')?.toString() || 'assigned';
		const leadSource = formData.get('leadSource')?.toString();

		// Validation
		const errors = {};

		// Note: Django requires 'title' field, not firstName/lastName
		// But we'll keep the UI friendly by using first/last name
		if (!firstName || firstName.length === 0) {
			errors.firstName = 'First name is required';
		}

		if (!lastName || lastName.length === 0) {
			errors.lastName = 'Last name is required';
		}

		if (!ownerId) {
			errors.ownerId = 'Owner is required';
		}

		// Title is required by Django - generate from first + last name if not provided
		if (!title && firstName && lastName) {
			// Will generate title below
		}

		// Validate email format if provided
		if (email && email.length > 0 && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
			errors.email = 'Please enter a valid email address';
		}

		// Validate phone number if provided
		let formattedPhone = null;
		if (phone && phone.length > 0) {
			const phoneValidation = validatePhoneNumber(phone);
			if (!phoneValidation.isValid) {
				errors.phone = phoneValidation.error || 'Please enter a valid phone number';
			} else {
				formattedPhone = formatPhoneForStorage(phone);
			}
		}

		// Status and source validation not needed here since form options
		// now match Django LEAD_STATUS and LEAD_SOURCE choices

		if (Object.keys(errors).length > 0) {
			return fail(400, {
				errors,
				values: {
					firstName,
					lastName,
					email,
					phone,
					company,
					title,
					industry,
					rating,
					description,
					ownerId,
					status,
					leadSource
				}
			});
		}

		try {
			// Transform to Django field names
			// Note: Django requires 'title' field - use provided title or generate from name
			const leadTitle = title || `${firstName} ${lastName}`.trim();

			const djangoData = {
				first_name: firstName,
				last_name: lastName,
				email: email || null,
				phone: formattedPhone,
				title: leadTitle, // Required by Django
				industry: industry || null,
				rating: rating || null,
				description: description || null,
				status: status,
				source: leadSource || null,
				assigned_to: ownerId ? [ownerId] : []
			};

			// Update lead via API
			await apiRequest(
				`/leads/${params.lead_id}/`,
				{
					method: 'PUT',
					body: djangoData
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error updating lead:', err);
			return fail(500, {
				error: 'Failed to update lead: ' + (err instanceof Error ? err.message : 'Unknown error'),
				values: {
					firstName,
					lastName,
					email,
					phone,
					company,
					title,
					industry,
					rating,
					description,
					ownerId,
					status,
					leadSource
				}
			});
		}
	}
};
