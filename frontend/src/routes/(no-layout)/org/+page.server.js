/**
 * Organization Selection Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/auth/me/ (returns user with organizations array)
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { env } from '$env/dynamic/private';
import axios from 'axios';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, locals }) {
	const user = locals.user;

	if (!user) {
		return { orgs: [] };
	}

	try {
		const jwtAccess = cookies.get('jwt_access');
		if (!jwtAccess) {
			return { orgs: [] };
		}

		const apiUrl = env.DJANGO_API_URL || 'http://localhost:8000';

		// Fetch current user with organization memberships
		// The /api/auth/me/ endpoint returns user data with organizations array
		const response = await axios.get(`${apiUrl}/api/auth/me/`, {
			headers: {
				Authorization: `Bearer ${jwtAccess}`
			}
		});

		// Extract organizations from the user data
		// Django's MeView returns user with organizations array
		let orgs = [];

		if (response.data.organizations && Array.isArray(response.data.organizations)) {
			orgs = response.data.organizations.map((org) => ({
				id: org.id,
				name: org.name,
				logo: org.logo || null,
				role: org.role || 'USER'
			}));
		}

		return { orgs };
	} catch (error) {
		console.error('Error fetching organizations:', error);
		// Return empty array so user can create a new organization
		return { orgs: [] };
	}
}
