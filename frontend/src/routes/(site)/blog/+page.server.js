/**
 * Blog List Page - API Version
 *
 * Requires Wagtail CMS API integration
 * Potential Django endpoints:
 *   - Wagtail API v2: /api/wagtail/v2/pages/ (if wagtailapi is configured)
 *   - Custom endpoint: /api/blog/posts/ (needs implementation)
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { env } from '$env/dynamic/private';
import axios from 'axios';

/** @type {import('./$types').PageServerLoad} */
export async function load({ url }) {
	try {
		// Pagination parameters
		const page = parseInt(url.searchParams.get('page') || '1', 10);
		const pageSize = 5;
		const offset = (page - 1) * pageSize;

		const apiUrl = env.DJANGO_API_URL || 'http://localhost:8000';

		// NOTE: Wagtail CMS is installed in Django backend, but we need to:
		// 1. Enable Wagtail API (wagtail.api.v2)
		// 2. Configure blog pages endpoint
		// 3. Or create a custom /api/blog/posts/ endpoint
		//
		// For now, returning a note that this needs backend configuration.

		return {
			posts: [],
			pagination: {
				page,
				pageSize,
				totalPosts: 0,
				totalPages: 0,
				hasNextPage: false,
				hasPreviousPage: false
			},
			note:
				'Blog functionality requires Wagtail API configuration. ' +
				'Please enable wagtail.api.v2 and configure a blog pages endpoint, ' +
				'or implement /api/blog/posts/ in Django backend.'
		};

		// Future implementation (when Wagtail API or custom endpoint is available):
		/*
		// Option 1: Using Wagtail API v2
		const response = await axios.get(
			`${apiUrl}/api/wagtail/v2/pages/`,
			{
				params: {
					type: 'blog.BlogPage',  // Adjust based on Wagtail page model
					fields: 'title,slug,excerpt,date',
					order: '-date',
					offset: offset,
					limit: pageSize
				}
			}
		);

		const posts = response.data.items.map(post => ({
			id: post.id,
			title: post.title,
			slug: post.meta.slug,
			excerpt: post.excerpt,
			createdAt: post.date,
			updatedAt: post.meta.last_published_at
		}));

		// Option 2: Using custom Django endpoint
		const response = await axios.get(
			`${apiUrl}/api/blog/posts/`,
			{
				params: {
					draft: false,
					offset: offset,
					limit: pageSize
				}
			}
		);

		const posts = response.data.results.map(post => ({
			id: post.id,
			title: post.title,
			slug: post.slug,
			excerpt: post.excerpt,
			createdAt: post.created_at,
			updatedAt: post.updated_at
		}));

		const totalPosts = response.data.count;
		const totalPages = Math.ceil(totalPosts / pageSize);

		return {
			posts,
			pagination: {
				page,
				pageSize,
				totalPosts,
				totalPages,
				hasNextPage: page < totalPages,
				hasPreviousPage: page > 1
			}
		};
		*/
	} catch (error) {
		console.error('Error loading blog posts:', error);
		return {
			posts: [],
			pagination: {
				page: 1,
				pageSize: 5,
				totalPosts: 0,
				totalPages: 0,
				hasNextPage: false,
				hasPreviousPage: false
			},
			error: 'Failed to load blog posts'
		};
	}
}
