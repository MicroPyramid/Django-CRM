import { fail } from '@sveltejs/kit';
import {
  listApprovals,
  approveApproval,
  rejectApproval,
  cancelApproval
} from '$lib/server/v2/approvals.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * The approvals queue. `load` returns `{ approvals, totals, rules }`; the three
 * actions decide a request. Authorization (approver pool, separation of duties,
 * pending-only) is enforced by the backend. These actions just surface its
 * error. On success `use:enhance` re-runs `load`, so the row reflects the real
 * new state rather than an optimistic guess.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return await listApprovals({ cookies });
}

/** @type {import('./$types').Actions} */
export const actions = {
  approve: async ({ cookies, request }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'Which approval? None was given.' });
    try {
      await approveApproval({ cookies }, id, form.get('note')?.toString() || '');
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error: readableError(err, 'Could not approve this request.')
      });
    }
    return { approved: true };
  },

  reject: async ({ cookies, request }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    const reason = form.get('reason')?.toString()?.trim();
    if (!id) return fail(400, { error: 'Which approval? None was given.' });
    if (!reason) return fail(400, { error: 'A rejection needs a reason.' });
    try {
      await rejectApproval({ cookies }, id, reason);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error: readableError(err, 'Could not reject this request.')
      });
    }
    return { rejected: true };
  },

  cancel: async ({ cookies, request }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'Which approval? None was given.' });
    try {
      await cancelApproval({ cookies }, id);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error: readableError(err, 'Could not withdraw this request.')
      });
    }
    return { cancelled: true };
  }
};
