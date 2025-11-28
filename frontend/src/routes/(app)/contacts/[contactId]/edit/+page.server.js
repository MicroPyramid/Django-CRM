/**
 * Contact Edit Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: PUT/PATCH /api/contacts/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { fail, error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';
import { validatePhoneNumber, formatPhoneForStorage } from '$lib/utils/phone.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		const response = await apiRequest(`/contacts/${params.contactId}/`, {}, { cookies, org });

		if (!response.contact_obj) {
			throw error(404, 'Contact not found');
		}

		const contactData = response.contact_obj;

		// Transform to Prisma structure
		const contact = {
			id: contactData.id,
			firstName: contactData.first_name,
			lastName: contactData.last_name,
			email: contactData.email,
			phone: contactData.phone,
			title: contactData.title,
			department: contactData.department,
			street: contactData.address?.address_line || null,
			city: contactData.address?.city || null,
			state: contactData.address?.state || null,
			postalCode: contactData.address?.postcode || null,
			country: contactData.address?.country || null,
			description: contactData.description
		};

		// Note: Account relationship handling
		// Django may return account info differently
		// This might require additional API call or different endpoint
		const account = contactData.account
			? {
					id: contactData.account.id,
					name: contactData.account.name
				}
			: null;

		return {
			contact,
			account,
			isPrimary: contactData.is_primary || false,
			role: contactData.role || ''
		};
	} catch (err) {
		console.error('Error loading contact for edit:', err);
		throw error(500, `Failed to load contact: ${err.message}`);
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
		const email = formData.get('email')?.toString().trim() || null;
		const phone = formData.get('phone')?.toString().trim() || null;
		const title = formData.get('title')?.toString().trim() || null;
		const department = formData.get('department')?.toString().trim() || null;
		const street = formData.get('street')?.toString().trim() || null;
		const city = formData.get('city')?.toString().trim() || null;
		const state = formData.get('state')?.toString().trim() || null;
		const postalCode = formData.get('postalCode')?.toString().trim() || null;
		const country = formData.get('country')?.toString().trim() || null;
		const description = formData.get('description')?.toString().trim() || null;

		// Validation
		const errors = {};

		if (!firstName || firstName.length === 0) {
			errors.firstName = 'First name is required';
		}

		if (!lastName || lastName.length === 0) {
			errors.lastName = 'Last name is required';
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

		if (Object.keys(errors).length > 0) {
			return fail(400, {
				errors,
				values: {
					firstName,
					lastName,
					email,
					phone,
					title,
					department,
					street,
					city,
					state,
					postalCode,
					country,
					description
				}
			});
		}

		try {
			// Transform to Django field names
			const djangoData = {
				first_name: firstName,
				last_name: lastName,
				email: email,
				phone: formattedPhone,
				title: title,
				department: department,
				address: {
					address_line: street,
					city: city,
					state: state,
					postcode: postalCode,
					country: country
				},
				description: description
			};

			// Update contact via API
			await apiRequest(
				`/contacts/${params.contactId}/`,
				{
					method: 'PUT',
					body: djangoData
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error updating contact:', err);
			return fail(500, {
				error: 'Failed to update contact: ' + (err instanceof Error ? err.message : 'Unknown error'),
				values: {
					firstName,
					lastName,
					email,
					phone,
					title,
					department,
					street,
					city,
					state,
					postalCode,
					country,
					description
				}
			});
		}
	}
};
