/**
 * Account Edit Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: PUT /api/accounts/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { fail, redirect, error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		const response = await apiRequest(`/accounts/${params.accountId}/`, {}, { cookies, org });

		if (!response.account_obj) {
			throw error(404, 'Account not found');
		}

		const accountData = response.account_obj;

		// Transform to Prisma structure
		const account = {
			id: accountData.id,
			name: accountData.name,
			industry: accountData.industry,
			type: accountData.account_type || accountData.type,
			website: accountData.website,
			phone: accountData.phone
		};

		return { account };
	} catch (err) {
		console.error('Error loading account:', err);
		throw error(500, `Failed to load account: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ request, params, locals, cookies }) => {
		const org = locals.org;
		const form = await request.formData();
		const name = form.get('name')?.toString();
		const industry = form.get('industry')?.toString() || null;
		const type = form.get('type')?.toString() || null;
		const website = form.get('website')?.toString() || null;
		const phone = form.get('phone')?.toString() || null;

		if (!name) {
			return fail(400, { name, missing: true });
		}

		try {
			// Transform to Django field names
			const djangoData = {
				name,
				industry,
				account_type: type,
				website,
				phone
			};

			// Update account via API
			await apiRequest(
				`/accounts/${params.accountId}/`,
				{
					method: 'PUT',
					body: djangoData
				},
				{ cookies, org }
			);

			throw redirect(303, `/accounts/${params.accountId}`);
		} catch (err) {
			console.error('Error updating account:', err);
			return fail(500, {
				error: 'Failed to update account: ' + (err instanceof Error ? err.message : 'Unknown error')
			});
		}
	}
};
