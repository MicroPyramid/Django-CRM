/**
 * Account Detail Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/accounts/{id}/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, url, locals, cookies }) {
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		const accountId = params.accountId;

		// If ?commentsOnly=1, return just comments as JSON (for live updates)
		if (url.searchParams.get('commentsOnly') === '1') {
			const response = await apiRequest(
				`/accounts/${accountId}/`,
				{},
				{ cookies, org }
			);

			const comments = (response.comments || []).map(comment => ({
				id: comment.id,
				body: comment.comment,
				createdAt: comment.created_at,
				author: comment.commented_by ? {
					id: comment.commented_by.id,
					name: comment.commented_by.user_details?.email || comment.commented_by.email
				} : null
			}));

			return new Response(JSON.stringify({ comments }), {
				headers: { 'Content-Type': 'application/json' }
			});
		}

		// Fetch full account details from Django
		const response = await apiRequest(
			`/accounts/${accountId}/`,
			{},
			{ cookies, org }
		);

		if (!response.account_obj) {
			throw error(404, 'Account not found');
		}

		const accountData = response.account_obj;

		// Transform account data
		const account = {
			id: accountData.id,
			name: accountData.name,
			email: accountData.email,
			phone: accountData.phone,
			website: accountData.website,
			industry: accountData.industry,
			description: accountData.description,
			billingAddress: accountData.billing_address_line,
			billingCity: accountData.billing_city,
			billingState: accountData.billing_state,
			billingPostcode: accountData.billing_postcode,
			billingCountry: accountData.billing_country,
			status: accountData.status,
			isActive: accountData.status === 'open' || accountData.is_active,
			createdAt: accountData.created_at,
			updatedAt: accountData.updated_at,
			closedAt: accountData.closed_at || null,
			closureReason: accountData.closure_reason || null,
			organizationId: accountData.org?.id || org.id,
			ownerId: accountData.created_by?.id || null
		};

		// Transform contacts
		const contacts = (response.contacts || []).map(contact => ({
			id: contact.id,
			firstName: contact.first_name,
			lastName: contact.last_name,
			email: contact.email,
			phone: contact.phone,
			title: contact.title,
			isPrimary: contact.is_primary || false,
			role: contact.role || null
		}));

		// Transform opportunities
		const opportunities = (response.opportunity_list || []).map(opp => ({
			id: opp.id,
			name: opp.name,
			amount: opp.amount ? Number(opp.amount) : null,
			stage: opp.stage,
			probability: opp.probability,
			closedOn: opp.closed_on
		}));

		// Transform comments
		const comments = (response.comments || []).map(comment => ({
			id: comment.id,
			body: comment.comment,
			createdAt: comment.created_at,
			author: comment.commented_by ? {
				id: comment.commented_by.id,
				name: comment.commented_by.user_details?.email || comment.commented_by.email
			} : null
		}));

		// Transform quotes/invoices
		const quotes = (response.invoices || []).map(invoice => ({
			id: invoice.id,
			name: invoice.invoice_title || invoice.name,
			total: invoice.total_amount ? Number(invoice.total_amount) : null,
			status: invoice.status
		}));

		// Transform tasks
		const tasks = (response.tasks || []).map(task => ({
			id: task.id,
			title: task.title,
			status: task.status,
			priority: task.priority,
			dueDate: task.due_date,
			owner: task.assigned_to && task.assigned_to.length > 0 ? {
				id: task.assigned_to[0].id,
				name: task.assigned_to[0].user_details?.email || task.assigned_to[0].email
			} : null
		}));

		// Transform cases
		const cases = (response.cases || []).map(caseItem => ({
			id: caseItem.id,
			subject: caseItem.name,
			status: caseItem.status,
			priority: caseItem.priority,
			closedOn: caseItem.closed_on
		}));

		// Transform users
		const users = (response.users || []).map(user => ({
			id: user.id,
			name: user.user_details?.email || user.email,
			email: user.user_details?.email || user.email
		}));

		return {
			account,
			contacts,
			opportunities,
			comments,
			quotes,
			tasks,
			cases,
			users,
			meta: {
				title: account.name,
				description: `Account details for ${account.name}`
			}
		};
	} catch (err) {
		console.error('Error loading account data:', err);
		const errorMessage = err instanceof Error ? err.message : 'Error loading account data';
		const statusCode = err && typeof err === 'object' && 'status' in err ?
			(typeof err.status === 'number' ? err.status : 500) : 500;
		throw error(statusCode, errorMessage);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	closeAccount: async ({ request, locals, params, cookies }) => {
		try {
			const user = locals.user;
			const org = locals.org;
			const { accountId } = params;
			const formData = await request.formData();
			const closureReason = formData.get('closureReason')?.toString();

			if (!closureReason) {
				return fail(400, { success: false, message: 'Please provide a reason for closing this account' });
			}

			// Close account via API (Django may not have dedicated endpoint, use PATCH)
			await apiRequest(
				`/accounts/${accountId}/`,
				{
					method: 'PATCH',
					body: {
						status: 'close',
						closure_reason: closureReason,
						is_active: false
					}
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error closing account:', err);
			return fail(500, { success: false, message: 'An unexpected error occurred' });
		}
	},

	reopenAccount: async ({ request, locals, params, cookies }) => {
		try {
			const user = locals.user;
			const org = locals.org;
			const { accountId } = params;

			// Reopen account via API
			await apiRequest(
				`/accounts/${accountId}/`,
				{
					method: 'PATCH',
					body: {
						status: 'open',
						closure_reason: null,
						is_active: true
					}
				},
				{ cookies, org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error reopening account:', err);
			return fail(500, { success: false, message: 'An unexpected error occurred' });
		}
	},

	comment: async ({ request, locals, params, cookies }) => {
		try {
			const org = locals.org;
			const form = await request.formData();
			const body = form.get('body')?.toString().trim();

			if (!body) {
				return fail(400, { error: 'Comment cannot be empty.' });
			}

			// Add comment via API
			await apiRequest(
				`/accounts/comment/${params.accountId}/`,
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
