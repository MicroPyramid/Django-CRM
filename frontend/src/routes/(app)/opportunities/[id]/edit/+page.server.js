import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
  if (!locals.org) throw error(401, 'Organization context required');
  try {
    const response = await apiRequest(
      `/opportunities/${params.id}/`,
      {},
      { cookies, org: locals.org }
    );
    if (response?.error) throw error(404, response.errors || 'Opportunity not found');
    return {
      opportunity: response.opportunity_obj || null,
      users: response.users || [],
      contacts: response.contacts || []
    };
  } catch (err) {
    if (err?.status) throw err;
    throw error(500, 'Failed to load opportunity');
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  default: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    const get = /** @param {string} k */ (k) => form.get(k)?.toString().trim() || '';

    const name = get('name');
    if (!name) return fail(400, { error: 'Name is required', values: Object.fromEntries(form) });

    /** @type {Record<string, any>} */
    const body = { name };
    const stage = get('stage');
    const currency = get('currency');
    const amount = get('amount');
    const probability = get('probability');
    const closeDate = get('closeDate');
    const description = get('description');
    const leadSource = get('leadSource');

    if (stage) body.stage = stage;
    if (currency) body.currency = currency;
    if (amount) body.amount = parseFloat(amount);
    if (probability) body.probability = parseInt(probability, 10);
    if (closeDate) body.close_date = closeDate;
    if (description) body.description = description;
    if (leadSource) body.lead_source = leadSource;

    try {
      await apiRequest(
        `/opportunities/${params.id}/`,
        { method: 'PATCH', body },
        { cookies, org: locals.org }
      );
    } catch (err) {
      console.error('Update opportunity error:', err);
      return fail(err?.status || 500, {
        error: err?.message || 'Failed to update opportunity',
        values: Object.fromEntries(form)
      });
    }

    throw redirect(303, `/opportunities/${params.id}`);
  }
};
