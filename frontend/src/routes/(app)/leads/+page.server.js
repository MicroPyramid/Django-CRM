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
export async function load({ url, cookies, locals }) {
	const user = locals.user;
	const org = locals.org;

	if (!org) {
		throw error(401, 'Organization context required');
	}

	// Parse pagination params from URL
	const page = parseInt(url.searchParams.get('page') || '1');
	const limit = parseInt(url.searchParams.get('limit') || '10');

	// Parse filter params from URL
	const filters = {
		search: url.searchParams.get('search') || '',
		status: url.searchParams.get('status') || '',
		source: url.searchParams.get('source') || '',
		rating: url.searchParams.get('rating') || '',
		assigned_to: url.searchParams.getAll('assigned_to'),
		tags: url.searchParams.getAll('tags'),
		created_at_gte: url.searchParams.get('created_at_gte') || '',
		created_at_lte: url.searchParams.get('created_at_lte') || ''
	};

	// Build query params for API
	const queryParams = new URLSearchParams();
	queryParams.append('limit', limit.toString());
	queryParams.append('offset', ((page - 1) * limit).toString());
	if (filters.search) queryParams.append('search', filters.search);
	if (filters.status) queryParams.append('status', filters.status.toLowerCase().replace(/_/g, ' '));
	if (filters.source) queryParams.append('source', filters.source.toLowerCase());
	if (filters.rating) queryParams.append('rating', filters.rating);
	filters.assigned_to.forEach((id) => queryParams.append('assigned_to', id));
	filters.tags.forEach((id) => queryParams.append('tags', id));
	if (filters.created_at_gte) queryParams.append('created_at__gte', filters.created_at_gte);
	if (filters.created_at_lte) queryParams.append('created_at__lte', filters.created_at_lte);

	try {
		// Django leads endpoint with filter params
		const queryString = queryParams.toString();
		const response = await apiRequest(`/leads/${queryString ? `?${queryString}` : ''}`, {}, { cookies, org });

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
			jobTitle: lead.job_title,
			company: lead.company_name,
			email: lead.email,
			phone: lead.phone,
			website: lead.website,
			linkedinUrl: lead.linkedin_url,

			// Sales Pipeline
			status: lead.status ? lead.status.toUpperCase().replace(/ /g, '_') : 'ASSIGNED',
			leadSource: lead.source,
			industry: lead.industry,
			rating: lead.rating,
			opportunityAmount: lead.opportunity_amount,
			currency: lead.currency || null,
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

		// Get total count from response
		const total = response.open_leads?.leads_count || response.count || transformedLeads.length;

		return {
			leads: transformedLeads,
			pagination: {
				page,
				limit,
				total,
				totalPages: Math.ceil(total / limit) || 1
			},
			filters,
			filterOptions: {
				statuses: [
					{ value: 'ASSIGNED', label: 'Assigned' },
					{ value: 'IN_PROCESS', label: 'In Process' },
					{ value: 'CONVERTED', label: 'Converted' },
					{ value: 'RECYCLED', label: 'Recycled' },
					{ value: 'CLOSED', label: 'Closed' }
				],
				sources: [
					{ value: 'call', label: 'Call' },
					{ value: 'email', label: 'Email' },
					{ value: 'existing customer', label: 'Existing Customer' },
					{ value: 'partner', label: 'Partner' },
					{ value: 'public relations', label: 'Public Relations' },
					{ value: 'campaign', label: 'Campaign' },
					{ value: 'other', label: 'Other' }
				],
				ratings: [
					{ value: 'HOT', label: 'Hot' },
					{ value: 'WARM', label: 'Warm' },
					{ value: 'COLD', label: 'Cold' }
				]
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
			const salutation = form.get('salutation')?.toString().trim() || '';
			const firstName = form.get('firstName')?.toString().trim();
			const lastName = form.get('lastName')?.toString().trim();
			const email = form.get('email')?.toString().trim();
			const phone = form.get('phone')?.toString().trim() || '';
			const company = form.get('company')?.toString().trim() || null;
			const title = form.get('title')?.toString().trim() || '';
			const jobTitle = form.get('jobTitle')?.toString().trim() || '';
			const website = form.get('website')?.toString().trim() || '';
			const linkedinUrl = form.get('linkedinUrl')?.toString().trim() || '';

			// Sales Pipeline
			// Convert uppercase underscore format (IN_PROCESS) to Django format (in process)
			const statusRaw = form.get('status')?.toString().trim().toLowerCase().replace(/_/g, ' ') || '';
			const status = validStatuses.includes(statusRaw) ? statusRaw : 'assigned';
			const sourceRaw = form.get('source')?.toString().trim().toLowerCase() || '';
			const source = validSources.includes(sourceRaw) ? sourceRaw : null;
			const industry = form.get('industry')?.toString().trim() || '';
			const ratingRaw = form.get('rating')?.toString().trim().toUpperCase() || '';
			const rating = validRatings.includes(ratingRaw) ? ratingRaw : null;
			const opportunityAmount = form.get('opportunityAmount')?.toString().trim() || null;
			const currency = form.get('currency')?.toString().trim() || null;
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

			// Assignment (multi-select arrays)
			const assignedToRaw = form.get('assignedTo')?.toString() || '[]';
			const teamsRaw = form.get('teams')?.toString() || '[]';
			const contactsRaw = form.get('contacts')?.toString() || '[]';
			const tagsRaw = form.get('tags')?.toString() || '[]';

			/** @type {string[]} */
			let assignedTo = [];
			/** @type {string[]} */
			let teams = [];
			/** @type {string[]} */
			let contacts = [];
			/** @type {string[]} */
			let tags = [];

			try {
				assignedTo = JSON.parse(assignedToRaw);
				teams = JSON.parse(teamsRaw);
				contacts = JSON.parse(contactsRaw);
				tags = JSON.parse(tagsRaw);
			} catch (e) {
				// If parsing fails, use empty arrays
			}

			if (!title) {
				return fail(400, { error: 'Lead title is required.' });
			}

			// Use assignedTo array if provided, otherwise fall back to ownerId
			const finalAssignedTo = assignedTo.length > 0 ? assignedTo : (ownerId ? [ownerId] : []);

			const leadData = {
				// Core Information (title is required, others optional)
				title,
				description,
				// Sales Pipeline
				status,
				assigned_to: finalAssignedTo,
				teams: teams,
				contacts: contacts,
				tags: tags,
				org: locals.org.id
			};

			// Only include optional fields if they have values
			if (salutation) leadData.salutation = salutation;
			if (firstName) leadData.first_name = firstName;
			if (lastName) leadData.last_name = lastName;
			if (email) leadData.email = email;
			if (phone) leadData.phone = phone;
			if (jobTitle) leadData.job_title = jobTitle;
			if (website) leadData.website = website;
			if (linkedinUrl) leadData.linkedin_url = linkedinUrl;
			if (industry) leadData.industry = industry;

			// Only include optional fields if they have valid values
			if (company) leadData.company_name = company;
			if (source) leadData.source = source;
			if (rating) leadData.rating = rating;
			if (opportunityAmount) leadData.opportunity_amount = parseFloat(opportunityAmount);
			if (currency) leadData.currency = currency;
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
			const salutation = form.get('salutation')?.toString().trim() || '';
			const firstName = form.get('firstName')?.toString().trim();
			const lastName = form.get('lastName')?.toString().trim();
			const email = form.get('email')?.toString().trim();
			const phone = form.get('phone')?.toString().trim() || '';
			const company = form.get('company')?.toString().trim() || null;
			const title = form.get('title')?.toString().trim() || '';
			const jobTitle = form.get('jobTitle')?.toString().trim() || '';
			const website = form.get('website')?.toString().trim() || '';
			const linkedinUrl = form.get('linkedinUrl')?.toString().trim() || '';

			// Sales Pipeline
			// Convert uppercase underscore format (IN_PROCESS) to Django format (in process)
			const statusRaw = form.get('status')?.toString().trim().toLowerCase().replace(/_/g, ' ') || '';
			const status = validStatuses.includes(statusRaw) ? statusRaw : null;
			const sourceRaw = form.get('source')?.toString().trim().toLowerCase() || '';
			const source = validSources.includes(sourceRaw) ? sourceRaw : null;
			const industry = form.get('industry')?.toString().trim() || '';
			const ratingRaw = form.get('rating')?.toString().trim().toUpperCase() || '';
			const rating = validRatings.includes(ratingRaw) ? ratingRaw : null;
			const opportunityAmount = form.get('opportunityAmount')?.toString().trim() || null;
			const currency = form.get('currency')?.toString().trim() || null;
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

			// Assignment (multi-select arrays)
			const assignedToRaw = form.get('assignedTo')?.toString() || '[]';
			const teamsRaw = form.get('teams')?.toString() || '[]';
			const contactsRaw = form.get('contacts')?.toString() || '[]';
			const tagsRaw = form.get('tags')?.toString() || '[]';

			/** @type {string[]} */
			let assignedTo = [];
			/** @type {string[]} */
			let teams = [];
			/** @type {string[]} */
			let contacts = [];
			/** @type {string[]} */
			let tags = [];

			try {
				assignedTo = JSON.parse(assignedToRaw);
				teams = JSON.parse(teamsRaw);
				contacts = JSON.parse(contactsRaw);
				tags = JSON.parse(tagsRaw);
			} catch (e) {
				// If parsing fails, use empty arrays
			}

			if (!leadId || !title) {
				return fail(400, { error: 'Lead ID and title are required.' });
			}

			// Use assignedTo array if provided, otherwise fall back to ownerId
			const finalAssignedTo = assignedTo.length > 0 ? assignedTo : (ownerId ? [ownerId] : []);

			const leadData = {
				// Core Information (title is required, others optional)
				title,
				description,
				assigned_to: finalAssignedTo,
				teams: teams,
				contacts: contacts,
				tags: tags,
				org: locals.org.id
			};

			// Only include optional fields if they have values
			if (salutation) leadData.salutation = salutation;
			if (firstName) leadData.first_name = firstName;
			if (lastName) leadData.last_name = lastName;
			if (email) leadData.email = email;
			if (phone) leadData.phone = phone;
			if (jobTitle) leadData.job_title = jobTitle;
			if (website) leadData.website = website;
			if (linkedinUrl) leadData.linkedin_url = linkedinUrl;
			if (industry) leadData.industry = industry;
			if (company) leadData.company_name = company;
			if (source) leadData.source = source;
			if (status) leadData.status = status;
			if (rating) leadData.rating = rating;
			if (opportunityAmount) leadData.opportunity_amount = parseFloat(opportunityAmount);
			if (currency) leadData.currency = currency;
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
			if (originalLead.currency) leadData.currency = originalLead.currency;
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
