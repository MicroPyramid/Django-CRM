import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  try {
    const response = await apiRequest('/org/settings/', {}, { cookies });
    return {
      settings: response
    };
  } catch (err) {
    console.error('Failed to load org settings:', err);
    throw error(500, 'Failed to load organization settings');
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  update: async ({ request, cookies }) => {
    const formData = await request.formData();

    const data = {
      name: formData.get('name'),
      domain: formData.get('domain') || null,
      description: formData.get('description') || null,
      default_currency: formData.get('default_currency'),
      default_country: formData.get('default_country') || null
    };

    try {
      const response = await apiRequest(
        '/org/settings/',
        { method: 'PATCH', body: data },
        { cookies }
      );
      return { success: true, settings: response };
    } catch (err) {
      console.error('Failed to update org settings:', err);
      const message = err?.message || 'Failed to update settings';
      return fail(400, { error: message });
    }
  }
};
