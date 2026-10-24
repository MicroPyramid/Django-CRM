import { fail, redirect } from '@sveltejs/kit';
import { listAccounts } from '#lib/server/v2/accounts.js';
import { listContacts } from '#lib/server/v2/contacts.js';
import { listProducts } from '#lib/server/v2/products.js';
import { createInvoice } from '#lib/server/v2/invoices.js';
import {
  fieldsForNew,
  readCustomFields,
  saveRefusal
} from '#lib/server/v2/record-custom-fields.js';
import { getNumbering } from '#lib/server/v2/organization.js';

/**
 * The builder needs three pickers: account (required), contact (required, the
 * create serializer enforces it and cross-validates it against the account),
 * and the product catalogue for line items. All three reuse the real list
 * layers; nothing here is a fixture. Contacts carry their primary account so
 * the page can offer only the ones that pass the account↔contact rule. The
 * org's numbering format feeds the "Assigned on save" preview.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  const [accounts, contacts, products, numbering, customFields] = await Promise.all([
    listAccounts({ cookies }, new URLSearchParams({ limit: '1000' })),
    listContacts({ cookies }, new URLSearchParams({ limit: '1000' })),
    listProducts({ cookies }),
    getNumbering({ cookies }),
    fieldsForNew(cookies, 'Invoice')
  ]);

  return {
    accounts: accounts.results.map((a) => ({ id: a.id, name: a.name || 'Unnamed account' })),
    contacts: contacts.results.map((c) => ({
      id: c.id,
      name: c.name || c.email || 'Unnamed contact',
      account_id: c.account?.id ?? null,
      account_name: c.account?.name ?? ''
    })),
    products: products.results
      .filter((p) => p.is_active)
      .map((p) => ({ id: p.id, name: p.name, sku: p.sku, price: p.price })),
    numbering,
    customFields
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Create the draft. The page serialises the whole builder into one `payload`
   * field so the dynamic line-item list travels intact; the server owns org,
   * totals, number, token, and forces the status to Draft. On success we land on
   * the new invoice; on rejection the DRF field errors surface in the banner.
   */
  create: async ({ cookies, request }) => {
    const form = await request.formData();
    let body;
    try {
      body = JSON.parse(form.get('payload')?.toString() || '{}');
    } catch {
      return fail(400, { error: 'The invoice form could not be read. Please try again.' });
    }

    // Custom fields come from their own inputs, never from the builder's payload.
    delete body.custom_fields;
    const custom = await readCustomFields(cookies, 'Invoice', form);
    if (custom.refusal) return fail(503, custom.refusal);
    if (custom.values) body.custom_fields = custom.values;

    if (!body.account_id) return fail(400, { error: 'Choose an account.' });
    if (!body.contact_id) return fail(400, { error: 'Choose a contact.' });
    if (!Array.isArray(body.line_items) || body.line_items.length === 0) {
      return fail(400, { error: 'Add at least one line with a description and an amount.' });
    }

    let created;
    try {
      created = await createInvoice({ cookies }, body);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        ...saveRefusal(err, custom.definitions, 'Could not create the invoice.')
      });
    }

    redirect(303, created?.id ? `/invoices/${created.id}` : '/invoices');
  }
};
