/**
 * Estimates List Page - CRM Pattern Version
 *
 * Full implementation with CrmTable, pagination, filters, and CRUD operations.
 * Django endpoint: GET /api/invoices/estimates/
 */

import { error, fail } from '@sveltejs/kit';
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
    expiry_date_gte: url.searchParams.get('expiry_date_gte') || '',
    expiry_date_lte: url.searchParams.get('expiry_date_lte') || ''
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
    if (filters.expiry_date_gte) queryParams.append('expiry_date_gte', filters.expiry_date_gte);
    if (filters.expiry_date_lte) queryParams.append('expiry_date_lte', filters.expiry_date_lte);

    // Fetch estimates, accounts, contacts, and templates in parallel
    const [estimatesResponse, accountsRes, contactsRes, templatesRes] = await Promise.all([
      apiRequest(`/invoices/estimates/?${queryParams.toString()}`, {}, { cookies, org }),
      apiRequest('/accounts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/contacts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/invoices/templates/', {}, { cookies, org }).catch(() => ({}))
    ]);

    // Handle Django response format
    let estimates = [];
    let totalCount = 0;

    if (estimatesResponse.results) {
      estimates = estimatesResponse.results;
      totalCount = estimatesResponse.count || 0;
    } else if (Array.isArray(estimatesResponse)) {
      estimates = estimatesResponse;
      totalCount = estimates.length;
    }

    // Transform Django estimates to frontend structure
    const transformedEstimates = estimates.map((estimate) => ({
      id: estimate.id,
      // Core fields
      estimateNumber: estimate.estimate_number,
      title: estimate.title || '',
      status: estimate.status,
      // Client info
      clientName: estimate.client_name || '',
      clientEmail: estimate.client_email || '',
      clientPhone: estimate.client_phone || '',
      // Dates
      issueDate: estimate.issue_date,
      expiryDate: estimate.expiry_date,
      sentAt: estimate.sent_at,
      viewedAt: estimate.viewed_at,
      acceptedAt: estimate.accepted_at,
      declinedAt: estimate.declined_at,
      // Amounts
      subtotal: estimate.subtotal || '0.00',
      discountType: estimate.discount_type,
      discountValue: estimate.discount_value || '0.00',
      discountAmount: estimate.discount_amount || '0.00',
      taxRate: estimate.tax_rate || '0.00',
      taxAmount: estimate.tax_amount || '0.00',
      totalAmount: estimate.total_amount || '0.00',
      // Currency
      currency: estimate.currency || 'USD',
      // Notes
      notes: estimate.notes || '',
      terms: estimate.terms || '',
      // Client address
      clientAddressLine: estimate.client_address_line || '',
      clientCity: estimate.client_city || '',
      clientState: estimate.client_state || '',
      clientPostcode: estimate.client_postcode || '',
      clientCountry: estimate.client_country || '',
      // Timestamps
      createdAt: estimate.created_at,
      // Conversion
      convertedToInvoice: estimate.converted_to_invoice
        ? {
            id: estimate.converted_to_invoice.id || estimate.converted_to_invoice,
            invoiceNumber:
              estimate.converted_to_invoice.invoice_number ||
              estimate.converted_to_invoice_number ||
              ''
          }
        : null,
      // Relationships
      account: estimate.account
        ? {
            id: estimate.account.id || estimate.account,
            name: estimate.account_name || estimate.account?.name || ''
          }
        : null,
      contact: estimate.contact
        ? {
            id: estimate.contact.id || estimate.contact,
            name: estimate.contact_name || estimate.contact?.name || ''
          }
        : null,
      opportunity: estimate.opportunity
        ? {
            id: estimate.opportunity.id || estimate.opportunity,
            name: estimate.opportunity_name || estimate.opportunity?.name || ''
          }
        : null,
      // Owner
      owner:
        estimate.assigned_to && estimate.assigned_to.length > 0
          ? {
              id: estimate.assigned_to[0].id,
              name: estimate.assigned_to[0].user_details?.email || 'Unknown',
              email: estimate.assigned_to[0].user_details?.email
            }
          : estimate.created_by
            ? {
                id: estimate.created_by.id,
                name: estimate.created_by.email,
                email: estimate.created_by.email
              }
            : null,
      // Line items
      lineItems:
        estimate.line_items?.map((item) => ({
          id: item.id,
          name: item.name || item.description || '',
          description: item.description || '',
          quantity: parseFloat(item.quantity) || 1,
          unitPrice: item.unit_price || '0.00',
          discountType: item.discount_type,
          discountValue: item.discount_value || '0.00',
          discountAmount: item.discount_amount || '0.00',
          taxRate: item.tax_rate || '0.00',
          taxAmount: item.tax_amount || '0.00',
          subtotal: item.subtotal || '0.00',
          total: item.total || '0.00',
          order: item.order || 0
        })) || []
    }));

    // Transform accounts for dropdown
    let accountsList = [];
    if (accountsRes.active_accounts?.open_accounts) {
      accountsList = accountsRes.active_accounts.open_accounts;
    } else if (accountsRes.results) {
      accountsList = accountsRes.results;
    } else if (Array.isArray(accountsRes)) {
      accountsList = accountsRes;
    }
    const accounts = accountsList.map((a) => ({ id: a.id, name: a.name }));

    // Transform contacts for dropdown
    let contactsList = [];
    if (contactsRes.contact_obj_list) {
      contactsList = contactsRes.contact_obj_list;
    } else if (contactsRes.results) {
      contactsList = contactsRes.results;
    } else if (Array.isArray(contactsRes)) {
      contactsList = contactsRes;
    }
    const contacts = contactsList.map((c) => ({
      id: c.id,
      name: `${c.first_name || ''} ${c.last_name || ''}`.trim() || c.email
    }));

    // Find the default template for pre-populating notes/terms
    let templatesList = [];
    if (templatesRes.results) {
      templatesList = templatesRes.results;
    } else if (Array.isArray(templatesRes)) {
      templatesList = templatesRes;
    }
    const defaultTemplate = templatesList.find((t) => t.is_default);
    const template = defaultTemplate
      ? {
          id: defaultTemplate.id,
          name: defaultTemplate.name,
          defaultNotes: defaultTemplate.default_notes || '',
          defaultTerms: defaultTemplate.default_terms || ''
        }
      : null;

    return {
      estimates: transformedEstimates,
      pagination: {
        page,
        limit,
        total: totalCount,
        totalPages: Math.ceil(totalCount / limit) || 1
      },
      filters,
      accounts,
      contacts,
      owners: [],
      template
    };
  } catch (err) {
    console.error('Error loading estimates from API:', err);
    throw error(500, `Failed to load estimates: ${err.message}`);
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();

      // Build estimate data
      const estimateData = {
        title: form.get('title')?.toString().trim() || '',
        status: form.get('status')?.toString() || 'Draft',
        // Client info
        client_name: form.get('clientName')?.toString().trim() || '',
        client_email: form.get('clientEmail')?.toString().trim() || '',
        client_phone: form.get('clientPhone')?.toString().trim() || '',
        // Dates
        issue_date: form.get('issueDate')?.toString() || null,
        expiry_date: form.get('expiryDate')?.toString() || null,
        // Amounts
        discount_type: form.get('discountType')?.toString() || 'fixed',
        discount_value: form.get('discountValue')?.toString() || '0',
        tax_rate: form.get('taxRate')?.toString() || '0',
        currency: form.get('currency')?.toString() || 'USD',
        // Notes
        notes: form.get('notes')?.toString() || '',
        terms: form.get('terms')?.toString() || '',
        // Client address
        client_address_line: form.get('clientAddressLine')?.toString() || '',
        client_city: form.get('clientCity')?.toString() || '',
        client_state: form.get('clientState')?.toString() || '',
        client_postcode: form.get('clientPostcode')?.toString() || '',
        client_country: form.get('clientCountry')?.toString() || '',
        // Relationships
        account: form.get('accountId')?.toString() || null,
        contact: form.get('contactId')?.toString() || null,
        opportunity: form.get('opportunityId')?.toString() || null
      };

      // Parse line items JSON
      const lineItemsJson = form.get('lineItems')?.toString() || '[]';
      const lineItems = JSON.parse(lineItemsJson);
      if (lineItems.length > 0) {
        estimateData.line_items = lineItems.map((item, idx) => ({
          name: item.name || item.description || '',
          description: item.description || '',
          quantity: item.quantity || 1,
          unit_price: item.unitPrice || '0',
          discount_type: item.discountType || 'fixed',
          discount_value: item.discountValue || '0',
          tax_rate: item.taxRate || '0',
          order: item.order || idx
        }));
      }

      await apiRequest(
        '/invoices/estimates/',
        {
          method: 'POST',
          body: estimateData
        },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error creating estimate:', err);
      return fail(400, { error: err.message || 'Failed to create estimate' });
    }
  },

  update: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const estimateId = form.get('estimateId')?.toString();

      if (!estimateId) {
        return fail(400, { error: 'Estimate ID is required' });
      }

      // Build estimate data
      const estimateData = {
        title: form.get('title')?.toString().trim() || '',
        status: form.get('status')?.toString() || 'Draft',
        // Client info
        client_name: form.get('clientName')?.toString().trim() || '',
        client_email: form.get('clientEmail')?.toString().trim() || '',
        client_phone: form.get('clientPhone')?.toString().trim() || '',
        // Dates
        issue_date: form.get('issueDate')?.toString() || null,
        expiry_date: form.get('expiryDate')?.toString() || null,
        // Amounts
        discount_type: form.get('discountType')?.toString() || 'fixed',
        discount_value: form.get('discountValue')?.toString() || '0',
        tax_rate: form.get('taxRate')?.toString() || '0',
        currency: form.get('currency')?.toString() || 'USD',
        // Notes
        notes: form.get('notes')?.toString() || '',
        terms: form.get('terms')?.toString() || '',
        // Client address
        client_address_line: form.get('clientAddressLine')?.toString() || '',
        client_city: form.get('clientCity')?.toString() || '',
        client_state: form.get('clientState')?.toString() || '',
        client_postcode: form.get('clientPostcode')?.toString() || '',
        client_country: form.get('clientCountry')?.toString() || '',
        // Relationships
        account: form.get('accountId')?.toString() || null,
        contact: form.get('contactId')?.toString() || null,
        opportunity: form.get('opportunityId')?.toString() || null
      };

      await apiRequest(
        `/invoices/estimates/${estimateId}/`,
        {
          method: 'PUT',
          body: estimateData
        },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error updating estimate:', err);
      return fail(400, { error: err.message || 'Failed to update estimate' });
    }
  },

  delete: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const estimateId = form.get('estimateId')?.toString();

      if (!estimateId) {
        return fail(400, { error: 'Estimate ID is required' });
      }

      await apiRequest(
        `/invoices/estimates/${estimateId}/`,
        { method: 'DELETE' },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error deleting estimate:', err);
      return fail(400, { error: err.message || 'Failed to delete estimate' });
    }
  },

  send: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const estimateId = form.get('estimateId')?.toString();

      if (!estimateId) {
        return fail(400, { error: 'Estimate ID is required' });
      }

      await apiRequest(
        `/invoices/estimates/${estimateId}/send/`,
        { method: 'POST' },
        { cookies, org: locals.org }
      );

      return { success: true, message: 'Estimate sent successfully' };
    } catch (err) {
      console.error('Error sending estimate:', err);
      return fail(400, { error: err.message || 'Failed to send estimate' });
    }
  },

  convert: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const estimateId = form.get('estimateId')?.toString();

      if (!estimateId) {
        return fail(400, { error: 'Estimate ID is required' });
      }

      const response = await apiRequest(
        `/invoices/estimates/${estimateId}/convert/`,
        { method: 'POST' },
        { cookies, org: locals.org }
      );

      return {
        success: true,
        message: 'Estimate converted to invoice',
        invoiceId: response.invoice?.id
      };
    } catch (err) {
      console.error('Error converting estimate:', err);
      return fail(400, { error: err.message || 'Failed to convert estimate' });
    }
  },

  accept: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const estimateId = form.get('estimateId')?.toString();

      if (!estimateId) {
        return fail(400, { error: 'Estimate ID is required' });
      }

      await apiRequest(
        `/invoices/estimates/${estimateId}/`,
        {
          method: 'PATCH',
          body: { status: 'Accepted' }
        },
        { cookies, org: locals.org }
      );

      return { success: true, message: 'Estimate marked as accepted' };
    } catch (err) {
      console.error('Error accepting estimate:', err);
      return fail(400, { error: err.message || 'Failed to accept estimate' });
    }
  },

  decline: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const estimateId = form.get('estimateId')?.toString();

      if (!estimateId) {
        return fail(400, { error: 'Estimate ID is required' });
      }

      await apiRequest(
        `/invoices/estimates/${estimateId}/`,
        {
          method: 'PATCH',
          body: { status: 'Declined' }
        },
        { cookies, org: locals.org }
      );

      return { success: true, message: 'Estimate marked as declined' };
    } catch (err) {
      console.error('Error declining estimate:', err);
      return fail(400, { error: err.message || 'Failed to decline estimate' });
    }
  }
};
