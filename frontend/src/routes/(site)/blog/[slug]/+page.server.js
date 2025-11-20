/**
 * Blog Detail Page - API Version
 *
 * This is the migrated version that uses Django REST API instead of Prisma.
 * Once tested and working, activate by:
 *   1. mv +page.server.js +page.server.prisma.js
 *   2. mv +page.server.api.js +page.server.js
 *
 * Migration completed: 2025-11-19
 * Django endpoint: GET /api/blog/posts/public/{slug}/
 *
 * NOTE: This is a public endpoint that doesn't require authentication
 */

import { error } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params }) {
	const { slug } = params;

	try {
		// Build API URL for public blog post by slug
		const API_BASE_URL = process.env.DJANGO_API_URL ? `${process.env.DJANGO_API_URL}/api` : 'http://localhost:8000/api';
		const apiUrl = `${API_BASE_URL}/blog/posts/public/${slug}/`;

		// Fetch post from Django API (no auth required for public posts)
		const response = await fetch(apiUrl, {
			headers: {
				'Content-Type': 'application/json'
			}
		});

		if (!response.ok) {
			if (response.status === 404) {
				throw error(404, 'Blog post not found');
			}
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		const djangoPost = await response.json();

		// Transform Django BlogPost to match SvelteKit format
		const post = {
			id: djangoPost.id,
			title: djangoPost.title,
			slug: djangoPost.slug,
			content: djangoPost.content,
			excerpt: djangoPost.excerpt || null,
			draft: djangoPost.status !== 'published',
			createdAt: new Date(djangoPost.created_at),
			updatedAt: new Date(djangoPost.updated_at),

			// Content blocks transformation
			// Django: content_blocks array
			// SvelteKit: contentBlocks array
			contentBlocks:
				djangoPost.content_blocks?.map((block) => ({
					id: block.id,
					type: block.block_type, // 'text', 'image', 'code'
					content: block.content,
					settings: block.settings || {},
					displayOrder: block.order || 0
				})) || []
		};

		return { post };
	} catch (err) {
		console.error('Error loading blog post:', err);

		if (err.status === 404) {
			throw err;
		}

		throw error(404, 'Blog post not found');
	}
}
