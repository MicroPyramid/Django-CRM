/**
 * Create Invoice Page - API Version
 *
 * This is the migrated version that uses Django REST API instead of Prisma.
 * Once tested and working, activate by:
 *   1. mv +page.server.js +page.server.prisma.js
 *   2. mv +page.server.api.js +page.server.js
 *
 * Migration completed: 2025-11-19
 * Django endpoint: POST /api/invoices/
 *
 * NOTE: Django's Invoice model with InvoiceLineItem maps to SvelteKit's Quote with QuoteLineItem
 */

import { fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
	if (!locals.user || !locals.org) {
		throw redirect(302, '/login');
	}

	try {
		// Get accounts for the dropdown
		const response = await apiRequest(
			'/accounts/?status=open&limit=1000',
			{},
			{ cookies, org: locals.org }
		);

		// Extract accounts from Django response
		let accounts = [];
		if (response.active_accounts?.open_accounts) {
			accounts = response.active_accounts.open_accounts;
		} else if (response.results) {
			accounts = response.results.filter((acc) => !acc.status || acc.status === 'open');
		}

		// Transform to match SvelteKit format
		const transformedAccounts = accounts.map((acc) => ({
			id: acc.id,
			name: acc.name
		}));

		return {
			accounts: transformedAccounts
		};
	} catch (err) {
		console.error('Failed to load accounts:', err);
		return {
			accounts: []
		};
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ request, locals, cookies }) => {
		if (!locals.user || !locals.org) {
			return fail(401, { error: 'Unauthorized' });
		}

		const formData = await request.formData();

		const invoiceNumber = String(formData.get('invoice_number') || '');
		const accountId = String(formData.get('account_id') || '');
		const invoiceDate = String(formData.get('invoice_date') || '');
		const dueDate = String(formData.get('due_date') || '');
		const status = String(formData.get('status') || 'DRAFT');
		const notes = String(formData.get('notes') || '');

		// Validation
		if (!invoiceNumber || !accountId || !invoiceDate || !dueDate) {
			return fail(400, {
				error: 'Invoice number, account, invoice date, and due date are required'
			});
		}

		try {
			// Create invoice via Django API
			// Transform SvelteKit Quote status to Django Invoice status
			const djangoStatus = mapQuoteStatusToInvoiceStatus(status);

			const invoiceData = {
				invoice_title: `Invoice ${invoiceNumber}`,
				invoice_number: invoiceNumber,
				status: djangoStatus,
				due_date: dueDate,
				details: notes,
				accounts: [accountId], // Django expects array of account IDs
				currency: 'USD',
				total_amount: '0.00', // Will be updated when line items are added
				amount_due: '0.00',
				amount_paid: '0.00'
			};

			const invoice = await apiRequest(
				'/invoices/',
				{
					method: 'POST',
					body: invoiceData
				},
				{ cookies, org: locals.org }
			);

			// Redirect to invoice detail page
			throw redirect(303, `/invoices/${invoice.id}`);
		} catch (error) {
			console.error('Error creating invoice:', error);

			// Check for validation errors
			if (error.message.includes('already exists')) {
				return fail(400, {
					error: 'An invoice with this number already exists'
				});
			}

			return fail(500, {
				error: 'Failed to create invoice. Please try again.'
			});
		}
	}
};

/**
 * Map SvelteKit Quote status to Django Invoice status
 *
 * SvelteKit: DRAFT, NEEDS_REVIEW, IN_REVIEW, APPROVED, REJECTED, PRESENTED, ACCEPTED
 * Django: Draft, Sent, Paid, Pending, Cancelled
 *
 * @param {string} quoteStatus - SvelteKit quote status
 * @returns {string} Django invoice status
 */
function mapQuoteStatusToInvoiceStatus(quoteStatus) {
	const statusMap = {
		DRAFT: 'Draft',
		NEEDS_REVIEW: 'Pending',
		IN_REVIEW: 'Pending',
		APPROVED: 'Sent',
		REJECTED: 'Cancelled',
		PRESENTED: 'Sent',
		ACCEPTED: 'Paid'
	};

	return statusMap[quoteStatus] || 'Draft';
}
