import { fail } from '@sveltejs/kit';
import { getReopenPolicy, updateReopenPolicy } from '$lib/server/v2/reopen.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getReopenPolicy({ cookies });
}

/** @type {import('./$types').Actions} */
export const actions = {
  // Admin-only. `load`'s `can_edit` hides the "Edit policy" control for a
  // member, but that is the affordance, not the check. `ReopenPolicyView.put`
  // 403s a non-admin regardless of what reaches it; this branch turns that
  // into a sentence instead of a raw backend error string.
  async update(event) {
    const form = await event.request.formData();

    // The two booleans are read as "was the checkbox submitted", the normal
    // HTML convention: an unchecked box sends nothing at all.
    const values = {
      is_enabled: form.get('is_enabled') === 'true',
      notify_assigned: form.get('notify_assigned') === 'true',
      reopen_window_days: form.get('reopen_window_days')?.toString() ?? '',
      reopen_to_status: form.get('reopen_to_status')?.toString() ?? ''
    };

    try {
      await updateReopenPolicy(event, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { update: { error: 'Only an admin can change the reopen policy.' } });
      }
      return fail(400, {
        update: { error: readableError(err, 'Could not save the reopen policy.') }
      });
    }

    // No redirect. The policy is on this page and `load` re-runs after an
    // action, so the new values appear where the user is already looking.
    return { updated: true };
  }
};
