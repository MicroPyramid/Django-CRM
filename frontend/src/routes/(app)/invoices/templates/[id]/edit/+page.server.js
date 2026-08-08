import { fail, redirect, error } from '@sveltejs/kit';
import { getInvoiceTemplateForEdit, updateInvoiceTemplate } from '$lib/server/v2/templates.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * Editing an invoice template.
 *
 * Admin-only, enforced server-side twice over: `getInvoiceTemplateForEdit`
 * returns `can_edit: false` for a non-admin without fetching anything, and the
 * editor route it would have called is admin-gated in the API. The fetch is
 * org-scoped, so a foreign or unknown id 404s.
 *
 * This page is the reason `GET /invoices/templates/<id>/editor/` exists: every
 * other read strips `template_html` / `template_css`, so before it a form here
 * could not show what was saved, and saving would have blanked it.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  try {
    return await getInvoiceTemplateForEdit(event, event.params.id);
  } catch (/** @type {any} */ err) {
    if (err?.status === 404) error(404, 'Template not found');
    throw err;
  }
}

/**
 * Read only the fields this form owns.
 *
 * `is_default` is not among them on purpose. It is a singleton the model swaps
 * inside a transaction and it has its own control on the list page; reading it
 * here would send an unchecked box along with every unrelated save and demote
 * the org's current default.
 *
 * @param {FormData} form
 */
function readValues(form) {
  return {
    name: form.get('name')?.toString() ?? '',
    primary_color: form.get('primary_color')?.toString() ?? '',
    secondary_color: form.get('secondary_color')?.toString() ?? '',
    default_notes: form.get('default_notes')?.toString() ?? '',
    default_terms: form.get('default_terms')?.toString() ?? '',
    footer_text: form.get('footer_text')?.toString() ?? '',
    template_html: form.get('template_html')?.toString() ?? '',
    template_css: form.get('template_css')?.toString() ?? ''
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  save: async (event) => {
    const form = await event.request.formData();
    const logo = form.get('logo');
    const logoFile = logo instanceof File && logo.size > 0 ? logo : null;
    const values = readValues(form);

    if (!values.name.trim()) {
      return fail(400, { values, error: 'Give the template a name.' });
    }

    try {
      await updateInvoiceTemplate(event, event.params.id, values, logoFile);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, {
          values,
          error: 'Only an administrator can change invoice templates.'
        });
      }
      if (err?.status === 404) error(404, 'Template not found');
      return fail(400, { values, error: readableError(err, 'Could not save this template.') });
    }

    redirect(303, '/invoices/templates');
  }
};
