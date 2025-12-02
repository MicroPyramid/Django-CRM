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

import { error, fail } from '@sveltejs/kit';
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
		// Fetch leads and dropdown data in parallel
		const [response, usersResponse, teamsResponse, contactsResponse, tagsResponse] =
			await Promise.all([
				apiRequest(`/leads/`, {}, { cookies, org }),
				apiRequest(`/users/`, {}, { cookies, org }).catch(() => ({ results: [] })),
				apiRequest(`/teams/`, {}, { cookies, org }).catch(() => ({ teams: [] })),
				apiRequest(`/contacts/`, {}, { cookies, org }).catch(() => ({ contact_obj_list: [] })),
				apiRequest(`/tags/`, {}, { cookies, org }).catch(() => [])
			]);

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
			// Core Information
			firstName: lead.first_name,
			lastName: lead.last_name,
			title: lead.title,
			salutation: lead.salutation,
			contactTitle: lead.job_title,
			company: lead.company_name,
			email: lead.email,
			phone: lead.phone,
			website: lead.website,
			linkedinUrl: lead.linkedin_url,

			// Sales Pipeline
			status: lead.status ? lead.status.toUpperCase().replace(' ', '_') : 'NEW',
			leadSource: lead.source,
			industry: lead.industry,
			rating: lead.rating,
			opportunityAmount: lead.opportunity_amount,
			probability: lead.probability,
			closeDate: lead.close_date,

			// Address
			addressLine: lead.address_line,
			city: lead.city,
			state: lead.state,
			postcode: lead.postcode,
			country: lead.country,

			// Activity Tracking
			lastContacted: lead.last_contacted,
			nextFollowUp: lead.next_follow_up,
			description: lead.description,

			// System
			isConverted: lead.status === 'converted',
			isActive: lead.is_active,
			createdAt: lead.created_at,
			updatedAt: lead.updated_at || lead.created_at,

			// Assignment - Owner info
			owner:
				lead.assigned_to && lead.assigned_to.length > 0
					? {
							id: lead.assigned_to[0].id,
							name:
								lead.assigned_to[0].user?.email ||
								lead.assigned_to[0].user_details?.email ||
								'Unknown',
							email: lead.assigned_to[0].user?.email || lead.assigned_to[0].user_details?.email
						}
					: lead.created_by
						? {
								id: lead.created_by.id,
								name: lead.created_by.email,
								email: lead.created_by.email
							}
						: null,

			// Assignment arrays (IDs for form editing)
			assignedTo: (lead.assigned_to || []).map((u) => u.id),
			teams: (lead.teams || []).map((t) => t.id),

			// Related data
			contacts: (lead.contacts || []).map((c) => c.id),
			tags: (lead.tags || []).map((t) => t.id),
			comments: lead.lead_comments || [],
			attachments: lead.lead_attachment || []
		}));

		// Transform dropdown data for form options
		const users = (usersResponse.results || usersResponse || []).map((u) => ({
			value: u.id,
			label: u.email || u.username || 'Unknown'
		}));

		const teamsList = (teamsResponse.teams || teamsResponse || []).map((t) => ({
			value: t.id,
			label: t.name || 'Unknown'
		}));

		const contactsList = (contactsResponse.contact_obj_list || contactsResponse.results || contactsResponse || []).map((c) => ({
			value: c.id,
			label: `${c.first_name || ''} ${c.last_name || ''}`.trim() || c.email || 'Unknown'
		}));

		const tagsList = (Array.isArray(tagsResponse) ? tagsResponse : tagsResponse.results || []).map((t) => ({
			value: t.id,
			label: t.name || 'Unknown'
		}));

		return {
			leads: transformedLeads,
			formOptions: {
				users,
				teamsList,
				contactsList,
				tagsList
			}
		};
	} catch (err) {
		console.error('Error fetching leads from API:', err);
		throw error(500, `Failed to fetch leads: ${err.message}`);
	}
}

