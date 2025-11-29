/**
 * Tasks Main Page (Kanban Boards List) - API Version
 *
 * Migrated from Prisma to Django REST API
 * Displays user's Kanban boards and allows creating new boards
 *
 * ⚠️ NOTE: This page requires Django Boards API (Phase 3 feature)
 * Django Endpoints (to be implemented):
 * - GET  /api/boards/                  - List user's boards
 * - POST /api/boards/                  - Create new board with default columns
 *
 * Until boards API is implemented, this returns empty list.
 */

import { fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
	const user = locals.user;
	const org = locals.org;

	try {
		// Fetch boards from Django API (Phase 3 feature - now implemented)
		const data = await apiRequest('/boards/', {}, { cookies, org });

		// Transform Django response to match Prisma format
		const boards = (data.results || []).map((board) => ({
			id: board.id,
			name: board.name,
			createdAt: new Date(board.created_at),
			ownerId: board.owner?.id || user.id,
			// Additional fields from Django
			isArchived: board.is_archived || false,
			_count: {
				columns: board.columns?.length || 0,
				members: board.members?.length || 0
			}
		}));

		return { boards };
	} catch (err) {
		console.error('Error loading boards:', err);

		// Graceful fallback if API has issues
		return {
			boards: [],
			error: err.message
		};
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	/**
	 * Create new board with default columns
	 */
	create: async ({ request, locals, cookies }) => {
		const user = locals.user;
		const org = locals.org;

		try {
			const formData = await request.formData();
			const name = formData.get('name')?.toString();

			if (!name) {
				return fail(400, { error: 'Board name is required' });
			}

			// Create board via Django API
			// Django will automatically create default columns (To Do, In Progress, Done)
			const boardData = {
				name
				// owner is set automatically from request.profile in Django
				// default columns are created automatically in Django backend
			};

			await apiRequest(
				'/boards/',
				{
					method: 'POST',
					body: boardData
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error creating board:', err);

			if (err.message.includes('404') || err.message.includes('Not Found')) {
				return fail(404, {
					error: 'Boards API endpoint not found',
					details: err.message
				});
			}

			return fail(500, { error: err.message || 'Failed to create board' });
		}
	}
};
