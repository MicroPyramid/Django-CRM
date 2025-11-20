/**
 * Login Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: POST /api/auth/google/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import axios from 'axios';
import { redirect } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

/**
 * @param {Object} params - OAuth parameters
 * @param {string} params.access_token - Access token
 */
async function fetchUserData(params) {
	const url = 'https://www.googleapis.com/oauth2/v1/userinfo';

	try {
		const response = await axios.get(url, {
			params,
			headers: {},
			timeout: 60000 // timeout in milliseconds
		});
		return response.data;
	} catch (error) {
		console.error('Error fetching user data:', error);
		throw error;
	}
}

/** @type {import('@sveltejs/kit').ServerLoad} */
export async function load({ url, cookies }) {
	const code = url.searchParams.get('code');
	const redirect_uri = env.GOOGLE_LOGIN_DOMAIN + '/login';

	// Check if we have a Google OAuth code
	if (code != null) {
		const tokenParams = {
			grant_type: 'authorization_code',
			code,
			redirect_uri,
			client_id: env.GOOGLE_CLIENT_ID,
			client_secret: env.GOOGLE_CLIENT_SECRET
		};

		let info;
		try {
			const response = await axios.post(
				'https://accounts.google.com/o/oauth2/token',
				tokenParams
			);
			info = response.data;
		} catch (error) {
			console.error('Error getting OAuth token:', error);
			throw redirect(307, '/login?error=oauth_failed');
		}

		// Get user info from Google
		const user_info = await fetchUserData({ access_token: info.access_token });

		try {
			// Authenticate with Django backend using Google token
			const apiUrl = env.DJANGO_API_URL || 'http://localhost:8000';
			const djangoResponse = await axios.post(`${apiUrl}/api/auth/google/`, {
				token: info.access_token
			});

			// Django returns JWT tokens (access_token, refresh_token)
			const { access_token: access, refresh_token: refresh } = djangoResponse.data;

			// Store JWT tokens in cookies
			await cookies.set('jwt_access', access, {
				path: '/',
				httpOnly: true,
				sameSite: 'strict',
				secure: env.NODE_ENV === 'production',
				maxAge: 60 * 60 * 24 // 1 day for access token
			});

			await cookies.set('jwt_refresh', refresh, {
				path: '/',
				httpOnly: true,
				sameSite: 'strict',
				secure: env.NODE_ENV === 'production',
				maxAge: 60 * 60 * 24 * 365 // 1 year for refresh token
			});

			// Also store user email for convenience
			await cookies.set('user_email', user_info.email, {
				path: '/',
				httpOnly: true,
				sameSite: 'strict',
				secure: env.NODE_ENV === 'production',
				maxAge: 60 * 60 * 24 * 7
			});
		} catch (error) {
			console.error('Error authenticating with Django:', error);
			throw redirect(307, '/login?error=auth_failed');
		}

		// Authentication successful, redirect to org selection (outside try-catch)
		throw redirect(307, '/org');
	}

	// Check for existing JWT token
	const jwtAccess = cookies.get('jwt_access');
	if (jwtAccess) {
		// User already authenticated, redirect to org selection
		throw redirect(307, '/org');
	}

	// Build Google OAuth URL
	const google_login_url =
		'https://accounts.google.com/o/oauth2/auth?client_id=' +
		env.GOOGLE_CLIENT_ID +
		'&response_type=code' +
		'&scope=https://www.googleapis.com/auth/userinfo.profile ' +
		'https://www.googleapis.com/auth/userinfo.email' +
		'&redirect_uri=' +
		redirect_uri +
		'&state=google';

	return { google_url: google_login_url };
}
