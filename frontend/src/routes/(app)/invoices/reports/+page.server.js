/**
 * Invoice Reports Dashboard
 *
 * Displays invoice summaries, revenue reports, and aging analysis.
 */

import { error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ url, locals, cookies }) {
  const org = locals.org;

  if (!org) {
    throw error(401, 'Organization context required');
  }

  try {
    // Get date range from URL params or defaults
    const today = new Date();
    const yearAgo = new Date(today);
    yearAgo.setFullYear(yearAgo.getFullYear() - 1);

    const startDate = url.searchParams.get('start_date') || yearAgo.toISOString().split('T')[0];
    const endDate = url.searchParams.get('end_date') || today.toISOString().split('T')[0];
    const groupBy = url.searchParams.get('group_by') || 'month';

    // Fetch all reports in parallel
    const [dashboardRes, revenueRes, agingRes] = await Promise.all([
      apiRequest('/invoices/reports/dashboard/', {}, { cookies, org }),
      apiRequest(
        `/invoices/reports/revenue/?start_date=${startDate}&end_date=${endDate}&group_by=${groupBy}`,
        {},
        { cookies, org }
      ),
      apiRequest('/invoices/reports/aging/', {}, { cookies, org })
    ]);

    return {
      dashboard: dashboardRes,
      revenue: revenueRes,
      aging: agingRes,
      filters: {
        startDate,
        endDate,
        groupBy
      }
    };
  } catch (err) {
    console.error('Error loading reports:', err);
    throw error(500, `Failed to load reports: ${err.message}`);
  }
}
