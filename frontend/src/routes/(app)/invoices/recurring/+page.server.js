/**
 * Recurring Invoices List Page
 *
 * Full implementation with CrmTable, pagination, filters, and CRUD operations.
 * Django endpoint: GET /api/invoices/recurring/
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
    is_active: url.searchParams.get('is_active') || '',
    frequency: url.searchParams.get('frequency') || '',
    account: url.searchParams.get('account') || ''
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
    if (filters.is_active) queryParams.append('is_active', filters.is_active);
    if (filters.frequency) queryParams.append('frequency', filters.frequency);
    if (filters.account) queryParams.append('account', filters.account);

    // Fetch recurring invoices and accounts in parallel
    const [recurringResponse, accountsRes] = await Promise.all([
      apiRequest(`/invoices/recurring/?${queryParams.toString()}`, {}, { cookies, org }),
      apiRequest('/accounts/', {}, { cookies, org }).catch(() => ({}))
    ]);

    // Handle Django response format
    let recurringInvoices = [];
    let totalCount = 0;

    if (recurringResponse.results) {
      recurringInvoices = recurringResponse.results;
      totalCount = recurringResponse.count || 0;
    } else if (Array.isArray(recurringResponse)) {
      recurringInvoices = recurringResponse;
      totalCount = recurringInvoices.length;
    }

    // Transform Django recurring invoices to frontend structure
    const transformedRecurring = recurringInvoices.map((recurring) => ({
      id: recurring.id,
      // Core fields
      title: recurring.title || '',
      isActive: recurring.is_active,
      // Client info
      clientName: recurring.client_name || '',
      clientEmail: recurring.client_email || '',
      // Schedule
      frequency: recurring.frequency,
      customDays: recurring.custom_days,
      startDate: recurring.start_date,
      endDate: recurring.end_date,
      nextGenerationDate: recurring.next_generation_date,
      // Settings
      paymentTerms: recurring.payment_terms,
      autoSend: recurring.auto_send,
      currency: recurring.currency || 'USD',
      // Financial
      subtotal: recurring.subtotal || '0.00',
      discountType: recurring.discount_type,
      discountValue: recurring.discount_value || '0.00',
      taxRate: recurring.tax_rate || '0.00',
      totalAmount: recurring.total_amount || '0.00',
      // Notes
      notes: recurring.notes || '',
      terms: recurring.terms || '',
      // Statistics
      invoicesGenerated: recurring.invoices_generated || 0,
      // Timestamps
      createdAt: recurring.created_at,
      // Relationships
      account: recurring.account
        ? {
            id: recurring.account.id || recurring.account,
            name: recurring.account_name || recurring.account?.name || ''
          }
        : null,
      contact: recurring.contact
        ? {
            id: recurring.contact.id || recurring.contact,
            name: recurring.contact_name || recurring.contact?.name || ''
          }
        : null,
      // Owner
      owner:
        recurring.assigned_to && recurring.assigned_to.length > 0
          ? {
              id: recurring.assigned_to[0].id,
              name: recurring.assigned_to[0].user_details?.email || 'Unknown',
              email: recurring.assigned_to[0].user_details?.email
            }
          : recurring.created_by
            ? {
                id: recurring.created_by.id,
                name: recurring.created_by.email,
                email: recurring.created_by.email
              }
            : null,
      // Line items
      lineItems:
        recurring.line_items?.map((item) => ({
          id: item.id,
          description: item.description || '',
          quantity: parseFloat(item.quantity) || 1,
          unitPrice: item.unit_price || '0.00',
          discountType: item.discount_type,
          discountValue: item.discount_value || '0.00',
          taxRate: item.tax_rate || '0.00',
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

    return {
      recurringInvoices: transformedRecurring,
      pagination: {
        page,
        limit,
        total: totalCount,
        totalPages: Math.ceil(totalCount / limit) || 1
      },
      filters,
      accounts
    };
  } catch (err) {
    console.error('Error loading recurring invoices from API:', err);
    throw error(500, `Failed to load recurring invoices: ${err.message}`);
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();

      // Build recurring invoice data
      const recurringData = {
        title: form.get('title')?.toString().trim() || '',
        is_active: form.get('isActive') === 'true',
        // Client info
        client_name: form.get('clientName')?.toString().trim() || '',
        client_email: form.get('clientEmail')?.toString().trim() || '',
        // Schedule
        frequency: form.get('frequency')?.toString() || 'MONTHLY',
        custom_days: form.get('customDays')?.toString() || null,
        start_date: form.get('startDate')?.toString() || null,
        end_date: form.get('endDate')?.toString() || null,
        // Settings
        payment_terms: form.get('paymentTerms')?.toString() || 'NET_30',
        auto_send: form.get('autoSend') === 'true',
        currency: form.get('currency')?.toString() || 'USD',
        // Amounts
        discount_type: form.get('discountType')?.toString() || 'fixed',
        discount_value: form.get('discountValue')?.toString() || '0',
        tax_rate: form.get('taxRate')?.toString() || '0',
        // Notes
        notes: form.get('notes')?.toString() || '',
        terms: form.get('terms')?.toString() || '',
        // Relationships
        account: form.get('accountId')?.toString() || null,
        contact: form.get('contactId')?.toString() || null
      };

      // Parse line items JSON
      const lineItemsJson = form.get('lineItems')?.toString() || '[]';
      const lineItems = JSON.parse(lineItemsJson);
      if (lineItems.length > 0) {
        recurringData.line_items = lineItems.map((item, idx) => ({
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
        '/invoices/recurring/',
        {
          method: 'POST',
          body: recurringData
        },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error creating recurring invoice:', err);
      return fail(400, { error: err.message || 'Failed to create recurring invoice' });
    }
  },

  update: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const recurringId = form.get('recurringId')?.toString();

      if (!recurringId) {
        return fail(400, { error: 'Recurring invoice ID is required' });
      }

      // Build recurring invoice data
      const recurringData = {
        title: form.get('title')?.toString().trim() || '',
        is_active: form.get('isActive') === 'true',
        // Client info
        client_name: form.get('clientName')?.toString().trim() || '',
        client_email: form.get('clientEmail')?.toString().trim() || '',
        // Schedule
        frequency: form.get('frequency')?.toString() || 'MONTHLY',
        custom_days: form.get('customDays')?.toString() || null,
        start_date: form.get('startDate')?.toString() || null,
        end_date: form.get('endDate')?.toString() || null,
        // Settings
        payment_terms: form.get('paymentTerms')?.toString() || 'NET_30',
        auto_send: form.get('autoSend') === 'true',
        currency: form.get('currency')?.toString() || 'USD',
        // Amounts
        discount_type: form.get('discountType')?.toString() || 'fixed',
        discount_value: form.get('discountValue')?.toString() || '0',
        tax_rate: form.get('taxRate')?.toString() || '0',
        // Notes
        notes: form.get('notes')?.toString() || '',
        terms: form.get('terms')?.toString() || '',
        // Relationships
        account: form.get('accountId')?.toString() || null,
        contact: form.get('contactId')?.toString() || null
      };

      await apiRequest(
        `/invoices/recurring/${recurringId}/`,
        {
          method: 'PUT',
          body: recurringData
        },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error updating recurring invoice:', err);
      return fail(400, { error: err.message || 'Failed to update recurring invoice' });
    }
  },

  delete: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const recurringId = form.get('recurringId')?.toString();

      if (!recurringId) {
        return fail(400, { error: 'Recurring invoice ID is required' });
      }

      await apiRequest(
        `/invoices/recurring/${recurringId}/`,
        { method: 'DELETE' },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error deleting recurring invoice:', err);
      return fail(400, { error: err.message || 'Failed to delete recurring invoice' });
    }
  },

  toggle: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const recurringId = form.get('recurringId')?.toString();

      if (!recurringId) {
        return fail(400, { error: 'Recurring invoice ID is required' });
      }

      await apiRequest(
        `/invoices/recurring/${recurringId}/toggle/`,
        { method: 'POST' },
        { cookies, org: locals.org }
      );

      return { success: true, message: 'Status toggled successfully' };
    } catch (err) {
      console.error('Error toggling recurring invoice:', err);
      return fail(400, { error: err.message || 'Failed to toggle status' });
    }
  }
};
