import { fail } from '@sveltejs/kit';
import { getOrgSettings } from '$lib/server/v2/organization.js';
import { listPacks, applyPack, clearSampleData } from '$lib/server/packs.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * Organization settings (read) + the "Vertical pack" section.
 *
 * Server load, so the JWT cookie stays server-side. GET is open to any member;
 * `can_edit` (from the JWT role claim) decides whether the page shows the edit
 * affordance, and the edit route + the backend PATCH are what actually enforce
 * admin-only. The same `can_edit` flag is reused below to decide whether the
 * pack list and its actions render at all. Vertical packs are admin-only for
 * the identical reason (`PackApplyView`/`PackSampleDataView` both 403 a
 * non-admin server-side), so there is no second admin check to invent.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  const settings = await getOrgSettings({ cookies });

  // GET /api/packs/ needs IsAuthenticated only, no org context, but a
  // reload of this page must never break over a transient failure here, so
  // this follows the same "empty list on error" fallback the org-creation
  // page already established for the identical call.
  let packs = [];
  try {
    packs = await listPacks(cookies);
  } catch (/** @type {any} */ err) {
    console.error('Could not load vertical packs:', err?.message, err?.status);
  }

  return { ...settings, packs };
}

/** @type {import('./$types').Actions} */
export const actions = {
  // Applying is additive-only and safe to repeat, a pack already applied
  // just reports everything as skipped. There is deliberately no guard here
  // against re-submitting the currently-applied pack.
  apply: async ({ cookies, request }) => {
    const packId = (await request.formData()).get('pack_id')?.toString();
    if (!packId) return fail(400, { error: 'Choose a pack to apply.' });

    try {
      const { report } = await applyPack(cookies, packId);
      return { appliedPackId: packId, report };
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { error: 'Only an administrator can apply a vertical pack.' });
      }
      return fail(400, { error: readableError(err, 'Could not apply this pack.') });
    }
  },

  clearSampleData: async ({ cookies }) => {
    try {
      const { deleted, retained_by_type } = await clearSampleData(cookies);
      // Retained records are not a failure. They are demo rows the user has
      // since attached real work to, which the backend deliberately keeps.
      // Passing the count through lets the page say so instead of reporting a
      // smaller number than the user expected with no explanation.
      const retained = Object.values(retained_by_type ?? {}).reduce((a, b) => a + b, 0);
      return { cleared: deleted ?? 0, retained };
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { error: 'Only an administrator can clear sample data.' });
      }
      return fail(400, { error: readableError(err, 'Could not clear sample data.') });
    }
  }
};
