import { fail, redirect } from '@sveltejs/kit';
import { getArticle, updateArticle } from '$lib/server/v2/solutions.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * The mock's detail page had an Edit button that went nowhere, so this route
 * is new rather than converted.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, locals, params }) {
  const { article } = await getArticle({ cookies }, params.id);
  return {
    article,
    canRelease: /** @type {any} */ (locals).profile?.role === 'ADMIN',
    form: {
      title: article.title,
      description: article.description,
      status: article.status
    }
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  save: async ({ cookies, params, request }) => {
    const form = await request.formData();

    /** @type {Record<string, any>} */
    const values = {
      title: form.get('title')?.toString().trim() ?? '',
      description: form.get('description')?.toString().trim() ?? ''
    };

    /*
     * The status is only sent when somebody actually changed it.
     *
     * This is the same "absent means unchanged" rule the other five modules
     * use for many-to-many fields, and here it matters for a different
     * reason: `SolutionDetailView` asks whether the request *moves* `status`
     * before demanding an admin. Sending the article's existing status on
     * every save is harmless for an admin and would be a 403 for the author
     * of an already-approved article who only fixed a typo, a form that
     * refuses to save what it just showed you.
     *
     * `is_published` is not on this form at all. It is the publish button on
     * the article page, which is a decision rather than a field.
     */
    const status = form.get('status')?.toString() ?? '';
    const statusWas = form.get('status_original')?.toString() ?? '';
    if (status && status !== statusWas) values.status = status;

    try {
      await updateArticle({ cookies }, params.id, values);
    } catch (/** @type {any} */ err) {
      return fail(400, { values, error: readableError(err, 'Could not save this article.') });
    }

    redirect(303, `/solutions/${params.id}`);
  }
};
