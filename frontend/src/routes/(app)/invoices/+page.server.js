/**
 * Invoices List Page - API Version
 *
 * This is the migrated version that uses Django REST API instead of Prisma.
 * Once tested and working, activate by:
 *   1. mv +page.server.js +page.server.prisma.js
 *   2. mv +page.server.api.js +page.server.js
 *
 * Migration completed: 2025-11-19
 * Django endpoint: GET /api/invoices/
 *
 * NOTE: Django's Invoice model with InvoiceLineItem maps to SvelteKit's Quote with QuoteLineItem
 */

import { error, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
	if (!locals.user || !locals.org) {
		throw redirect(302, '/login');
	}

	try {
		// Get invoices from Django API
		// Django returns: { results: [...], count: N }
		const response = await apiRequest('/invoices/', {}, { cookies, org: locals.org });

		// Transform Django Invoice to match SvelteKit Quote structure
		const invoices = (response.results || []).map((invoice) =>
			transformInvoiceToQuote(invoice)
		);

		return {
			invoices
		};
	} catch (err) {
		console.error('Failed to load invoices:', err);
		throw error(500, {
			message: 'Failed to load invoices. Please try again.',
			details: err.message
		});
	}
}

/**
 * Transform Django Invoice to SvelteKit Quote format
 *
 * Django structure:
 * - invoice_title, invoice_number, status, due_date, total_amount
 * - line_items: [{ product, quantity, unit_price, total }]
 * - accounts: [{ id, name }]
 *
 * SvelteKit structure:
 * - name (from invoice_title), quoteNumber, status, expirationDate (from due_date), grandTotal
 * - lineItems: [{ product, quantity, unitPrice, totalPrice }]
 * - account: { id, name }
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

		// Amounts - Django uses total_amount, amount_due, amount_paid
		// SvelteKit uses subtotal, discountAmount, taxAmount, grandTotal
		subtotal: invoice.total_amount || '0.00',
		discountAmount: '0.00', // Not in Django Invoice model
		taxAmount: invoice.tax || '0.00',
		grandTotal: invoice.total_amount || '0.00',

		// Billing address - Django has Address model, SvelteKit has inline fields
		billingStreet: invoice.from_address?.street || null,
		billingCity: invoice.from_address?.city || null,
		billingState: invoice.from_address?.state || null,
		billingPostalCode: invoice.from_address?.postcode || null,
		billingCountry: invoice.from_address?.country || null,

		// Shipping address
		shippingStreet: invoice.to_address?.street || null,
		shippingCity: invoice.to_address?.city || null,
		shippingState: invoice.to_address?.state || null,
		shippingPostalCode: invoice.to_address?.postcode || null,
		shippingCountry: invoice.to_address?.country || null,

		// Timestamps
		createdAt: new Date(invoice.created_at),
		updatedAt: new Date(invoice.created_at), // Django doesn't have updated_at on Invoice

		// Relationships
		account: invoice.accounts?.[0]
			? {
					id: invoice.accounts[0].id,
					name: invoice.accounts[0].name
				}
			: null,

		// Line items transformation
		lineItems:
			invoice.line_items?.map((item) => ({
				id: item.id,
				quantity: parseFloat(item.quantity) || 1,
				listPrice: item.unit_price || '0.00',
				unitPrice: item.unit_price || '0.00',
				discount: '0.00', // Not in Django InvoiceLineItem
				totalPrice: item.total || '0.00',
				description: item.description || null,
				product: item.product
					? {
							id: item.product.id,
							name: item.product_name || item.product.name
						}
					: null
			})) || []
	};
}

/**
 * Map Django Invoice status to SvelteKit Quote status
 *
 * Django: Draft, Sent, Paid, Pending, Cancelled
 * SvelteKit: DRAFT, NEEDS_REVIEW, IN_REVIEW, APPROVED, REJECTED, PRESENTED, ACCEPTED
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
