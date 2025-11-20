/**
 * Contact Detail Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/contacts/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Fetch contact details from Django
		const response = await apiRequest(
			`/contacts/${params.contactId}/`,
			{},
			{ cookies, org }
		);

		if (!response.contact_obj) {
			return {
				status: 404,
				error: new Error('Contact not found')
			};
		}

		const contactData = response.contact_obj;

		// Transform contact data
		const contact = {
			id: contactData.id,
			firstName: contactData.first_name,
			lastName: contactData.last_name,
			email: contactData.email,
			phone: contactData.phone,
			title: contactData.title,
			department: contactData.department,
			description: contactData.description,
			createdAt: contactData.created_at,
			updatedAt: contactData.updated_at,
			organizationId: contactData.org?.id || org.id,
			ownerId: contactData.created_by?.id || null,

			// Owner info
			owner: contactData.assigned_to && contactData.assigned_to.length > 0
				? {
					id: contactData.assigned_to[0].id,
					name: contactData.assigned_to[0].user_details?.email || contactData.assigned_to[0].email,
					email: contactData.assigned_to[0].user_details?.email || contactData.assigned_to[0].email
				}
				: contactData.created_by
					? {
						id: contactData.created_by.id,
						name: contactData.created_by.email,
						email: contactData.created_by.email
					}
					: null
		};

		// Transform account relationships
		const accountRelationships = (contactData.accounts || response.accounts_list || []).map(account => ({
			account: {
				id: account.id,
				name: account.name,
				industry: account.industry,
				email: account.email
			},
			isPrimary: account.is_primary || false,
			role: account.role || null,
			startDate: account.start_date || null
		}));

		// Transform opportunities
		const opportunities = (response.opportunity_list || []).map(opp => ({
			id: opp.id,
			name: opp.name,
			amount: opp.amount ? Number(opp.amount) : null,
			stage: opp.stage,
			probability: opp.probability,
			closedOn: opp.closed_on,
			createdAt: opp.created_at,
			account: opp.account ? {
				id: opp.account.id,
				name: opp.account.name
			} : null
		}));

		// Transform tasks
		const tasks = (response.tasks || []).map(task => ({
			id: task.id,
			title: task.title,
			status: task.status,
			priority: task.priority,
			dueDate: task.due_date,
			createdAt: task.created_at,
			owner: task.assigned_to && task.assigned_to.length > 0 ? {
				id: task.assigned_to[0].id,
				name: task.assigned_to[0].user_details?.email || task.assigned_to[0].email
			} : null
		})).slice(0, 5);

		// Transform events (Django may return these)
		const events = (response.events || []).map(event => ({
			id: event.id,
			name: event.name,
			startDate: event.start_date,
			startTime: event.start_time,
			endDate: event.end_date,
			status: event.status,
			createdAt: event.created_at,
			owner: event.assigned_to && event.assigned_to.length > 0 ? {
				id: event.assigned_to[0].id,
				name: event.assigned_to[0].user_details?.email || event.assigned_to[0].email
			} : null
		})).slice(0, 5);

		return {
			contact: {
				...contact,
				accountRelationships,
				opportunities,
				tasks,
				events
			}
		};
	} catch (err) {
		console.error('Error loading contact data:', err);
		throw error(500, `Failed to load contact: ${err.message}`);
	}
}
