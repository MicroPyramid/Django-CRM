/**
 * SvelteKit Server Hooks with JWT Authentication
 *
 * Authentication Flow:
 * 1. JWT tokens stored in cookies (httpOnly for security)
 * 2. Decode JWT locally to check org context (no API call needed)
 * 3. Only call switch-org if token doesn't have correct org
 * 4. Routes protected based on authentication and org membership
 */

import { redirect } from '@sveltejs/kit';
import axios from 'axios';

const API_BASE_URL = process.env.DJANGO_API_URL ? `${process.env.DJANGO_API_URL}/api` : 'http://localhost:8000/api';

/**
 * Decode JWT payload without verification (for reading claims only)
 * @param {string} token - JWT token
 * @returns {Object|null} Decoded payload or null if invalid
 */
function decodeJwtPayload(token) {
	try {
		const parts = token.split('.');
		if (parts.length !== 3) return null;

		const payload = parts[1];
		// Handle base64url encoding
		const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
		const jsonPayload = Buffer.from(base64, 'base64').toString('utf8');
		return JSON.parse(jsonPayload);
	} catch (error) {
		return null;
	}
}

/**
 * Check if JWT token has the specified org_id in its payload
 * @param {string} token - JWT token
 * @param {string} orgId - Organization UUID to check
 * @returns {boolean} True if token has the org context
 */
function tokenHasOrgContext(token, orgId) {
	const payload = decodeJwtPayload(token);
	return payload && payload.org_id === orgId;
}

/**
 * Verify JWT token with Django backend
 * @param {string} accessToken - JWT access token
 * @returns {Promise<Object|null>} User data or null if invalid
 */
async function verifyToken(accessToken) {
	try {
		const response = await axios.get(`${API_BASE_URL}/auth/me/`, {
			headers: {
				Authorization: `Bearer ${accessToken}`
			}
		});

		return response.data;
	} catch (error) {
		console.error('Token verification failed:', error);
		return null;
	}
}

/**
 * Refresh access token using refresh token
 * @param {string} refreshToken - JWT refresh token
 * @returns {Promise<string|null>} New access token or null if refresh failed
 */
async function refreshAccessToken(refreshToken) {
	try {
		const response = await axios.post(`${API_BASE_URL}/auth/refresh-token/`, {
			refresh: refreshToken
		});

		return response.data.access;
	} catch (error) {
		console.error('Token refresh failed:', error);
		return null;
	}
}

/**
 * Get profile for specific organization
 * @param {string} accessToken - JWT access token
 * @returns {Promise<Object|null>} Profile data or null if invalid
 */
async function getProfile(accessToken) {
	try {
		const response = await axios.get(`${API_BASE_URL}/auth/profile/`, {
			headers: {
				Authorization: `Bearer ${accessToken}`
			}
		});

		return response.data;
	} catch (error) {
		console.error('Profile fetch failed:', error);
		return null;
	}
}

/**
 * Switch organization and get new tokens with org context
 * @param {string} accessToken - Current JWT access token
 * @param {string} orgId - Organization UUID to switch to
 * @returns {Promise<Object|null>} New tokens and org data or null if failed
 */
async function switchOrg(accessToken, orgId) {
	try {
		const response = await axios.post(`${API_BASE_URL}/auth/switch-org/`,
			{ org_id: orgId },
			{
				headers: {
					Authorization: `Bearer ${accessToken}`,
					'Content-Type': 'application/json'
				}
			}
		);

		return response.data;
	} catch (error) {
		console.error('Org switch failed:', error);
		return null;
	}
}

