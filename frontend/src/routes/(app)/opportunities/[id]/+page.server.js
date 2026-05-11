/**
 * Opportunity Detail Page - Server Load
 *
 * Django endpoint: GET /api/opportunities/<id>/
 * Response shape: { opportunity_obj, comments, attachments, contacts, users, stage, lead_source, currency, comment_permission, users_mention }
 */

import { error } from '@sveltejs/kit';
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

    return {
      opportunity: response.opportunity_obj || null,
      comments: response.comments || [],
      attachments: response.attachments || [],
      contacts: response.contacts || [],
      users: response.users || [],
      commentPermission: response.comment_permission || false
    };
  } catch (err) {
    // SvelteKit `error()` throws a special object — let it bubble.
    if (/** @type {any} */ (err)?.status) throw err;
    console.error('Failed to load opportunity detail:', err);
    throw error(500, 'Failed to load opportunity');
  }
}
