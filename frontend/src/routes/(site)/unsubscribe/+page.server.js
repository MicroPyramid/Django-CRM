/**
 * Unsubscribe Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: POST /api/marketing/newsletter/unsubscribe/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { fail } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import axios from 'axios';

/** @type {import('./$types').PageServerLoad} */
export async function load({ url }) {
	const token = url.searchParams.get('token');

	if (!token) {
		return {
			error: 'Invalid unsubscribe link. Please check your email for the correct link.'
		};
	}

	try {
		const apiUrl = env.DJANGO_API_URL || 'http://localhost:8000';

		// Verify token with Django API
		const response = await axios.get(
			`${apiUrl}/api/marketing/newsletter/subscribers/`,
			{
				params: { token: token },
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);

		// Django should return subscriber info
		const subscriber = response.data?.subscriber || response.data;

		if (!subscriber) {
			return {
				error: 'Invalid unsubscribe token. This link may have expired or already been used.'
			};
		}

		return {
			subscriber: {
				email: subscriber.email,
				token: token
			}
		};
	} catch (error) {
		console.error('Unsubscribe load error:', error);
		return {
			error: 'An error occurred while processing your request. Please try again later.'
		};
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	unsubscribe: async ({ request }) => {
		const formData = await request.formData();
		const token = formData.get('token')?.toString();

		if (!token) {
			return fail(400, { message: 'Invalid unsubscribe token' });
		}

		try {
			const apiUrl = env.DJANGO_API_URL || 'http://localhost:8000';

			// Unsubscribe via Django API
			const response = await axios.post(
				`${apiUrl}/api/marketing/newsletter/unsubscribe/`,
				{
					token: token
				},
				{
					headers: {
						'Content-Type': 'application/json'
					}
				}
			);

			// Check response
			if (response.data?.message?.toLowerCase().includes('already unsubscribed')) {
				return {
					success: true,
					message: 'You have already been unsubscribed from our newsletter'
				};
			}

			return { success: true, message: 'Successfully unsubscribed from newsletter' };
		} catch (error) {
			console.error('Unsubscribe error:', error);

			if (error.response?.status === 404) {
				return fail(404, { message: 'Subscriber not found or already unsubscribed' });
			}

			if (error.response?.status === 400) {
				return fail(400, {
					message: error.response.data?.error || 'Invalid unsubscribe request'
				});
			}

			return fail(500, { message: 'Failed to unsubscribe. Please try again later.' });
		}
	}
};
