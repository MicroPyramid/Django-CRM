import { fail, redirect } from '@sveltejs/kit';
import { createArticle } from '$lib/server/v2/solutions.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals }) {
  return {
    // Decides whether the form offers "Approved" and the publish switch at
    // all. The API refuses both for anyone else, so offering them would be a
    // form that fails on submit for reasons the writer cannot see.
    canRelease: /** @type {any} */ (locals).profile?.role === 'ADMIN'
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async ({ cookies, request }) => {
    const form = await request.formData();

    const values = {
      title: form.get('title')?.toString().trim() ?? '',
      description: form.get('description')?.toString().trim() ?? '',
      status: form.get('status')?.toString() || 'draft',
      // A checkbox that is off submits nothing at all, which on a *create* is
      // unambiguous. There is no stored value for "unchanged" to mean.
      is_published: form.get('is_published') === 'on'
    };

    /** @type {any} */
    let created;
    try {
      created = await createArticle({ cookies }, values);
    } catch (/** @type {any} */ err) {
      return fail(400, { values, error: readableError(err, 'Could not save this article.') });
    }

    redirect(303, `/solutions/${created.id}`);
  }
};
