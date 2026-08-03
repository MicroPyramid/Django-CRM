import { fail, redirect, error } from '@sveltejs/kit';
import { getProductForEdit, updateProduct, deleteProduct } from '$lib/server/v2/products.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * Editing a catalogue product.
 *
 * Admin-only, and enforced server-side: `getProductForEdit` returns
 * `can_edit: false` for a non-admin without even fetching the row, so the form
 * is never drawn for someone the PUT would refuse; the API refuses it too. The
 * detail fetch is org-scoped, so a foreign or unknown id 404s.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  try {
    return await getProductForEdit(event, event.params.id);
  } catch (/** @type {any} */ err) {
    if (err?.status === 404) error(404, 'Product not found');
    throw err;
  }
}

/** A price is required and must be a number ≥ 0. */
function priceOk(value) {
  if (value === '') return false;
  const n = Number(value);
  return Number.isFinite(n) && n >= 0;
}

/** @type {import('./$types').Actions} */
export const actions = {
  save: async (event) => {
    const form = await event.request.formData();
    const name = form.get('name')?.toString().trim() ?? '';
    const sku = form.get('sku')?.toString().trim() ?? '';
    const price = form.get('price')?.toString().trim() ?? '';
    const currency = form.get('currency')?.toString() ?? '';
    const category = form.get('category')?.toString().trim() ?? '';
    const description = form.get('description')?.toString().trim() ?? '';
    const is_active = form.get('is_active') !== 'false';

    const values = { name, sku, price, currency, category, description, is_active };

    if (!name) return fail(400, { values, error: 'Give the product a name.' });
    if (!priceOk(price)) return fail(400, { values, error: 'Enter a list price of 0 or more.' });

    try {
      await updateProduct(event, event.params.id, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { values, error: 'Only an administrator can change products.' });
      }
      if (err?.status === 404) error(404, 'Product not found');
      return fail(400, { values, error: readableError(err, 'Could not save this product.') });
    }

    redirect(303, '/invoices/products');
  },

  delete: async (event) => {
    try {
      await deleteProduct(event, event.params.id);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { error: 'Only an administrator can delete products.' });
      }
      // 404 means it is already gone: fall through to the list either way.
      if (err?.status !== 404) {
        return fail(400, { error: readableError(err, 'Could not delete this product.') });
      }
    }

    redirect(303, '/invoices/products');
  }
};
