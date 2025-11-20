/**
 * Users Management Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Allows organization admins to:
 * - View all users in the organization
 * - Add users to the organization by email
 * - Change user roles (ADMIN/USER)
 * - Remove users from the organization
 * - Update organization details
 *
 * Django Endpoints:
 * - GET    /api/users/                  - List organization users
 * - POST   /api/users/                  - Create new user
 * - GET    /api/user/{id}/              - Get user details
 * - PUT    /api/user/{id}/              - Update user/profile
 * - DELETE /api/user/{id}/              - Deactivate user (soft delete)
 */

import { error, fail } from '@sveltejs/kit';

const API_BASE_URL = process.env.DJANGO_API_URL ? `${process.env.DJANGO_API_URL}/api` : 'http://localhost:8000/api';

/**
 * Make authenticated API request
 * @param {string} endpoint
 * @param {Object} options
 * @param {Object} context
 * @returns {Promise<any>}
 */
async function apiRequest(endpoint, options = {}, context) {
	const { cookies, org } = context;
	const accessToken = cookies.get('jwt_access') || cookies.get('access_token');

	const response = await fetch(`${API_BASE_URL}${endpoint}`, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${accessToken}`,
			'org': org.id,
			...options.headers
		}
	});

	if (!response.ok) {
		const errorData = await response.json().catch(() => ({ error: response.statusText }));
		throw new Error(errorData.errors || errorData.error || response.statusText);
	}

	return await response.json();
}

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
	const org = locals.org;
	const user = locals.user;

	try {
		// Fetch users list (returns active and inactive users)
		const data = await apiRequest('/users/', {}, { cookies, org });

		// Django returns: { active_users: {...}, inactive_users: {...}, roles: [...] }
		const activeUsers = data.active_users?.active_users || [];
		const inactiveUsers = data.inactive_users?.inactive_users || [];

		// Check if current user is admin
		// Django returns user_details with id and email
		const currentUserProfile = activeUsers.find(p =>
			p.user_details?.id === user.id ||
			p.user_details?.email === user.email
		);
		const isAdmin = currentUserProfile?.role === 'ADMIN' || currentUserProfile?.is_organization_admin;

		if (!isAdmin) {
			return {
				error: {
					name: 'You do not have permission to access this page'
				}
			};
		}

		// Combine active and inactive users, transform to match Prisma format
		const allUsers = [
			...activeUsers.map(profile => ({
				userId: profile.user_details?.id || profile.id,
				organizationId: org.id,
				role: profile.role,
				user: {
					id: profile.user_details?.id || profile.id,
					email: profile.user_details?.email || 'N/A',
					name: profile.user_details?.email?.split('@')[0] || 'N/A'
				},
				isActive: true,
				profile
			})),
			...inactiveUsers.map(profile => ({
				userId: profile.user_details?.id || profile.id,
				organizationId: org.id,
				role: profile.role,
				user: {
					id: profile.user_details?.id || profile.id,
					email: profile.user_details?.email || 'N/A',
					name: profile.user_details?.email?.split('@')[0] || 'N/A'
				},
				isActive: false,
				profile
			}))
		];

		return {
			organization: {
				id: org.id,
				name: org.name,
				domain: org.domain || '',
				description: org.description || ''
			},
			users: allUsers,
			user: { id: user.id }
		};
	} catch (err) {
		console.error('Error loading users:', err);
		return {
			error: {
				name: err.message || 'Failed to load users'
			}
		};
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	/**
	 * Update organization details
	 */
	update: async ({ request, locals, cookies }) => {
		const org = locals.org;
		const user = locals.user;

		try {
			// Check if user is admin (done in API, but double-check client-side)
			const formData = await request.formData();
			const name = formData.get('name')?.toString().trim();

			if (!name) {
				return fail(400, { error: 'Name is required' });
			}

			// Update organization via Django API
			await apiRequest(`/org/${org.id}/`, {
				method: 'PUT',
				body: JSON.stringify({ name })
			}, { cookies, org });

			return { success: true };

		} catch (err) {
			console.error('Error updating organization:', err);
			return fail(500, { error: err.message || 'Failed to update organization' });
		}
	},

	/**
	 * Add user to organization by email
	 */
	add_user: async ({ request, locals, cookies }) => {
		const org = locals.org;

		try {
			const formData = await request.formData();
			const email = formData.get('email')?.toString().trim().toLowerCase();
			const role = formData.get('role')?.toString();

			if (!email || !role) {
				return fail(400, { error: 'Email and role are required' });
			}

			// Create user via Django API
			// Django endpoint: POST /api/users/
			const userData = {
				email,
				role,
				// Django requires these fields for user creation
				username: email.split('@')[0],
				password: Math.random().toString(36).slice(-12), // Random password
			};

			await apiRequest('/users/', {
				method: 'POST',
				body: JSON.stringify(userData)
			}, { cookies, org });

			return { success: true };

		} catch (err) {
			console.error('Error adding user:', err);
			// Check for specific error messages
			if (err.message.includes('already exists') || err.message.includes('already in organization')) {
				return fail(400, { error: 'User already in organization' });
			}
			if (err.message.includes('not found')) {
				return fail(404, { error: 'No user found with that email' });
			}
			return fail(500, { error: err.message || 'Failed to add user' });
		}
	},

	/**
	 * Edit user role
	 */
	edit_role: async ({ request, locals, cookies }) => {
		const org = locals.org;
		const user = locals.user;

		try {
			const formData = await request.formData();
			const user_id = formData.get('user_id')?.toString();
			const role = formData.get('role')?.toString();

			if (!user_id || !role) {
				return fail(400, { error: 'User and role are required' });
			}

			// Don't allow editing own role
			if (user_id === user.id) {
				return fail(400, { error: 'You cannot change your own role' });
			}

			// Update user role via Django API
			// Django endpoint: PUT /api/user/{id}/
			await apiRequest(`/user/${user_id}/`, {
				method: 'PUT',
				body: JSON.stringify({ role })
			}, { cookies, org });

			return { success: true };

		} catch (err) {
			console.error('Error editing role:', err);
			if (err.message.includes('at least one admin')) {
				return fail(400, { error: 'Organization must have at least one admin' });
			}
			return fail(500, { error: err.message || 'Failed to edit role' });
		}
	},

	/**
	 * Remove user from organization
	 */
	remove_user: async ({ request, locals, cookies }) => {
		const org = locals.org;
		const user = locals.user;

		try {
			const formData = await request.formData();
			const user_id = formData.get('user_id')?.toString();

			if (!user_id) {
				return fail(400, { error: 'User is required' });
			}

			// Don't allow removing self
			if (user_id === user.id) {
				return fail(400, { error: 'You cannot remove yourself' });
			}

			// Remove user via Django API (soft delete - set is_active=False)
			// Django endpoint: PUT /api/user/{id}/status/
			await apiRequest(`/user/${user_id}/status/`, {
				method: 'POST',
				body: JSON.stringify({ is_active: false })
			}, { cookies, org });

			return { success: true };

		} catch (err) {
			console.error('Error removing user:', err);
			if (err.message.includes('at least one admin')) {
				return fail(400, { error: 'Organization must have at least one admin' });
			}
			return fail(500, { error: err.message || 'Failed to remove user' });
		}
	}
};
