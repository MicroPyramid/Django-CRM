import { fail, redirect } from '@sveltejs/kit';
import { getNewProductOptions, createProduct } from '$lib/server/v2/products.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * Adding to the product catalogue.
 *
 * Admin-only: `POST /api/invoices/products/` refuses a non-admin (the catalogue
 * is org-wide config, not a per-rep record), so the page hides the form from a
 * non-admin and the action would 403 anyway. `org` is server-derived and never
 * read from the body; `currency` defaults to the org's when left blank.
 *
 * @type {import('./$types').PageServerLoad}
 */
export function load(event) {
  return getNewProductOptions(event);
}

/** A price is required and must be a number ≥ 0 (the model default is 0). */
function priceOk(value) {
  if (value === '') return false;
  const n = Number(value);
  return Number.isFinite(n) && n >= 0;
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async (event) => {
    const form = await event.request.formData();
    const name = form.get('name')?.toString().trim() ?? '';
    const sku = form.get('sku')?.toString().trim() ?? '';
    const price = form.get('price')?.toString().trim() ?? '';
    const currency = form.get('currency')?.toString() ?? '';
    const category = form.get('category')?.toString().trim() ?? '';
    const description = form.get('description')?.toString().trim() ?? '';
    const is_active = form.get('is_active') !== 'false';

    const values = { name, sku, price, currency, category, description, is_active };

    // UX-side mirrors of the serializer's rules. The API enforces both again.
    if (!name) return fail(400, { values, error: 'Give the product a name.' });
    if (!priceOk(price)) return fail(400, { values, error: 'Enter a list price of 0 or more.' });

    try {
      await createProduct(event, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { values, error: 'Only an administrator can add products.' });
      }
      return fail(400, { values, error: readableError(err, 'Could not create this product.') });
    }

    redirect(303, '/invoices/products');
  }
};
