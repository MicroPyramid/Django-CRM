/**
 * Lead Detail Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/leads/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 *
 * Note: Lead conversion is complex in Django and may require custom endpoint
 */

import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const lead_id = params.lead_id;
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Fetch lead details from Django
		const response = await apiRequest(
			`/leads/${lead_id}/`,
			{},
			{ cookies, org }
		);

		if (!response.lead_obj) {
			throw error(404, 'Lead not found');
		}

		const leadData = response.lead_obj;

		// Transform lead data
		const lead = {
			id: leadData.id,
			firstName: leadData.first_name,
			lastName: leadData.last_name,
			company: leadData.company?.name || null,
			email: leadData.email,
			phone: leadData.phone,
			title: leadData.title,
			industry: leadData.industry,
			website: leadData.website,
			description: leadData.description,
			leadSource: leadData.source,
			status: leadData.status,
			isConverted: leadData.is_converted || leadData.status === 'converted',
			convertedAt: leadData.converted_at || null,
			convertedContactId: leadData.converted_contact_id || null,
			convertedAccountId: leadData.converted_account_id || null,
			convertedOpportunityId: leadData.converted_opportunity_id || null,
			createdAt: leadData.created_at,
			updatedAt: leadData.updated_at,
			organizationId: leadData.org?.id || org.id,
			ownerId: leadData.created_by?.id || null,

			// Owner info
			owner: leadData.assigned_to && leadData.assigned_to.length > 0
				? {
					id: leadData.assigned_to[0].id,
					name: leadData.assigned_to[0].user_details?.email || leadData.assigned_to[0].email,
					email: leadData.assigned_to[0].user_details?.email || leadData.assigned_to[0].email
				}
				: leadData.created_by
					? {
						id: leadData.created_by.id,
						name: leadData.created_by.email,
						email: leadData.created_by.email
					}
					: null,

			// Contact info (if converted)
			contact: leadData.contact ? {
				id: leadData.contact.id,
				firstName: leadData.contact.first_name,
				lastName: leadData.contact.last_name,
				email: leadData.contact.email
			} : null
		};

		// Transform tasks
		const tasks = (response.tasks || leadData.tasks || []).map(task => ({
			id: task.id,
			title: task.title,
			status: task.status,
			priority: task.priority,
			dueDate: task.due_date,
			createdAt: task.created_at
		}));

		// Transform events (Django may return these separately)
		const events = (response.events || leadData.events || []).map(event => ({
			id: event.id,
			name: event.name,
			startDate: event.start_date,
			startTime: event.start_time,
			endDate: event.end_date,
			status: event.status
		}));

		// Transform comments
		const comments = (response.comments || []).map(comment => ({
			id: comment.id,
			body: comment.comment,
			createdAt: comment.created_at,
			author: comment.commented_by ? {
				id: comment.commented_by.id,
				name: comment.commented_by.user_details?.email || comment.commented_by.email,
				email: comment.commented_by.user_details?.email || comment.commented_by.email
			} : null
		}));

		return {
			lead: {
				...lead,
				tasks,
				events,
				comments
			}
		};
	} catch (err) {
		console.error('Error loading lead data:', err);
		throw error(500, `Failed to load lead: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	convert: async ({ params, locals, cookies }) => {
		const lead_id = params.lead_id;
		const org = locals.org;

		try {
			console.log('Starting lead conversion for lead:', lead_id);

			const response = await apiRequest(
				`/leads/${lead_id}/`,
				{
					method: 'PATCH',
					body: {
						status: 'converted',
						is_converted: true
					}
				},
				{ cookies, org }
			);

			// Return success with account ID for redirect
			return {
				status: 'success',
				message: response.message || 'Lead converted successfully',
				accountId: response.account_id,
				contactId: response.contact_id,
				redirectTo: response.account_id ? `/accounts/${response.account_id}` : null
			};
		} catch (err) {
			console.error('Error converting lead:', err);

			let errorMessage = 'Failed to convert lead';
			if (err instanceof Error) {
				errorMessage = err.message;
			}

			return fail(500, {
				status: 'error',
				message: `Error converting lead: ${errorMessage}`
			});
		}
	},

	addComment: async ({ params, request, locals, cookies }) => {
		const lead_id = params.lead_id;
		const org = locals.org;

		try {
			const data = await request.formData();
			const comment = data.get('comment')?.toString().trim();

			if (!comment || comment.length === 0) {
				return fail(400, { status: 'error', message: 'Comment cannot be empty' });
			}

			if (comment.length > 1000) {
				return fail(400, { status: 'error', message: 'Comment too long (max 1000 characters)' });
			}

			// Add comment via API
			await apiRequest(
				`/leads/comment/${lead_id}/`,
				{
					method: 'POST',
					body: { comment }
				},
				{ cookies, org }
			);

			// Fetch updated comments
			const response = await apiRequest(
				`/leads/${lead_id}/`,
				{},
				{ cookies, org }
			);

			const comments = (response.comments || []).map(comment => ({
				id: comment.id,
				body: comment.comment,
				createdAt: comment.created_at,
				author: comment.commented_by ? {
					id: comment.commented_by.id,
					name: comment.commented_by.user_details?.email || comment.commented_by.email,
					email: comment.commented_by.user_details?.email || comment.commented_by.email
				} : null
			}));

			return {
				status: 'success',
				message: 'Comment added successfully',
				commentAdded: true,
				comments
			};
		} catch (err) {
			console.error('Error adding comment:', err);
			return fail(500, { status: 'error', message: 'Failed to add comment' });
		}
	}
};
