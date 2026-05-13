import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
  if (!locals.org) throw error(401, 'Organization context required');

  try {
    const detail = await apiRequest(
      `/cases/solutions/${params.id}/`,
      {},
      { cookies, org: locals.org }
    );
    if (!detail || !detail.id) throw error(404, 'Solution not found');
    return { solution: detail };
  } catch (err) {
    if (err?.status) throw err;
    console.error('Load solution error:', err);
    throw error(500, `Failed to load solution: ${err?.message || 'unknown error'}`);
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  update: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    const title = form.get('title')?.toString().trim();
    const description = form.get('description')?.toString() || '';
    const status = form.get('status')?.toString() || 'draft';
    if (!title) return fail(400, { error: 'Title is required' });

    try {
      await apiRequest(
        `/cases/solutions/${params.id}/`,
        { method: 'PATCH', body: { title, description, status } },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Update solution error:', err);
      return fail(err?.status || 500, {
        error: err?.message || 'Failed to update solution'
      });
    }
  },

  publish: async ({ params, locals, cookies }) => {
    try {
      await apiRequest(
        `/cases/solutions/${params.id}/publish/`,
        { method: 'POST', body: {} },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Publish solution error:', err);
      return fail(err?.status || 500, {
        error: err?.message || 'Failed to publish solution'
      });
    }
  },

  unpublish: async ({ params, locals, cookies }) => {
    try {
      await apiRequest(
        `/cases/solutions/${params.id}/unpublish/`,
        { method: 'POST', body: {} },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Unpublish solution error:', err);
      return fail(err?.status || 500, {
        error: err?.message || 'Failed to unpublish solution'
      });
    }
  },

  delete: async ({ params, locals, cookies }) => {
    try {
      await apiRequest(
        `/cases/solutions/${params.id}/`,
        { method: 'DELETE' },
        { cookies, org: locals.org }
      );
    } catch (err) {
      console.error('Delete solution error:', err);
      return fail(err?.status || 500, {
        error: err?.message || 'Failed to delete solution'
      });
    }
    throw redirect(303, '/solutions');
  }
};
