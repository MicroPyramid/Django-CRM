import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

function isAdmin(profile) {
  return profile?.role === 'ADMIN' || profile?.is_organization_admin === true;
}

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, locals }) {
  const profile = locals.profile;
  // The settings page surfaces both org and personal macros, so non-admins
  // can land here too — they just can't create/edit org-scope rows. Block
  // entirely-anonymous access via the standard auth gate above this layer.
  if (!profile) {
    throw error(401, 'Login required');
  }
  try {
    const data = await apiRequest('/macros/', {}, { cookies, org: locals?.org });
    return {
      macros: data?.results || [],
      isAdmin: isAdmin(profile),
      currentProfileId: /** @type {any} */ (profile)?.id || null
    };
  } catch (err) {
    console.error('Failed to load macros:', err);
    throw error(500, 'Failed to load macros');
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const title = formData.get('title')?.toString().trim();
    const body = formData.get('body')?.toString();
    const scope = formData.get('scope')?.toString() || 'personal';
    if (!title || !body) {
      return fail(400, { error: 'Title and body are required' });
    }
    try {
      await apiRequest(
        '/macros/',
        { method: 'POST', body: { title, body, scope } },
        { cookies, org: locals?.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Failed to create macro:', err);
      return fail(400, { error: err?.message || 'Failed to create macro' });
    }
  },

  update: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = formData.get('id')?.toString();
    if (!id) return fail(400, { error: 'Missing macro id' });
    /** @type {Record<string, unknown>} */
    const body = {};
    const title = formData.get('title')?.toString().trim();
    if (title !== undefined) body.title = title;
    const macroBody = formData.get('body');
    if (macroBody !== null) body.body = macroBody.toString();
    const isActive = formData.get('is_active');
    if (isActive !== null) body.is_active = isActive.toString() === 'true';
    try {
      await apiRequest(
        `/macros/${id}/`,
        { method: 'PATCH', body },
        { cookies, org: locals?.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Failed to update macro:', err);
      return fail(400, { error: err?.message || 'Failed to update macro' });
    }
  },

  remove: async ({ request, cookies, locals }) => {
    const formData = await request.formData();
    const id = formData.get('id')?.toString();
    if (!id) return fail(400, { error: 'Missing macro id' });
    try {
      await apiRequest(
        `/macros/${id}/`,
        { method: 'DELETE' },
        { cookies, org: locals?.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Failed to delete macro:', err);
      return fail(400, { error: err?.message || 'Failed to delete macro' });
    }
  }
};
