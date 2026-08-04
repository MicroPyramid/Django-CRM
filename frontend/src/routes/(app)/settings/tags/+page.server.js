import { fail } from '@sveltejs/kit';
import { getTags, createTag } from '$lib/server/v2/tags.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return getTags({ cookies });
}

/** @type {import('./$types').Actions} */
export const actions = {
  // Admin-only. `load`'s `can_edit` hides the "New tag" control for a member,
  // but that is only the affordance; this check is the one that matters.
  // `TagsListView.post` (`backend/common/views/tags_views.py:143-149`) 403s a
  // non-admin regardless of what reaches it, so this branch exists to turn
  // that response into a message instead of a raw backend error string, not
  // to be the authority itself.
  async create(event) {
    const form = await event.request.formData();
    const name = form.get('name')?.toString() ?? '';

    try {
      await createTag(event, { name });
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { create: { name, error: 'Only an admin can create tags.' } });
      }
      return fail(400, {
        create: { name, error: readableError(err, 'Could not create the tag.') }
      });
    }

    // No redirect. The list is on this page, and `load` re-runs after an
    // action, so the new tag appears where the user is already looking.
    return { created: true };
  }
};
