import { fail, redirect } from '@sveltejs/kit';
import { createObject, listObjectsForSettings } from '#lib/server/v2/custom-objects.js';
import { readableError } from '#lib/server/v2/form-errors.js';
import { readObjectForm } from '#lib/server/v2/object-settings.js';
import { viewerIsAdmin } from '#lib/server/v2/organization.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  return {
    answer: await listObjectsForSettings({ cookies }),
    can_edit: viewerIsAdmin(cookies)
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  // The server refuses non-admins and orgs without the plan; `can_edit` only hides the control.
  async create(event) {
    const form = await event.request.formData();
    const body = readObjectForm(form, { creating: true });
    try {
      await createObject(event, body);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, {
          create: { error: err?.body?.detail ?? 'Only an admin can add custom objects.' }
        });
      }
      return fail(400, {
        create: { error: readableError(err, 'Could not add the object.'), values: body }
      });
    }
    redirect(303, `/settings/objects/${encodeURIComponent(String(body.key))}`);
  }
};