/** @type {import('@sveltejs/kit').Handle} */
export async function handle({ event, resolve }) {
	// Get tokens from cookies (support both naming conventions)
	let accessToken = event.cookies.get('access_token') || event.cookies.get('jwt_access');
	const refreshToken = event.cookies.get('refresh_token') || event.cookies.get('jwt_refresh');
	const orgId = event.cookies.get('org');

	let user = null;

	// Try to authenticate user
	if (accessToken) {
		user = await verifyToken(accessToken);

		// If access token expired, try to refresh
		if (!user && refreshToken) {
			const newAccessToken = await refreshAccessToken(refreshToken);
			if (newAccessToken) {
				// Update cookie with new access token (use jwt_access for consistency with login)
				event.cookies.set('jwt_access', newAccessToken, {
					path: '/',
					httpOnly: true,
					sameSite: 'lax',
					secure: process.env.NODE_ENV === 'production',
					maxAge: 60 * 60 * 24 // 1 day
				});
				accessToken = newAccessToken;
				user = await verifyToken(newAccessToken);
			} else {
				// Refresh failed, clear cookies (both naming conventions)
				event.cookies.delete('access_token', { path: '/' });
				event.cookies.delete('jwt_access', { path: '/' });
				event.cookies.delete('refresh_token', { path: '/' });
				event.cookies.delete('jwt_refresh', { path: '/' });
				event.cookies.delete('org', { path: '/' });
				event.cookies.delete('org_name', { path: '/' });
			}
		}
	}

	// Set user in locals
	if (user) {
		event.locals.user = user;

		// Check if org cookie is set
		if (orgId) {
			// Verify user has access to this organization
			const userOrg = user.organizations?.find((org) => org.id === orgId);

			if (userOrg) {
				// OPTIMIZATION: Check if token already has correct org context
				// This avoids unnecessary API calls on every request
				if (tokenHasOrgContext(accessToken, orgId)) {
					// Token already has org context, just get profile
					const profile = await getProfile(accessToken);

					if (profile) {
						event.locals.org = profile.org;
						event.locals.profile = profile;
						event.locals.org_name = profile.org.name;
					} else {
						// Profile fetch failed, clear org cookies
						event.cookies.delete('org', { path: '/' });
						event.cookies.delete('org_name', { path: '/' });
					}
				} else {
					// Token doesn't have org context, need to switch
					const switchResult = await switchOrg(accessToken, orgId);

					if (switchResult) {
						// Update cookies with new tokens that have org context
						event.cookies.set('jwt_access', switchResult.access_token, {
							path: '/',
							httpOnly: true,
							sameSite: 'lax',
							secure: process.env.NODE_ENV === 'production',
							maxAge: 60 * 60 * 24 // 1 day
						});
						event.cookies.set('jwt_refresh', switchResult.refresh_token, {
							path: '/',
							httpOnly: true,
							sameSite: 'lax',
							secure: process.env.NODE_ENV === 'production',
							maxAge: 60 * 60 * 24 * 365 // 1 year
						});

						// Update accessToken for profile fetch
						accessToken = switchResult.access_token;

						// Get profile using the new token
						const profile = await getProfile(accessToken);

						if (profile) {
							event.locals.org = profile.org;
							event.locals.profile = profile;
							event.locals.org_name = switchResult.current_org?.name || profile.org.name;
						} else {
							// Profile fetch failed, clear org cookies
							event.cookies.delete('org', { path: '/' });
							event.cookies.delete('org_name', { path: '/' });
						}
					} else {
						// Org switch failed, clear org cookies
						event.cookies.delete('org', { path: '/' });
						event.cookies.delete('org_name', { path: '/' });
					}
				}
			} else {
				// User doesn't have access to this organization, clear org cookies
				event.cookies.delete('org', { path: '/' });
				event.cookies.delete('org_name', { path: '/' });
				// Don't throw error here, just redirect
				throw redirect(307, '/org');
			}
		}
	}

	// Route protection
	const pathname = event.url.pathname;

	// Check if the route starts with /app
	if (pathname.startsWith('/app')) {
		if (!user) {
			// User not authenticated
			throw redirect(307, '/login');
		}

		// For /app routes, also ensure an organization is selected
		if (!event.locals.org) {
			// If user is authenticated but no org is selected, redirect to org selection page
			throw redirect(307, '/org');
		}
	}
	// Handle admin routes - only allow micropyramid.com domain users
	else if (pathname.startsWith('/admin')) {
		if (!user) {
			throw redirect(307, '/login');
		}

		// Check if user's email domain is micropyramid.com
		if (!user.email || !user.email.endsWith('@micropyramid.com')) {
			throw redirect(307, '/app');
		}
	}
	// Handle other protected routes
	else if (pathname.startsWith('/org')) {
		if (!user) {
			throw redirect(307, '/login');
		}
	}

	return resolve(event);
}
