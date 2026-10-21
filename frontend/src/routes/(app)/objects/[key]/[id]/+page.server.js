import { fail, redirect } from '@sveltejs/kit';
import {
  checkId,
  checkKey,
  deleteAttachment,
  deleteRecord,
  recordPage,
  uploadAttachment
} from '#lib/server/v2/custom-objects.js';
import { pairForDisplay } from '#lib/server/v2/record-fields.js';
import { readableError } from '#lib/server/v2/form-errors.js';
import { uploadTooLarge } from '#lib/v2/custom-objects.js';

/** @param {any} err */
const refusalCode = (err) => (err?.status >= 400 && err?.status < 500 ? err.status : 400);

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  const page = await recordPage({ cookies }, params.key, params.id);
  const fields = page.definition.fields ?? [];
  return {
    ...page,
    details: pairForDisplay(
      fields.filter((/** @type {any} */ f) => f.field_type !== 'link'),
      page.record.custom_fields
    ),
    linkFields: fields.filter((/** @type {any} */ f) => f.field_type === 'link')
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  async delete({ cookies, params }) {
    const key = checkKey(params.key);
    const id = checkId(params.id);
    try {
      await deleteRecord({ cookies }, key, id);
    } catch (/** @type {any} */ err) {
      return fail(refusalCode(err), {
        deleteError: readableError(err, 'Could not delete this record.')
      });
    }
    redirect(303, `/objects/${key}`);
  },

  async upload({ cookies, params, request }) {
    const key = checkKey(params.key);
    const id = checkId(params.id);
    const picked = (await request.formData()).get('file');
    if (!picked || typeof picked !== 'object' || !('size' in picked) || picked.size === 0) {
      return fail(400, { uploadError: 'Choose a file to upload.' });
    }
    const tooLarge = uploadTooLarge(picked);
    if (tooLarge) return fail(400, { uploadError: tooLarge });
    try {
      await uploadAttachment({ cookies }, key, id, picked);
    } catch (/** @type {any} */ err) {
      return fail(refusalCode(err), {
        uploadError: readableError(err, 'Could not upload that file.')
      });
    }
    return { uploaded: true };
  },

  async deleteFile({ cookies, params, request }) {
    const key = checkKey(params.key);
    const id = checkId(params.id);
    const attachment = checkId(String((await request.formData()).get('attachment') ?? ''));
    try {
      await deleteAttachment({ cookies }, key, id, attachment);
    } catch (/** @type {any} */ err) {
      return fail(refusalCode(err), {
        fileError: readableError(err, 'Could not delete that file.')
      });
    }
    return { fileDeleted: true };
  }
};
