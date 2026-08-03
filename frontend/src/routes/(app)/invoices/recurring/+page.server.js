import { fail } from '@sveltejs/kit';
import { listRecurringInvoices, toggleRecurring } from '$lib/server/v2/recurring.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * The schedules worklist. `load` returns `{ schedules, totals }`. The names the
 * page reads; the data layer's own field is `schedules`, so no rename here.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return await listRecurringInvoices({ cookies });
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Pause a live schedule or resume a paused one. The id comes from the row, and
   * the API decides whether this caller may toggle it. A member who is neither
   * creator nor assignee gets 403.
   */
  toggle: async ({ cookies, request }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'Which schedule? None was given.' });

    try {
      await toggleRecurring({ cookies }, id);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error:
          err?.status === 403
            ? 'This schedule is not yours to pause or resume.'
            : readableError(err, 'Could not change this schedule.')
      });
    }
    return { toggled: true };
  }
};
