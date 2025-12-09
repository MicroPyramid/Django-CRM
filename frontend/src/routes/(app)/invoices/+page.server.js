/**
 * Invoices List Page - Server Load
 *
 * Simple list with pagination and filters. CRUD operations moved to /invoices/new and /invoices/[id]
 * Django endpoint: GET /api/invoices/
 */

import { error } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ url, locals, cookies }) {
  const org = locals.org;

  if (!org) {
    throw error(401, 'Organization context required');
  }

  // Parse filter params from URL
  const filters = {
    search: url.searchParams.get('search') || '',
    status: url.searchParams.get('status') || '',
    account: url.searchParams.get('account') || '',
    contact: url.searchParams.get('contact') || '',
    assigned_to: url.searchParams.getAll('assigned_to'),
    issue_date_gte: url.searchParams.get('issue_date_gte') || '',
    issue_date_lte: url.searchParams.get('issue_date_lte') || '',
    due_date_gte: url.searchParams.get('due_date_gte') || '',
    due_date_lte: url.searchParams.get('due_date_lte') || ''
  };

  try {
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const sort = url.searchParams.get('sort') || '-created_at';

    // Build query parameters for Django
    const queryParams = buildQueryParams({
      page,
      limit,
      sort: sort.startsWith('-') ? sort.substring(1) : sort,
      order: sort.startsWith('-') ? 'desc' : 'asc'
    });

    // Add filter params
    if (filters.search) queryParams.append('search', filters.search);
    if (filters.status) queryParams.append('status', filters.status);
    if (filters.account) queryParams.append('account', filters.account);
    if (filters.contact) queryParams.append('contact', filters.contact);
    filters.assigned_to.forEach((id) => queryParams.append('assigned_to', id));
    if (filters.issue_date_gte) queryParams.append('issue_date_gte', filters.issue_date_gte);
    if (filters.issue_date_lte) queryParams.append('issue_date_lte', filters.issue_date_lte);
    if (filters.due_date_gte) queryParams.append('due_date_gte', filters.due_date_gte);
    if (filters.due_date_lte) queryParams.append('due_date_lte', filters.due_date_lte);

    // Fetch invoices
    const invoicesResponse = await apiRequest(
      `/invoices/?${queryParams.toString()}`,
      {},
      { cookies, org }
    );

    // Handle Django response format
    let invoices = [];
    let totalCount = 0;

    if (invoicesResponse.results) {
      invoices = invoicesResponse.results;
      totalCount = invoicesResponse.count || 0;
    } else if (Array.isArray(invoicesResponse)) {
      invoices = invoicesResponse;
      totalCount = invoices.length;
    }

    // Transform Django invoices to frontend structure
    const transformedInvoices = invoices.map((invoice) => ({
      id: invoice.id,
      invoiceNumber: invoice.invoice_number,
      invoiceTitle: invoice.invoice_title || '',
      status: invoice.status,
      clientName: invoice.client_name || '',
      clientEmail: invoice.client_email || '',
      issueDate: invoice.issue_date,
      dueDate: invoice.due_date,
      totalAmount: invoice.total_amount || '0.00',
      amountDue: invoice.amount_due || '0.00',
      amountPaid: invoice.amount_paid || '0.00',
      currency: invoice.currency || 'USD',
      account: invoice.account
        ? {
            id: invoice.account.id || invoice.account,
            name: invoice.account_name || invoice.account?.name || ''
          }
        : null,
      contact: invoice.contact
        ? {
            id: invoice.contact.id || invoice.contact,
            name: invoice.contact_name || invoice.contact?.name || ''
          }
        : null,
      createdAt: invoice.created_at
    }));

    return {
      invoices: transformedInvoices,
      pagination: {
        page,
        limit,
        total: totalCount,
        totalPages: Math.ceil(totalCount / limit) || 1
      },
      filters
    };
  } catch (err) {
    console.error('Error loading invoices from API:', err);
    throw error(500, `Failed to load invoices: ${err.message}`);
  }
}
