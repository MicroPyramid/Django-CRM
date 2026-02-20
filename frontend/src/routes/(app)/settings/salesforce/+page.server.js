import { apiRequest } from '$lib/api-helpers.js';
import { fail } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  try {
    const status = await apiRequest('/salesforce/status/', {}, { cookies });
    return { sfStatus: status };
  } catch {
    return { sfStatus: { connected: false, has_credentials: false } };
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  saveCredentials: async ({ request, cookies }) => {
    const formData = await request.formData();
    const client_id = formData.get('client_id')?.toString().trim();
    const client_secret = formData.get('client_secret')?.toString().trim();
    const login_url = formData.get('login_url')?.toString().trim() || 'https://login.salesforce.com';

    if (!client_id || !client_secret) {
      return fail(400, { credentialError: 'Both Client ID and Client Secret are required.' });
    }

    // Step 1: Save credentials
    try {
      await apiRequest(
        '/salesforce/credentials/',
        { method: 'POST', body: { client_id, client_secret, login_url } },
        { cookies }
      );
    } catch (err) {
      return fail(400, { credentialError: err?.message || 'Failed to save credentials.' });
    }

    // Step 2: Immediately connect using Client Credentials flow
    try {
      await apiRequest('/salesforce/connect/', { method: 'POST' }, { cookies });
      return { connected: true };
    } catch (err) {
      return fail(400, {
        credentialError: err?.message || 'Credentials saved but failed to connect to Salesforce. Check your Connected App settings.'
      });
    }
  },
  disconnect: async ({ cookies }) => {
    try {
      await apiRequest('/salesforce/disconnect/', { method: 'DELETE' }, { cookies });
      return { disconnected: true };
    } catch (err) {
      return fail(400, { credentialError: err?.message || 'Failed to disconnect.' });
    }
  }
};
