import { fail } from '@sveltejs/kit';
import { addLeadNote, getLead } from '$lib/server/v2/leads.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  return await getLead({ cookies }, params.id);
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Log a note against the lead. The body carries only the note text; who
   * wrote it and which org it belongs to are derived server-side from the JWT
   * (see `addLeadNote`), never from the form. An empty note is refused here so
   * the API is not asked to store a blank comment, and the DRF view enforces
   * the same access as reading the lead — this action cannot post to a lead the
   * caller could not open.
   */
  note: async ({ cookies, params, request }) => {
    const form = await request.formData();
    const comment = form.get('comment')?.toString().trim() ?? '';

    const picked = form.get('attachment');
    const file =
      picked && typeof picked === 'object' && 'size' in picked && picked.size > 0 ? picked : null;

    // A note is required, and a file only rides with one — the API drops an
    // attachment posted without a comment (see `addLeadNote`), so refusing it
    // here turns a silent no-op into a message somebody can act on.
    if (!comment) {
      return fail(400, {
        message: file
          ? 'Add a note to save alongside the file.'
          : 'Write something before you save the note.'
      });
    }

    try {
      await addLeadNote({ cookies }, params.id, comment, file);
    } catch (/** @type {any} */ err) {
      return fail(400, { message: String(err?.message ?? 'Could not save that note.') });
    }

    return { noted: true };
  }
};
