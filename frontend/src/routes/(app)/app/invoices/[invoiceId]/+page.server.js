/**
 * Invoice Detail Page - API Version
 *
 * This is the migrated version that uses Django REST API instead of Prisma.
 * Once tested and working, activate by:
 *   1. mv +page.server.js +page.server.prisma.js
 *   2. mv +page.server.api.js +page.server.js
 *
 * Migration completed: 2025-11-19
 * Django endpoint: GET /api/invoices/{id}/
 *
 * NOTE: Django's Invoice model with InvoiceLineItem maps to SvelteKit's Quote with QuoteLineItem
 */

import { error, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
	if (!locals.user || !locals.org) {
		throw redirect(302, '/login');
	}

	try {
		// Get invoice detail from Django API
		const invoice = await apiRequest(
			`/invoices/${params.invoiceId}/`,
			{},
			{ cookies, org: locals.org }
		);

		if (!invoice) {
			throw error(404, 'Invoice not found');
		}

		// Transform to SvelteKit Quote format
		const transformedInvoice = transformInvoiceToQuote(invoice);

		return {
			invoice: transformedInvoice
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

		// Amounts
		subtotal: invoice.total_amount || '0.00',
		discountAmount: '0.00',
		taxAmount: invoice.tax || '0.00',
		grandTotal: invoice.total_amount || '0.00',

		// Billing address - Django has Address model
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
		updatedAt: new Date(invoice.created_at),

		// Account relationship
		account: invoice.accounts?.[0]
			? {
					id: invoice.accounts[0].id,
					name: invoice.accounts[0].name,
					// Address fields might be in the Account object
					street: invoice.accounts[0].billing_address?.street || null,
					city: invoice.accounts[0].billing_address?.city || null,
					state: invoice.accounts[0].billing_address?.state || null,
					postalCode: invoice.accounts[0].billing_address?.postcode || null,
					country: invoice.accounts[0].billing_address?.country || null
				}
			: null,

		// Contact - Django doesn't have direct contact on Invoice
		// It's linked through Account
		contact: null, // TODO: May need to fetch separately if needed

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

		// Prepared by - Django has created_by
		preparedBy: invoice.created_by
			? {
					name: invoice.created_by.username || invoice.created_by.email,
					email: invoice.created_by.email
				}
			: null
	};
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
