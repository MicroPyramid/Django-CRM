/**
 * Opportunity Detail Page - Server Load
 *
 * Django endpoint: GET /api/opportunities/<id>/
 * Response shape: { opportunity_obj, comments, attachments, contacts, users, stage, lead_source, currency, comment_permission, users_mention, custom_field_definitions }
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
  const org = locals.org;
  if (!org) {
    throw error(401, 'Organization context required');
  }

  try {
    const response = await apiRequest(`/opportunities/${params.id}/`, {}, { cookies, org });

    if (response?.error) {
      throw error(404, response.errors || 'Opportunity not found');
    }

    const opportunity = response.opportunity_obj || null;

    return {
      opportunity,
      comments: response.comments || [],
      attachments: response.attachments || [],
      contacts: response.contacts || [],
      users: response.users || [],
      commentPermission: response.comment_permission || false,
      customFieldDefinitions: response.custom_field_definitions || [],
      customFieldValues: opportunity?.custom_fields || {}
    };
  } catch (err) {
    // SvelteKit `error()` throws a special object — let it bubble.
    if (/** @type {any} */ (err)?.status) throw err;
    console.error('Failed to load opportunity detail:', err);
    throw error(500, 'Failed to load opportunity');
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  updateCustomFields: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    const raw = form.get('custom_fields')?.toString() || '{}';
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return fail(400, { error: 'Malformed custom_fields payload' });
    }
    try {
      await apiRequest(
        `/opportunities/${params.id}/`,
        { method: 'PATCH', body: { custom_fields: parsed } },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Update opportunity custom fields error:', err);
      return fail(400, {
        error: /** @type {any} */ (err)?.message || 'Failed to save custom fields'
      });
    }
  }
};
