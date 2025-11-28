/**
 * Edit Invoice Page - API Version
 *
 * This is the migrated version that uses Django REST API instead of Prisma.
 * Once tested and working, activate by:
 *   1. mv +page.server.js +page.server.prisma.js
 *   2. mv +page.server.api.js +page.server.js
 *
 * Migration completed: 2025-11-19
 * Django endpoint: PUT /api/invoices/{id}/
 *
 * NOTE: Django's Invoice model with InvoiceLineItem maps to SvelteKit's Quote with QuoteLineItem
 */

import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	if (!locals.user || !locals.org) {
		throw redirect(302, '/login');
	}

	try {
		// Get invoice and accounts in parallel
		const [invoice, accountsResponse] = await Promise.all([
			apiRequest(`/invoices/${params.invoiceId}/`, {}, { cookies, org: locals.org }),
			apiRequest('/accounts/?status=open&limit=1000', {}, { cookies, org: locals.org })
		]);

		if (!invoice) {
			throw error(404, 'Invoice not found');
		}

		// Transform invoice to Quote format
		const transformedInvoice = transformInvoiceToQuote(invoice);

		// Extract accounts from Django response
		let accounts = [];
		if (accountsResponse.active_accounts?.open_accounts) {
			accounts = accountsResponse.active_accounts.open_accounts;
		} else if (accountsResponse.results) {
			accounts = accountsResponse.results.filter((acc) => !acc.status || acc.status === 'open');
		}

		const transformedAccounts = accounts.map((acc) => ({
			id: acc.id,
			name: acc.name
		}));

		return {
			invoice: transformedInvoice,
			accounts: transformedAccounts
		};
	} catch (err) {
		if (err.message.includes('404') || err.message.includes('not found')) {
			throw error(404, 'Invoice not found');
		}
		console.error('Failed to load invoice:', err);
		throw error(500, {
			message: 'Failed to load invoice. Please try again.',
			details: err.message
		});
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	default: async ({ request, params, locals, cookies }) => {
		if (!locals.user || !locals.org) {
			return fail(401, { error: 'Unauthorized' });
		}

		const formData = await request.formData();

		const accountId = String(formData.get('account_id') || '');
		const invoiceDate = String(formData.get('invoice_date') || '');
		const dueDate = String(formData.get('due_date') || '');
		const status = String(formData.get('status') || 'DRAFT');
		const notes = String(formData.get('notes') || '');

		// Validation
		if (!accountId || !invoiceDate || !dueDate) {
			return fail(400, {
				error: 'Account, invoice date, and due date are required'
			});
		}

		try {
			// First, verify the invoice exists
			const existingInvoice = await apiRequest(
				`/invoices/${params.invoiceId}/`,
				{},
				{ cookies, org: locals.org }
			);

			if (!existingInvoice) {
				return fail(404, { error: 'Invoice not found' });
			}

			// Transform status
			const djangoStatus = mapQuoteStatusToInvoiceStatus(status);

			// Update invoice via Django API
			const updateData = {
				accounts: [accountId],
				status: djangoStatus,
				details: notes,
				due_date: dueDate
			};

			await apiRequest(
				`/invoices/${params.invoiceId}/`,
				{
					method: 'PUT',
					body: updateData
				},
				{ cookies, org: locals.org }
			);

			// Redirect to invoice detail page
			throw redirect(303, `/invoices/${params.invoiceId}`);
		} catch (err) {
			if (err instanceof Response) throw err; // Re-throw redirects

			console.error('Error updating invoice:', err);

			if (err.message.includes('404') || err.message.includes('not found')) {
				return fail(404, { error: 'Invoice not found' });
			}

			return fail(500, {
				error: 'Failed to update invoice. Please try again.'
			});
		}
	}
};

/**
 * Transform Django Invoice to SvelteKit Quote format
 *
 * @param {Object} invoice - Django invoice object
 * @returns {Object} SvelteKit-compatible quote object
 */
function transformInvoiceToQuote(invoice) {
	return {
		id: invoice.id,
		quoteNumber: invoice.invoice_number || `INV-${invoice.id.substring(0, 8)}`,
		name: invoice.invoice_title || invoice.name || 'Untitled Invoice',
		status: mapInvoiceStatusToQuoteStatus(invoice.status),
		description: invoice.details || null,
		expirationDate: invoice.due_date ? new Date(invoice.due_date) : null,

		// Account relationship
		account: invoice.accounts?.[0]
			? {
					id: invoice.accounts[0].id,
					name: invoice.accounts[0].name
				}
			: null,

		// Line items
		lineItems:
			invoice.line_items?.map((item) => ({
				id: item.id,
				quantity: parseFloat(item.quantity) || 1,
				listPrice: item.unit_price || '0.00',
				unitPrice: item.unit_price || '0.00',
				discount: '0.00',
				totalPrice: item.total || '0.00',
				description: item.description || null,
				product: item.product
					? {
							id: item.product.id,
							name: item.product_name || item.product.name,
							code: item.product.sku || null
						}
					: null
			})) || [],

		// Timestamps
		createdAt: new Date(invoice.created_at),
		updatedAt: new Date(invoice.created_at)
	};
}

/**
 * Map SvelteKit Quote status to Django Invoice status
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

/**
 * Map Django Invoice status to SvelteKit Quote status
 *
 * @param {string} djangoStatus - Django invoice status
 * @returns {string} SvelteKit quote status
 */
function mapInvoiceStatusToQuoteStatus(djangoStatus) {
	const statusMap = {
		Draft: 'DRAFT',
		Sent: 'PRESENTED',
		Paid: 'ACCEPTED',
		Pending: 'IN_REVIEW',
		Cancelled: 'REJECTED'
	};

	return statusMap[djangoStatus] || 'DRAFT';
}
