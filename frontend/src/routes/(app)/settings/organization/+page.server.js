import { getOrgSettings } from '#lib/server/v2/organization.js';

/**
 * Organization settings (read). GET is open to any member; `can_edit` (from
 * the JWT role claim) decides whether the page shows the edit affordance, and
 * the edit route and the backend PATCH are what enforce admin-only. Industry
 * apps and sample data live in Settings › Apps.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return await getOrgSettings({ cookies });
}
