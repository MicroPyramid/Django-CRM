import { fail, redirect } from '@sveltejs/kit';
import { listAccounts } from '$lib/server/v2/accounts.js';
import { listContacts } from '$lib/server/v2/contacts.js';
import { listProducts } from '$lib/server/v2/products.js';
import { createRecurringInvoice } from '$lib/server/v2/recurring.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * Same three pickers as the one-off invoice builder: account and contact are
 * both required by the serializer, which also cross-checks that the contact
 * belongs to the chosen account, and the product catalogue feeds the line-item
 * rows. Contacts carry their account so the page can offer only the ones that
 * pass that rule.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  const [accounts, contacts, products] = await Promise.all([
    listAccounts({ cookies }, new URLSearchParams({ limit: '1000' })),
    listContacts({ cookies }, new URLSearchParams({ limit: '1000' })),
    listProducts({ cookies })
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
      .map((p) => ({ id: p.id, name: p.name, sku: p.sku, price: p.price }))
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Create the schedule. The page serialises the whole builder into one
   * `payload` field so the dynamic line-item list travels intact; the server
   * owns org, totals and invoices_generated. There is no per-schedule detail
   * route (`invoices/recurring/[id]/` does not exist), so on success we land
   * back on the schedules list rather than inventing a redirect target.
   */
  create: async ({ cookies, request }) => {
    const form = await request.formData();
    let values;
    try {
      values = JSON.parse(form.get('payload')?.toString() || '{}');
    } catch {
      return fail(400, { error: 'The schedule form could not be read. Please try again.' });
    }

    try {
      await createRecurringInvoice({ cookies }, values);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error: readableError(err, 'Could not create the schedule.')
      });
    }

    redirect(303, '/invoices/recurring');
  }
};
