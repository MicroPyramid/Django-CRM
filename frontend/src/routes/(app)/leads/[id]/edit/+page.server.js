import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
  if (!locals.org) throw error(401, 'Organization context required');
  try {
    const response = await apiRequest(`/leads/${params.id}/`, {}, { cookies, org: locals.org });
    if (response?.error) throw error(404, response.errors || 'Lead not found');
    return {
      lead: response.lead_obj || null,
      users: response.users || [],
      tags: response.tags || []
    };
  } catch (err) {
    if (err?.status) throw err;
    throw error(500, 'Failed to load lead');
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  default: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    const get = /** @param {string} k */ (k) => form.get(k)?.toString().trim() || '';

    const title = get('title');
    if (!title) {
      return fail(400, { error: 'Title is required', values: Object.fromEntries(form) });
    }

    /** @type {Record<string, any>} */
    const body = {
      title,
      description: get('description') || '',
      org: locals.org.id
    };

    const map = {
      salutation: 'salutation',
      firstName: 'first_name',
      lastName: 'last_name',
      email: 'email',
      phone: 'phone',
      jobTitle: 'job_title',
      website: 'website',
      linkedinUrl: 'linkedin_url',
      industry: 'industry',
      company: 'company_name',
      source: 'source',
      status: 'status',
      rating: 'rating',
      currency: 'currency',
      addressLine: 'address_line',
      city: 'city',
      state: 'state',
      postcode: 'postcode',
      country: 'country'
    };
    for (const [formKey, apiKey] of Object.entries(map)) {
      const v = get(formKey);
      if (v) body[apiKey] = v;
    }

    const amount = get('opportunityAmount');
    if (amount) body.opportunity_amount = parseFloat(amount);
    const probability = get('probability');
    if (probability) body.probability = parseInt(probability, 10);
    const closeDate = get('closeDate');
    if (closeDate) body.close_date = closeDate;
    const lastContacted = get('lastContacted');
    if (lastContacted) body.last_contacted = lastContacted;
    const nextFollowUp = get('nextFollowUp');
    if (nextFollowUp) body.next_follow_up = nextFollowUp;

    try {
      await apiRequest(
        `/leads/${params.id}/`,
        { method: 'PATCH', body },
        { cookies, org: locals.org }
      );
    } catch (err) {
      console.error('Update lead error:', err);
      return fail(err?.status || 500, {
        error: err?.message || 'Failed to update lead',
        values: Object.fromEntries(form)
      });
    }

    throw redirect(303, `/leads/${params.id}`);
  }
};
