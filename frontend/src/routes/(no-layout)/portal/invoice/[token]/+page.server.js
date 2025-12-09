/**
 * Public Invoice Portal Page
 *
 * Public view for clients to see their invoice via token.
 * No authentication required.
 */

import { error } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, fetch }) {
  const { token } = params;

  if (!token) {
    throw error(400, 'Invoice token is required');
  }

  try {
    // Fetch invoice from public API (no auth)
    const response = await fetch(`/api/public/invoice/${token}/`);

    if (!response.ok) {
      if (response.status === 404) {
        throw error(404, 'Invoice not found or link has expired');
      }
      throw error(response.status, 'Failed to load invoice');
    }

    const invoice = await response.json();

    return {
      invoice: {
        id: invoice.id,
        invoiceNumber: invoice.invoice_number,
        invoiceTitle: invoice.invoice_title,
        status: invoice.status,
        clientName: invoice.client_name,
        clientEmail: invoice.client_email,
        issueDate: invoice.issue_date,
        dueDate: invoice.due_date,
        subtotal: invoice.subtotal,
        discountAmount: invoice.discount_amount,
        taxAmount: invoice.tax_amount,
        totalAmount: invoice.total_amount,
        amountPaid: invoice.amount_paid,
        amountDue: invoice.amount_due,
        currency: invoice.currency,
        notes: invoice.notes,
        terms: invoice.terms,
        billingAddress: invoice.billing_address,
        lineItems: invoice.line_items || [],
        payments: invoice.payments || [],
        org: invoice.org
      },
      template: invoice.template
        ? {
            primaryColor: invoice.template.primary_color || '#3B82F6',
            secondaryColor: invoice.template.secondary_color || '#1E40AF',
            footerText: invoice.template.footer_text || ''
          }
        : {
            primaryColor: '#3B82F6',
            secondaryColor: '#1E40AF',
            footerText: ''
          },
      token
    };
  } catch (err) {
    if (err.status) throw err;
    console.error('Error loading public invoice:', err);
    throw error(500, 'Failed to load invoice');
  }
}
