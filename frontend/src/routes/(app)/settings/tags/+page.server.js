import { fail } from '@sveltejs/kit';
import { getTags, createTag, archiveTag, restoreTag } from '$lib/server/v2/tags.js';
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
  },

  // Turns a tag off. Admin-only on the backend (`TagsDetailView.delete`),
  // same split as `create`: `can_edit` hides the control for a member, this
  // branch is what actually matters if that hint is bypassed. The backend
  // soft-archives (`is_active = False`); it never deletes the row, so the
  // error copy below stays consistent with that, nothing here talks about
  // removal.
  async archive(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    if (!id) return fail(400, { archive: { error: 'That tag could not be identified.' } });

    try {
      await archiveTag(event, id);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { archive: { error: 'Only an admin can turn a tag off.' } });
      }
      return fail(400, {
        archive: { error: readableError(err, 'Could not turn that tag off.') }
      });
    }
    return { archived: true };
  },

  // Turns an archived tag back on. Same admin-only gate as `archive`.
  async restore(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    if (!id) return fail(400, { restore: { error: 'That tag could not be identified.' } });

    try {
      await restoreTag(event, id);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { restore: { error: 'Only an admin can turn a tag back on.' } });
      }
      return fail(400, {
        restore: { error: readableError(err, 'Could not turn that tag back on.') }
      });
    }
    return { restored: true };
  }
};
