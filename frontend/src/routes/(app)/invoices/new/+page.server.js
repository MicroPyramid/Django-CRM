/**
 * New Invoice Page - Server Load and Actions
 */

import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
  const org = locals.org;

  if (!org) {
    throw error(401, 'Organization context required');
  }

  try {
    // Fetch accounts, contacts, and templates for dropdowns
    const [accountsRes, contactsRes, templatesRes] = await Promise.all([
      apiRequest('/accounts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/contacts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/invoices/templates/', {}, { cookies, org }).catch(() => ({}))
    ]);

    // Transform accounts
    let accountsList = [];
    if (accountsRes.active_accounts?.open_accounts) {
      accountsList = accountsRes.active_accounts.open_accounts;
    } else if (accountsRes.results) {
      accountsList = accountsRes.results;
    } else if (Array.isArray(accountsRes)) {
      accountsList = accountsRes;
    }
    const accounts = accountsList.map((a) => ({
      id: a.id,
      name: a.name,
      email: a.email || '',
      phone: a.phone || '',
      billingAddressLine: a.billing_address_line || '',
      billingCity: a.billing_city || '',
      billingState: a.billing_state || '',
      billingPostcode: a.billing_postcode || '',
      billingCountry: a.billing_country || ''
    }));

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
      phone: c.mobile_number || c.phone || '',
      accountId: c.account?.id || c.account || null
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
          primaryColor: defaultTemplate.primary_color || '#3B82F6',
          secondaryColor: defaultTemplate.secondary_color || '#1E40AF',
          defaultNotes: defaultTemplate.default_notes || '',
          defaultTerms: defaultTemplate.default_terms || '',
          footerText: defaultTemplate.footer_text || ''
        }
      : null;

    return {
      accounts,
      contacts,
      template
    };
  } catch (err) {
    console.error('Error loading invoice form data:', err);
    throw error(500, `Failed to load form data: ${err.message}`);
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();

      // Validate required fields
      const accountId = form.get('accountId')?.toString().trim();
      const contactId = form.get('contactId')?.toString().trim();

      if (!accountId) {
        return fail(400, { error: 'Account is required' });
      }
      if (!contactId) {
        return fail(400, { error: 'Contact is required' });
      }

      // Parse line items
      const lineItemsJson = form.get('lineItems')?.toString() || '[]';
      let lineItems = [];
      try {
        lineItems = JSON.parse(lineItemsJson);
      } catch (e) {
        console.error('Failed to parse line items:', e);
      }

      // Build invoice data
      const clientEmail = form.get('clientEmail')?.toString().trim() || '';
      if (!clientEmail) {
        return fail(400, { error: 'Client email is required' });
      }

      const invoiceData = {
        invoice_title: form.get('invoiceTitle')?.toString().trim() || '',
        status: form.get('status')?.toString() || 'Draft',
        // CRM Integration
        account_id: accountId,
        contact_id: contactId,
        // Client info
        client_name: form.get('clientName')?.toString().trim() || '',
        client_email: clientEmail,
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
        // Reminder settings (defaults)
        reminder_enabled: true,
        reminder_days_before: 3,
        reminder_days_after: 7,
        reminder_frequency: 'ONCE'
      };

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
        '/invoices/',
        {
          method: 'POST',
          body: invoiceData
        },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error creating invoice:', err);
      return fail(400, { error: err.message || 'Failed to create invoice' });
    }
  }
};
