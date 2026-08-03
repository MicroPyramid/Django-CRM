/**
 * Public Invoice Portal Page
 *
 * Public view for clients to see their invoice via token.
 * No authentication required.
 */

import { error } from '@sveltejs/kit';
import { env } from '$env/dynamic/public';

// The Django API, reached server-to-server. Absolute (not a relative `/api/...`
// that only resolves behind a production reverse proxy) so the anonymous portal
// works the same in dev and prod. The CSAT loader takes the same approach.
const API_BASE_URL = `${env.PUBLIC_DJANGO_API_URL}/api`;

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, fetch }) {
  const { token } = params;

  if (!token) {
    throw error(400, 'Invoice token is required');
  }

  try {
    // Fetch invoice from public API (no auth)
    const response = await fetch(`${API_BASE_URL}/public/invoice/${token}/`);

    if (!response.ok) {
      if (response.status === 404) {
        throw error(404, 'Invoice not found or link has expired');
      }
      throw error(response.status, 'Failed to load invoice');
    }

    // The v2 portal renders the Django shape directly (snake_case, template
    // nested), so pass it through rather than re-mapping to camelCase.
    const invoice = await response.json();

    return { invoice, token };
  } catch (err) {
    if (err.status) throw err;
    console.error('Error loading public invoice:', err);
    throw error(500, 'Failed to load invoice');
  }
}
