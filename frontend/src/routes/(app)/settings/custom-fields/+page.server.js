import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const SUPPORTED_TARGETS = [
  { value: 'Case', label: 'Tickets', enabled: true },
  { value: 'Lead', label: 'Leads', enabled: true },
  { value: 'Contact', label: 'Contacts', enabled: true },
  { value: 'Account', label: 'Accounts', enabled: true },
  { value: 'Opportunity', label: 'Opportunities', enabled: true },
  { value: 'Task', label: 'Tasks', enabled: true },
  { value: 'Invoice', label: 'Invoices', enabled: true },
  { value: 'Estimate', label: 'Estimates', enabled: true },
  { value: 'RecurringInvoice', label: 'Recurring Invoices', enabled: true }
];

/** @type {import('./$types').PageServerLoad} */
export async function load({ url, cookies, locals }) {
  const profile = locals.profile;
  if (profile?.role !== 'ADMIN' && !profile?.is_organization_admin) {
    throw error(403, 'Only admins can manage custom fields');
  }

  const target = url.searchParams.get('target') || 'Case';

  try {
    const data = await apiRequest(
      `/custom-fields/?target_model=${encodeURIComponent(target)}`,
      {},
      { cookies, org: locals?.org }
    );
    return {
      target,
      targets: SUPPORTED_TARGETS,
      definitions: data.definitions || []
    };
  } catch (err) {
    console.error('Failed to load custom fields:', err);
    throw error(500, 'Failed to load custom fields');
  }
}

function parseOptions(raw) {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return null;
    return parsed
      .map((entry) => ({
        value: String(entry?.value ?? '').trim(),
        label: String(entry?.label ?? '').trim()
      }))
      .filter((entry) => entry.value && entry.label);
  } catch {
    return null;
  }
}

function buildBody(formData) {
  const fieldType = String(formData.get('field_type') || 'text');
  const optionsRaw = formData.get('options');
  return {
    target_model: String(formData.get('target_model') || 'Case'),
    key: String(formData.get('key') || '').trim(),
    label: String(formData.get('label') || '').trim(),
    field_type: fieldType,
    options: fieldType === 'dropdown' ? parseOptions(optionsRaw) : null,
    is_required: formData.get('is_required') === 'true',
    is_filterable: formData.get('is_filterable') === 'true',
    display_order: Number(formData.get('display_order') || 0),
    is_active: formData.get('is_active') !== 'false'
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const body = buildBody(formData);
    try {
      const created = await apiRequest(
        '/custom-fields/',
        { method: 'POST', body },
        { cookies, org: locals?.org }
      );
      return { success: true, created };
    } catch (err) {
      console.error('Failed to create custom field:', err);
      return fail(400, { error: err?.message || 'Failed to create custom field' });
    }
  },

  update: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = String(formData.get('id') || '');
    if (!id) return fail(400, { error: 'Missing field id' });
    const body = buildBody(formData);
    // key/target_model/field_type are immutable post-create; the API rejects changes,
    // but we strip them client-side too so a stale form can't accidentally bump them.
    delete body.target_model;
    delete body.field_type;
    delete body.key;
    try {
      const updated = await apiRequest(
        `/custom-fields/${id}/`,
        { method: 'PUT', body },
        { cookies, org: locals?.org }
      );
      return { success: true, updated };
    } catch (err) {
      console.error('Failed to update custom field:', err);
      return fail(400, { error: err?.message || 'Failed to update custom field' });
    }
  },

  delete: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = String(formData.get('id') || '');
    if (!id) return fail(400, { error: 'Missing field id' });
    try {
      await apiRequest(
        `/custom-fields/${id}/`,
        { method: 'DELETE' },
        { cookies, org: locals?.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Failed to delete custom field:', err);
      return fail(400, { error: err?.message || 'Failed to delete custom field' });
    }
  }
};
