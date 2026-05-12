/**
 * Account Detail Page - Server Load
 *
 * Django endpoint: GET /api/accounts/<id>/
 * Response shape (see backend/accounts/views.py AccountDetailView.get):
 *   { account_obj, attachments, comments, contacts, opportunity_list, cases,
 *     tasks, invoices, emails, users, teams, users_mention,
 *     leads, status, stages, sources, countries, currencies,
 *     case_types, case_priority, case_status, comment_permission }
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
    const response = await apiRequest(`/accounts/${params.id}/`, {}, { cookies, org });

    if (response?.error) {
      throw error(404, response.errors || 'Account not found');
    }

    const account = response.account_obj || response.account || response;

    return {
      account,
      comments: response.comments || [],
      attachments: response.attachments || [],
      contacts: response.contacts || account?.contacts || [],
      opportunities: response.opportunity_list || [],
      cases: response.cases || [],
      tasks: response.tasks || [],
      invoices: response.invoices || [],
      emails: response.emails || [],
      tags: account?.tags || [],
      teams: account?.teams || [],
      assignedTo: account?.assigned_to || [],
      commentPermission: response.comment_permission || false
    };
  } catch (err) {
    if (/** @type {any} */ (err)?.status) throw err;
    console.error('Failed to load account detail:', err);
    throw error(500, 'Failed to load account');
  }
}
