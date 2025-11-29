/**
 * Case Detail Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/cases/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const org = locals.org;
	const caseId = params.caseId;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Fetch case details from Django
		const response = await apiRequest(`/cases/${caseId}/`, {}, { cookies, org });

		if (!response.cases_obj) {
			throw error(404, 'Case not found');
		}

		const caseData = response.cases_obj;

		// Transform case data
		const caseItem = {
			id: caseData.id,
			subject: caseData.name,
			description: caseData.description,
			status: caseData.status,
			priority: caseData.priority,
			caseType: caseData.case_type,
			closedOn: caseData.closed_on,
			createdAt: caseData.created_at,
			updatedAt: caseData.updated_at,

			// Owner
			owner:
				caseData.assigned_to && caseData.assigned_to.length > 0
					? {
							id: caseData.assigned_to[0].id,
							name: caseData.assigned_to[0].user_details?.email || caseData.assigned_to[0].email
						}
					: null,

			// Account
			account: caseData.account
				? {
						id: caseData.account.id,
						name: caseData.account.name
					}
				: null,

			// Comments
			comments: (response.comments || []).map((comment) => ({
				id: comment.id,
				body: comment.comment,
				createdAt: comment.created_at,
				author: comment.commented_by
					? {
							id: comment.commented_by.id,
							name: comment.commented_by.user_details?.email || comment.commented_by.email
						}
					: null
			}))
		};

		return { caseItem };
	} catch (err) {
		console.error('Error loading case data:', err);
		throw error(500, `Failed to load case: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	comment: async ({ request, params, locals, cookies }) => {
		const org = locals.org;

		try {
			const form = await request.formData();
			const body = form.get('body')?.toString().trim();

			if (!body) {
				return fail(400, { error: 'Comment cannot be empty.' });
			}

			// Add comment via API
			await apiRequest(
				`/cases/comment/${params.caseId}/`,
				{
					method: 'POST',
					body: { comment: body }
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error adding comment:', err);
			return fail(500, { error: 'Failed to add comment' });
		}
	}
};
