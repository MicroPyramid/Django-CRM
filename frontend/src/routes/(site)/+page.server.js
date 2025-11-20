/**
 * Site Homepage - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: POST /api/marketing/newsletter/subscribe/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { fail } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import axios from 'axios';

/** @type {import('./$types').Actions} */
export const actions = {
	subscribe: async ({ request, getClientAddress }) => {
		const formData = await request.formData();
		const email = formData.get('email')?.toString().trim();

		if (!email) {
			return fail(400, { message: 'Email is required' });
		}

		// Basic email validation
		const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
		if (!emailRegex.test(email)) {
			return fail(400, { message: 'Please enter a valid email address' });
		}

		// Restrict emails with '+' character
		if (email.includes('+')) {
			return fail(400, { message: 'Please enter a valid email address' });
		}

		try {
			const apiUrl = env.DJANGO_API_URL || 'http://localhost:8000';

			// Subscribe via Django API
			const response = await axios.post(
				`${apiUrl}/api/marketing/newsletter/subscribe/`,
				{
					email: email,
					ip_address: getClientAddress(),
					user_agent: request.headers.get('user-agent')
				},
				{
					headers: {
						'Content-Type': 'application/json'
					}
				}
			);

			// Django should return success response
			return { success: true, message: 'Successfully subscribed to newsletter' };
		} catch (error) {
			console.error('Newsletter subscription error:', error);

			// Check if it's an already subscribed error
			if (error.response?.status === 400) {
				const errorMessage = error.response.data?.error || error.response.data?.message;
				if (errorMessage?.toLowerCase().includes('already subscribed')) {
					return fail(400, { message: 'You are already subscribed to our newsletter' });
				}
				return fail(400, { message: errorMessage || 'Invalid subscription request' });
			}

			return fail(500, { message: 'Failed to subscribe. Please try again later.' });
		}
	}
};
