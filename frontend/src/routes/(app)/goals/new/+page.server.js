import { fail, redirect } from '@sveltejs/kit';
import { getGoalFormOptions, createGoal, EDITABLE_FIELDS } from '$lib/server/v2/goals.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * Creating a goal.
 *
 * Admin-only. The load returns `can_edit: false` for a non-admin so the page can
 * render an "admins only" state instead of a form, and the create action is
 * gated again by the backend, `POST /api/opportunities/goals/` 403s a non-admin
 * regardless of what reaches it.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  return await getGoalFormOptions(event);
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async (event) => {
    const form = await event.request.formData();

    /** @type {Record<string, any>} */
    const values = {};
    // Text and select fields, plus the single `target` picker that stands in
    // for assigned_to/team. is_active is omitted on create. A new goal is
    // active (the model default), so there is nothing to choose yet.
    for (const field of [...EDITABLE_FIELDS, 'target']) {
      if (form.has(field)) values[field] = form.get(field)?.toString().trim() ?? '';
    }

    try {
      await createGoal(event, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { values, error: 'Only an admin can create goals.' });
      }
      return fail(400, {
        values,
        error: readableError(err, 'Could not create this goal.')
      });
    }

    redirect(303, '/goals');
  }
};
