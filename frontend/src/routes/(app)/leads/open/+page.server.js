/**
 * Open Leads Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET /api/leads/
 *
 * Django LeadListView returns leads separated into:
 * - open_leads: { leads_count, open_leads: [...] } - excludes status='closed'
 * - close_leads: { leads_count, close_leads: [...] } - only status='closed'
 *
 * Valid Django LEAD_STATUS values: assigned, in process, converted, recycled, closed
 */

import { error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, locals }) {
	const user = locals.user;
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	try {
		// Django leads endpoint - no status filter needed
		// Django LeadListView already separates leads into open_leads and close_leads
		// Valid Django status values: assigned, in process, converted, recycled, closed
		const response = await apiRequest(
			`/leads/`,
			{},
			{ cookies, org }
		);

		// Handle Django response format
		// Django returns: { open_leads: { leads_count, open_leads: [...] }, close_leads: {...}, ... }
		let leads = [];

		if (response.open_leads && response.open_leads.open_leads) {
			// Django returns nested structure: open_leads.open_leads
			leads = response.open_leads.open_leads || [];
		} else if (response.results) {
			// Standard Django pagination
			leads = response.results;
		} else if (Array.isArray(response)) {
			// Direct array response
			leads = response;
		}

		// Transform Django leads to match Prisma structure
		const transformedLeads = leads.map((lead) => ({
			id: lead.id,
			firstName: lead.first_name,
			lastName: lead.last_name,
			title: lead.title,
			company: lead.company,
			email: lead.email,
			phone: lead.phone,
			website: lead.website,
			status: lead.status ? lead.status.toUpperCase().replace(' ', '_') : 'NEW',
			leadSource: lead.source, // Map Django 'source' to Prisma 'leadSource'
			rating: lead.rating, // Include rating for filtering
			description: lead.description,
			isConverted: lead.status === 'converted',
			createdAt: lead.created_at,
			updatedAt: lead.updated_at || lead.created_at,

			// Owner info - Django returns assigned_to array with ProfileSerializer
			owner: lead.assigned_to && lead.assigned_to.length > 0
				? {
						name: lead.assigned_to[0].user?.email || lead.assigned_to[0].user_details?.email || 'Unknown',
						email: lead.assigned_to[0].user?.email || lead.assigned_to[0].user_details?.email
					}
				: lead.created_by
					? {
							name: lead.created_by.email,
							email: lead.created_by.email
						}
					: null
		}));

		return {
			leads: transformedLeads
		};
	} catch (err) {
		console.error('Error fetching leads from API:', err);
		throw error(500, `Failed to fetch leads: ${err.message}`);
	}
}