/** @type {import('./$types').Actions} */
export const actions = {
	create: async ({ request, locals, cookies }) => {
		// Valid Django choices
		const validSources = ['call', 'email', 'existing customer', 'partner', 'public relations', 'compaign', 'other'];
		const validStatuses = ['assigned', 'in process', 'converted', 'recycled', 'closed'];
		const validRatings = ['HOT', 'WARM', 'COLD'];

		try {
			const form = await request.formData();

			// Core Information
			const firstName = form.get('firstName')?.toString().trim();
			const lastName = form.get('lastName')?.toString().trim();
			const email = form.get('email')?.toString().trim();
			const phone = form.get('phone')?.toString().trim() || '';
			const companyId = form.get('companyId')?.toString().trim() || null;
			const title = form.get('title')?.toString().trim() || '';
			const contactTitle = form.get('contactTitle')?.toString().trim() || '';
			const website = form.get('website')?.toString().trim() || '';
			const linkedinUrl = form.get('linkedinUrl')?.toString().trim() || '';

			// Sales Pipeline
			const statusRaw = form.get('status')?.toString().trim().toLowerCase() || '';
			const status = validStatuses.includes(statusRaw) ? statusRaw : 'assigned';
			const sourceRaw = form.get('source')?.toString().trim().toLowerCase() || '';
			const source = validSources.includes(sourceRaw) ? sourceRaw : null;
			const industry = form.get('industry')?.toString().trim() || '';
			const ratingRaw = form.get('rating')?.toString().trim().toUpperCase() || '';
			const rating = validRatings.includes(ratingRaw) ? ratingRaw : null;
			const opportunityAmount = form.get('opportunityAmount')?.toString().trim() || null;
			const probability = form.get('probability')?.toString().trim() || null;
			const closeDate = form.get('closeDate')?.toString().trim() || null;

			// Address
			const addressLine = form.get('addressLine')?.toString().trim() || '';
			const city = form.get('city')?.toString().trim() || '';
			const state = form.get('state')?.toString().trim() || '';
			const postcode = form.get('postcode')?.toString().trim() || '';
			const country = form.get('country')?.toString().trim() || '';

			// Activity
			const lastContacted = form.get('lastContacted')?.toString().trim() || null;
			const nextFollowUp = form.get('nextFollowUp')?.toString().trim() || null;
			const description = form.get('description')?.toString().trim() || '';
			const ownerId = form.get('ownerId')?.toString();

			if (!title) {
				return fail(400, { error: 'Lead title is required.' });
			}

			const leadData = {
				// Core Information (title is required, others optional)
				title,
				description,
				// Sales Pipeline
				status,
				assigned_to: ownerId ? [ownerId] : [],
				org: locals.org.id
			};

			// Only include optional fields if they have values
			if (firstName) leadData.first_name = firstName;
			if (lastName) leadData.last_name = lastName;
			if (email) leadData.email = email;
			if (phone) leadData.phone = phone;
			if (contactTitle) leadData.job_title = contactTitle;
			if (website) leadData.website = website;
			if (linkedinUrl) leadData.linkedin_url = linkedinUrl;
			if (industry) leadData.industry = industry;

			// Only include optional fields if they have valid values
			if (companyId) leadData.company_name = companyId;
			if (source) leadData.source = source;
			if (rating) leadData.rating = rating;
			if (opportunityAmount) leadData.opportunity_amount = parseFloat(opportunityAmount);
			if (probability) leadData.probability = parseInt(probability);
			if (closeDate) leadData.close_date = closeDate;
			if (addressLine) leadData.address_line = addressLine;
			if (city) leadData.city = city;
			if (state) leadData.state = state;
			if (postcode) leadData.postcode = postcode;
			if (country) leadData.country = country;
			if (lastContacted) leadData.last_contacted = lastContacted;
			if (nextFollowUp) leadData.next_follow_up = nextFollowUp;

			await apiRequest(
				'/leads/',
				{
					method: 'POST',
					body: leadData
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error creating lead:', err);
			return fail(500, { error: 'Failed to create lead' });
		}
	},

	update: async ({ request, locals, cookies }) => {
		// Valid Django choices
		const validSources = ['call', 'email', 'existing customer', 'partner', 'public relations', 'compaign', 'other'];
		const validStatuses = ['assigned', 'in process', 'converted', 'recycled', 'closed'];
		const validRatings = ['HOT', 'WARM', 'COLD'];

		try {
			const form = await request.formData();
			const leadId = form.get('leadId')?.toString();

			// Core Information
			const firstName = form.get('firstName')?.toString().trim();
			const lastName = form.get('lastName')?.toString().trim();
			const email = form.get('email')?.toString().trim();
			const phone = form.get('phone')?.toString().trim() || '';
			const companyId = form.get('companyId')?.toString().trim() || null;
			const title = form.get('title')?.toString().trim() || '';
			const contactTitle = form.get('contactTitle')?.toString().trim() || '';
			const website = form.get('website')?.toString().trim() || '';
			const linkedinUrl = form.get('linkedinUrl')?.toString().trim() || '';

			// Sales Pipeline
			const statusRaw = form.get('status')?.toString().trim().toLowerCase() || '';
			const status = validStatuses.includes(statusRaw) ? statusRaw : null;
			const sourceRaw = form.get('source')?.toString().trim().toLowerCase() || '';
			const source = validSources.includes(sourceRaw) ? sourceRaw : null;
			const industry = form.get('industry')?.toString().trim() || '';
			const ratingRaw = form.get('rating')?.toString().trim().toUpperCase() || '';
			const rating = validRatings.includes(ratingRaw) ? ratingRaw : null;
			const opportunityAmount = form.get('opportunityAmount')?.toString().trim() || null;
			const probability = form.get('probability')?.toString().trim() || null;
			const closeDate = form.get('closeDate')?.toString().trim() || null;

			// Address
			const addressLine = form.get('addressLine')?.toString().trim() || '';
			const city = form.get('city')?.toString().trim() || '';
			const state = form.get('state')?.toString().trim() || '';
			const postcode = form.get('postcode')?.toString().trim() || '';
			const country = form.get('country')?.toString().trim() || '';

			// Activity
			const lastContacted = form.get('lastContacted')?.toString().trim() || null;
			const nextFollowUp = form.get('nextFollowUp')?.toString().trim() || null;
			const description = form.get('description')?.toString().trim() || '';
			const ownerId = form.get('ownerId')?.toString();

			if (!leadId || !title) {
				return fail(400, { error: 'Lead ID and title are required.' });
			}

			const leadData = {
				// Core Information (title is required, others optional)
				title,
				description,
				assigned_to: ownerId ? [ownerId] : [],
				org: locals.org.id
			};

			// Only include optional fields if they have values
			if (firstName) leadData.first_name = firstName;
			if (lastName) leadData.last_name = lastName;
			if (email) leadData.email = email;
			if (phone) leadData.phone = phone;
			if (contactTitle) leadData.job_title = contactTitle;
			if (website) leadData.website = website;
			if (linkedinUrl) leadData.linkedin_url = linkedinUrl;
			if (industry) leadData.industry = industry;
			if (companyId) leadData.company_name = companyId;
			if (source) leadData.source = source;
			if (status) leadData.status = status;
			if (rating) leadData.rating = rating;
			if (opportunityAmount) leadData.opportunity_amount = parseFloat(opportunityAmount);
			if (probability) leadData.probability = parseInt(probability);
			if (closeDate) leadData.close_date = closeDate;
			if (addressLine) leadData.address_line = addressLine;
			if (city) leadData.city = city;
			if (state) leadData.state = state;
			if (postcode) leadData.postcode = postcode;
			if (country) leadData.country = country;
			if (lastContacted) leadData.last_contacted = lastContacted;
			if (nextFollowUp) leadData.next_follow_up = nextFollowUp;

			await apiRequest(
				`/leads/${leadId}/`,
				{
					method: 'PATCH',
					body: leadData
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error updating lead:', err);
			return fail(500, { error: 'Failed to update lead' });
		}
	},

	delete: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const leadId = form.get('leadId')?.toString();

			if (!leadId) {
				return fail(400, { error: 'Lead ID is required.' });
			}

			await apiRequest(`/leads/${leadId}/`, { method: 'DELETE' }, { cookies, org: locals.org });

			return { success: true };
		} catch (err) {
			console.error('Error deleting lead:', err);
			return fail(500, { error: 'Failed to delete lead' });
		}
	},

	convert: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const leadId = form.get('leadId')?.toString();

			if (!leadId) {
				return fail(400, { error: 'Lead ID is required.' });
			}

			await apiRequest(
				`/leads/${leadId}/`,
				{
					method: 'PATCH',
					body: { status: 'converted' }
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error converting lead:', err);
			return fail(500, { error: 'Failed to convert lead' });
		}
	},

	duplicate: async ({ request, locals, cookies }) => {
		try {
			const form = await request.formData();
			const leadId = form.get('leadId')?.toString();

			if (!leadId) {
				return fail(400, { error: 'Lead ID is required.' });
			}

			// Fetch the original lead
			const originalLead = await apiRequest(
				`/leads/${leadId}/`,
				{ method: 'GET' },
				{ cookies, org: locals.org }
			);

			// Create a copy with modified title
			const leadData = {
				title: `${originalLead.title || 'Lead'} (Copy)`,
				description: originalLead.description || '',
				status: 'assigned',
				org: locals.org.id
			};

			// Copy optional fields if they exist
			if (originalLead.first_name) leadData.first_name = originalLead.first_name;
			if (originalLead.last_name) leadData.last_name = originalLead.last_name;
			if (originalLead.email) leadData.email = originalLead.email;
			if (originalLead.phone) leadData.phone = originalLead.phone;
			if (originalLead.job_title) leadData.job_title = originalLead.job_title;
			if (originalLead.website) leadData.website = originalLead.website;
			if (originalLead.linkedin_url) leadData.linkedin_url = originalLead.linkedin_url;
			if (originalLead.industry) leadData.industry = originalLead.industry;
			if (originalLead.company_name) leadData.company_name = originalLead.company_name;
			if (originalLead.source) leadData.source = originalLead.source;
			if (originalLead.rating) leadData.rating = originalLead.rating;
			if (originalLead.opportunity_amount) leadData.opportunity_amount = originalLead.opportunity_amount;
			if (originalLead.probability) leadData.probability = originalLead.probability;
			if (originalLead.address_line) leadData.address_line = originalLead.address_line;
			if (originalLead.city) leadData.city = originalLead.city;
			if (originalLead.state) leadData.state = originalLead.state;
			if (originalLead.postcode) leadData.postcode = originalLead.postcode;
			if (originalLead.country) leadData.country = originalLead.country;

			await apiRequest(
				'/leads/',
				{
					method: 'POST',
					body: leadData
				},
				{ cookies, org: locals.org }
			);

			return { success: true };
		} catch (err) {
			console.error('Error duplicating lead:', err);
			return fail(500, { error: 'Failed to duplicate lead' });
		}
	}
};
