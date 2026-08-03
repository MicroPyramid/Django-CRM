import { fail } from '@sveltejs/kit';
import { addContactNote, getContact } from '$lib/server/v2/contacts.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  return await getContact({ cookies }, params.id);
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Log a note against the contact, with an optional file. The body carries only
   * the note text and the file; who wrote it and which org it belongs to are
   * derived server-side from the JWT (see `addContactNote`), never from the form.
   *
   * A contact accepts a file on its own, unlike a lead, `ContactDetailView.post`
   * saves the attachment in a separate block from the comment, so this refuses
   * only the empty case: nothing typed and nothing picked. The DRF view enforces
   * the same access as reading the contact, so this action cannot post to a
   * contact the caller could not open.
   */
  note: async ({ cookies, params, request }) => {
    const form = await request.formData();
    const comment = form.get('comment')?.toString().trim() ?? '';

    const picked = form.get('attachment');
    const file =
      picked && typeof picked === 'object' && 'size' in picked && picked.size > 0 ? picked : null;

    if (!comment && !file) {
      return fail(400, { message: 'Write a note or attach a file before you save.' });
    }

    try {
      await addContactNote({ cookies }, params.id, comment, file);
    } catch (/** @type {any} */ err) {
      return fail(400, { message: String(err?.message ?? 'Could not save that note.') });
    }

    return { noted: true };
  }
};
