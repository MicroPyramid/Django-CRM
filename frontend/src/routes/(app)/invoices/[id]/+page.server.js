/**
 * Invoice Detail/Edit Page - Server Load and Actions
 */

import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';
import { env } from '$env/dynamic/public';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
  const org = locals.org;

  if (!org) {
    throw error(401, 'Organization context required');
  }

  try {
    // Fetch invoice, accounts, contacts, org settings, and templates in parallel
    const [invoiceRes, accountsRes, contactsRes, orgSettingsRes, templatesRes] = await Promise.all([
      apiRequest(`/invoices/${params.id}/`, {}, { cookies, org }),
      apiRequest('/accounts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/contacts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/org/settings/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/invoices/templates/', {}, { cookies, org }).catch(() => ({}))
    ]);

    // API returns { invoice: {...}, attachments: [...], comments: [...], history: [...] }
    const invoiceData = invoiceRes.invoice || invoiceRes;

    // Transform invoice
    const invoice = {
      id: invoiceData.id,
      invoiceNumber: invoiceData.invoice_number,
      invoiceTitle: invoiceData.invoice_title || '',
      status: invoiceData.status,
      // CRM relationships
      accountId: invoiceData.account?.id || '',
      contactId: invoiceData.contact?.id || '',
      opportunityId: invoiceData.opportunity?.id || '',
      // Client details
      clientName: invoiceData.client_name || '',
      clientEmail: invoiceData.client_email || '',
      clientPhone: invoiceData.client_phone || '',
      clientAddressLine: invoiceData.client_address_line || '',
      clientCity: invoiceData.client_city || '',
      clientState: invoiceData.client_state || '',
      clientPostcode: invoiceData.client_postcode || '',
      clientCountry: invoiceData.client_country || '',
      // Financial
      subtotal: invoiceData.subtotal || '0.00',
      discountType: invoiceData.discount_type || '',
      discountValue: invoiceData.discount_value || '0',
      discountAmount: invoiceData.discount_amount || '0.00',
      taxRate: invoiceData.tax_rate || '0',
      taxAmount: invoiceData.tax_amount || '0.00',
      shippingAmount: invoiceData.shipping_amount || '0.00',
      totalAmount: invoiceData.total_amount || '0.00',
      amountPaid: invoiceData.amount_paid || '0.00',
      amountDue: invoiceData.amount_due || '0.00',
      currency: invoiceData.currency || 'USD',
      // Dates
      issueDate: invoiceData.issue_date,
      dueDate: invoiceData.due_date,
      paymentTerms: invoiceData.payment_terms || 'NET_30',
      sentAt: invoiceData.sent_at,
      viewedAt: invoiceData.viewed_at,
      paidAt: invoiceData.paid_at,
      // Notes
      notes: invoiceData.notes || '',
      terms: invoiceData.terms || '',
      // Additional metadata
      billingPeriod: invoiceData.billing_period || '',
      poNumber: invoiceData.po_number || '',
      // Line items
      lineItems: (invoiceData.line_items || []).map((item) => ({
        id: item.id,
        name: item.name || '',
        description: item.description || '',
        quantity: parseFloat(item.quantity) || 1,
        rate: parseFloat(item.unit_price) || 0,
        amount: parseFloat(item.total) || 0
      })),
      // Meta
      createdAt: invoiceData.created_at,
      createdBy: invoiceData.created_by
    };

    // Transform accounts
    let accountsList = [];
    if (accountsRes.active_accounts?.open_accounts) {
      accountsList = accountsRes.active_accounts.open_accounts;
    } else if (accountsRes.results) {
      accountsList = accountsRes.results;
    } else if (Array.isArray(accountsRes)) {
      accountsList = accountsRes;
    }
    const accounts = accountsList.map((a) => ({ id: a.id, name: a.name }));

    // Transform contacts
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
      name: `${c.first_name || ''} ${c.last_name || ''}`.trim() || c.email,
      email: c.email || '',
      phone: c.mobile_number || c.phone || ''
    }));

    // Transform org settings for company profile
    const company = {
      name: orgSettingsRes.name || '',
      companyName: orgSettingsRes.company_name || orgSettingsRes.name || '',
      addressLine: orgSettingsRes.address_line || '',
      city: orgSettingsRes.city || '',
      state: orgSettingsRes.state || '',
      postcode: orgSettingsRes.postcode || '',
      country: orgSettingsRes.country || '',
      phone: orgSettingsRes.phone || '',
      email: orgSettingsRes.email || '',
      website: orgSettingsRes.website || '',
      taxId: orgSettingsRes.tax_id || '',
      logoUrl: orgSettingsRes.logo_url || null
    };

    // Find the default template
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
          primaryColor: defaultTemplate.primary_color || '#3B82F6',
          secondaryColor: defaultTemplate.secondary_color || '#1E40AF',
          footerText: defaultTemplate.footer_text || '',
          defaultNotes: defaultTemplate.default_notes || '',
          defaultTerms: defaultTemplate.default_terms || ''
        }
      : {
          primaryColor: '#3B82F6',
          secondaryColor: '#1E40AF',
          footerText: '',
          defaultNotes: '',
          defaultTerms: ''
        };

    return {
      invoice,
      accounts,
      contacts,
      company,
      template
    };
  } catch (err) {
    console.error('Error loading invoice:', err);
    throw error(500, `Failed to load invoice: ${err.message}`);
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  update: async ({ params, request, locals, cookies }) => {
    try {
      const form = await request.formData();

      // Get CRM fields
      const accountId = form.get('accountId')?.toString().trim();
      const contactId = form.get('contactId')?.toString().trim();

      // Parse line items
      const lineItemsJson = form.get('lineItems')?.toString() || '[]';
      let lineItems = [];
      try {
        lineItems = JSON.parse(lineItemsJson);
      } catch (e) {
        console.error('Failed to parse line items:', e);
      }

      // Build invoice data
      const invoiceData = {
        invoice_title: form.get('invoiceTitle')?.toString().trim() || '',
        status: form.get('status')?.toString() || 'Draft',
        // Client info
        client_name: form.get('clientName')?.toString().trim() || '',
        client_email: form.get('clientEmail')?.toString().trim() || '',
        client_phone: form.get('clientPhone')?.toString().trim() || '',
        // Client address
        client_address_line: form.get('clientAddressLine')?.toString() || '',
        client_city: form.get('clientCity')?.toString() || '',
        client_state: form.get('clientState')?.toString() || '',
        client_postcode: form.get('clientPostcode')?.toString() || '',
        client_country: form.get('clientCountry')?.toString() || '',
        // Dates
        issue_date: form.get('issueDate')?.toString() || null,
        due_date: form.get('dueDate')?.toString() || null,
        payment_terms: form.get('paymentTerms')?.toString() || 'NET_30',
        // Financial
        currency: form.get('currency')?.toString() || 'USD',
        tax_rate: Math.max(
          0,
          Math.min(100, parseFloat(form.get('taxRate')?.toString() || '0') || 0)
        ),
        discount_type: '',
        discount_value: '0',
        // Notes
        notes: form.get('notes')?.toString() || '',
        terms: form.get('terms')?.toString() || '',
        // Additional metadata
        billing_period: form.get('billingPeriod')?.toString() || '',
        po_number: form.get('poNumber')?.toString() || '',
        // Reminder settings
        reminder_enabled: true,
        reminder_days_before: 3,
        reminder_days_after: 7,
        reminder_frequency: 'ONCE'
      };

      // Add CRM relationships if provided
      if (accountId) invoiceData.account_id = accountId;
      if (contactId) invoiceData.contact_id = contactId;

      // Add line items if any
      if (lineItems.length > 0) {
        invoiceData.line_items = lineItems.map((item, idx) => ({
          name: item.name || '',
          description: item.description || '',
          quantity: item.quantity || 1,
          unit_price: item.rate || 0,
          order: idx
        }));
      }

      await apiRequest(
        `/invoices/${params.id}/`,
        {
          method: 'PUT',
          body: invoiceData
        },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error updating invoice:', err);
      return fail(400, { error: err.message || 'Failed to update invoice' });
    }
  },

  cancel: async ({ params, locals, cookies }) => {
    try {
      await apiRequest(
        `/invoices/${params.id}/cancel/`,
        { method: 'POST' },
        { cookies, org: locals.org }
      );
      throw redirect(303, '/invoices');
    } catch (err) {
      if (err.status === 303) throw err; // Re-throw redirect
      console.error('Error cancelling invoice:', err);
      return fail(400, { error: err.message || 'Failed to cancel invoice' });
    }
  },

  send: async ({ params, locals, cookies }) => {
    try {
      await apiRequest(
        `/invoices/${params.id}/send/`,
        { method: 'POST' },
        { cookies, org: locals.org }
      );
      return { success: true, message: 'Invoice sent successfully' };
    } catch (err) {
      console.error('Error sending invoice:', err);
      return fail(400, { error: err.message || 'Failed to send invoice' });
    }
  },

  markPaid: async ({ params, request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const amount = form.get('amount')?.toString();
      const paymentMethod = form.get('paymentMethod')?.toString() || 'OTHER';
      const paymentDate =
        form.get('paymentDate')?.toString() || new Date().toISOString().split('T')[0];

      await apiRequest(
        `/invoices/${params.id}/mark-paid/`,
        {
          method: 'POST',
          body: {
            amount,
            payment_method: paymentMethod,
            payment_date: paymentDate
          }
        },
        { cookies, org: locals.org }
      );

      return { success: true, message: 'Payment recorded' };
    } catch (err) {
      console.error('Error marking paid:', err);
      return fail(400, { error: err.message || 'Failed to record payment' });
    }
  },

  downloadPdf: async ({ params, locals, cookies }) => {
    try {
      const org = locals.org;
      if (!org) {
        return fail(401, { error: 'Organization context required' });
      }

      // Get the JWT token from cookies
      const accessToken = cookies.get('jwt_access');
      if (!accessToken) {
        return fail(401, { error: 'Authentication required' });
      }

      // Make request to Django backend for PDF
      const apiUrl = env.PUBLIC_DJANGO_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/invoices/${params.id}/pdf/`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'X-Org-ID': org.id
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || errorData.error || 'Failed to generate PDF');
      }

      // Get the PDF blob
      const pdfBuffer = await response.arrayBuffer();
      const base64Pdf = Buffer.from(pdfBuffer).toString('base64');

      return {
        success: true,
        pdf: base64Pdf,
        filename: `invoice-${params.id}.pdf`
      };
    } catch (err) {
      console.error('Error downloading PDF:', err);
      return fail(400, { error: err.message || 'Failed to download PDF' });
    }
  }
};
