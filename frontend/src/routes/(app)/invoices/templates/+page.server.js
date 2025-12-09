/**
 * Invoice Templates List Page
 *
 * Templates for customizing invoice PDF generation.
 * Django endpoint: GET /api/invoices/templates/
 */

import { error, fail } from '@sveltejs/kit';
import { apiRequest, buildQueryParams } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ url, locals, cookies }) {
  const org = locals.org;

  if (!org) {
    throw error(401, 'Organization context required');
  }

  // Parse filter params from URL
  const filters = {
    search: url.searchParams.get('search') || ''
  };

  try {
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    // Build query parameters for Django
    const queryParams = buildQueryParams({
      page,
      limit
    });

    // Add filter params
    if (filters.search) queryParams.append('search', filters.search);

    // Fetch templates
    const templatesResponse = await apiRequest(
      `/invoices/templates/?${queryParams.toString()}`,
      {},
      { cookies, org }
    );

    // Handle Django response format
    let templates = [];
    let totalCount = 0;

    if (templatesResponse.results) {
      templates = templatesResponse.results;
      totalCount = templatesResponse.count || 0;
    } else if (Array.isArray(templatesResponse)) {
      templates = templatesResponse;
      totalCount = templates.length;
    }

    // Transform templates to frontend structure
    const transformedTemplates = templates.map((template) => ({
      id: template.id,
      name: template.name,
      logo: template.logo,
      primaryColor: template.primary_color || '#3B82F6',
      secondaryColor: template.secondary_color || '#1E40AF',
      templateHtml: template.template_html || '',
      templateCss: template.template_css || '',
      defaultNotes: template.default_notes || '',
      defaultTerms: template.default_terms || '',
      footerText: template.footer_text || '',
      isDefault: template.is_default,
      createdAt: template.created_at
    }));

    return {
      templates: transformedTemplates,
      pagination: {
        page,
        limit,
        total: totalCount,
        totalPages: Math.ceil(totalCount / limit) || 1
      },
      filters
    };
  } catch (err) {
    console.error('Error loading templates from API:', err);
    throw error(500, `Failed to load templates: ${err.message}`);
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();

      const templateData = {
        name: form.get('name')?.toString().trim() || '',
        primary_color: form.get('primaryColor')?.toString() || '#3B82F6',
        secondary_color: form.get('secondaryColor')?.toString() || '#1E40AF',
        default_notes: form.get('defaultNotes')?.toString() || '',
        default_terms: form.get('defaultTerms')?.toString() || '',
        footer_text: form.get('footerText')?.toString() || '',
        is_default: form.get('isDefault') === 'true'
      };

      await apiRequest(
        '/invoices/templates/',
        {
          method: 'POST',
          body: templateData
        },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error creating template:', err);
      return fail(400, { error: err.message || 'Failed to create template' });
    }
  },

  update: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const templateId = form.get('templateId')?.toString();

      if (!templateId) {
        return fail(400, { error: 'Template ID is required' });
      }

      const templateData = {
        name: form.get('name')?.toString().trim() || '',
        primary_color: form.get('primaryColor')?.toString() || '#3B82F6',
        secondary_color: form.get('secondaryColor')?.toString() || '#1E40AF',
        default_notes: form.get('defaultNotes')?.toString() || '',
        default_terms: form.get('defaultTerms')?.toString() || '',
        footer_text: form.get('footerText')?.toString() || '',
        is_default: form.get('isDefault') === 'true'
      };

      await apiRequest(
        `/invoices/templates/${templateId}/`,
        {
          method: 'PUT',
          body: templateData
        },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error updating template:', err);
      return fail(400, { error: err.message || 'Failed to update template' });
    }
  },

  delete: async ({ request, locals, cookies }) => {
    try {
      const form = await request.formData();
      const templateId = form.get('templateId')?.toString();

      if (!templateId) {
        return fail(400, { error: 'Template ID is required' });
      }

      await apiRequest(
        `/invoices/templates/${templateId}/`,
        { method: 'DELETE' },
        { cookies, org: locals.org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error deleting template:', err);
      return fail(400, { error: err.message || 'Failed to delete template' });
    }
  }
};
