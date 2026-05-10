import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals }) {
  if (!locals.org) throw error(401, 'Organization context required');
  return {};
}

/** @type {import('./$types').Actions} */
export const actions = {
  default: async ({ request, locals, cookies }) => {
    const form = await request.formData();
    const title = form.get('title')?.toString().trim();
    const description = form.get('description')?.toString() || '';
    const status = form.get('status')?.toString() || 'draft';

    if (!title) return fail(400, { error: 'Title is required', title, description, status });

    try {
      const created = await apiRequest(
        '/cases/solutions/',
        { method: 'POST', body: { title, description, status } },
        { cookies, org: locals.org }
      );
      const id = created?.id;
      if (!id) return fail(500, { error: 'Backend returned no id', title, description, status });
      throw redirect(303, `/solutions/${id}`);
    } catch (err) {
      if (err?.status === 303) throw err;
      console.error('Create solution error:', err);
      return fail(err?.status || 500, {
        error: err?.message || 'Failed to create solution',
        title,
        description,
        status
      });
    }
  }
};
