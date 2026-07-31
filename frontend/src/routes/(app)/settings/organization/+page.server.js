import { getOrgSettings } from '$lib/server/v2/organization.js';

/**
 * Organization settings (read).
 *
 * Server load, so the JWT cookie stays server-side. GET is open to any member;
 * `can_edit` (from the JWT role claim) decides whether the page shows the edit
 * affordance, and the edit route + the backend PATCH are what actually enforce
 * admin-only.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return await getOrgSettings({ cookies });
}
