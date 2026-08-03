import { fail, redirect } from '@sveltejs/kit';
import { getUploadOptions, uploadDocument, STATUS_CHOICES } from '$lib/server/v2/documents.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * Uploading a document.
 *
 * Open to any org member: `POST /api/documents/` gates on auth + org context
 * only, so a rep can add their own file, not just an admin. `created_by` and
 * `org` are server-derived and never read from the body. The share pickers only
 * ever offer in-org people and teams, and the view re-scopes both to the
 * caller's org, so a share can never point at another tenant. (Editing and
 * deleting are the narrow writes, creator or admin, enforced server-side.)
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  return await getUploadOptions(event);
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async (event) => {
    const form = await event.request.formData();

    const title = form.get('title')?.toString().trim() ?? '';
    const statusRaw = form.get('status')?.toString() ?? 'active';
    const status = STATUS_CHOICES.includes(statusRaw) ? statusRaw : 'active';
    const file = form.get('document_file');
    const shared_to = form.getAll('shared_to').map((v) => v.toString());
    const teams = form.getAll('teams').map((v) => v.toString());

    // What the form re-fills on a rejected submit. The file is never echoed.
    // A browser will not let us re-populate a file input, so a rejected upload
    // asks for the file again, which is the honest thing to do.
    const values = { title, status, shared_to, teams };

    // Mirror the server's required-field checks so an obvious miss does not cost
    // a round trip. The serializer enforces both regardless.
    if (!title) {
      return fail(400, { values, error: 'Give the document a title.' });
    }
    if (!(file instanceof File) || file.size === 0) {
      return fail(400, { values, error: 'Choose a file to upload.' });
    }

    try {
      await uploadDocument(event.cookies, { title, status, file, shared_to, teams });
    } catch (/** @type {any} */ err) {
      if (err?.status === 401 || err?.status === 403) {
        return fail(err.status, { values, error: 'You do not have permission to upload here.' });
      }
      return fail(400, {
        values,
        error: readableError(err, 'Could not upload this document.')
      });
    }

    redirect(303, '/documents');
  }
};
