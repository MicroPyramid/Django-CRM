import { error, fail } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

const PAGE_SIZE = 20;

/** @type {import('./$types').PageServerLoad} */
export async function load({ url, cookies, locals }) {
  if (!locals.org) throw error(401, 'Organization context required');

  const statusFilter = url.searchParams.get('status') || '';
  const publishedFilter = url.searchParams.get('published') || '';
  const search = url.searchParams.get('q') || '';
  const pageNum = Math.max(1, parseInt(url.searchParams.get('page') || '1', 10));
  const offset = (pageNum - 1) * PAGE_SIZE;

  const qs = new URLSearchParams();
  qs.set('limit', String(PAGE_SIZE));
  qs.set('offset', String(offset));
  if (statusFilter) qs.set('status', statusFilter);
  if (publishedFilter === 'yes') qs.set('is_published', 'true');
  if (publishedFilter === 'no') qs.set('is_published', 'false');
  if (search) qs.set('search', search);

  try {
    const data = await apiRequest(
      `/cases/solutions/?${qs.toString()}`,
      {},
      { cookies, org: locals.org }
    );
    return {
      solutions: data?.results || [],
      total: data?.count || 0,
      pageNum,
      pageSize: PAGE_SIZE,
      filters: { status: statusFilter, published: publishedFilter, search }
    };
  } catch (err) {
    console.error('Solutions list load failed:', err);
    return {
      solutions: [],
      total: 0,
      pageNum,
      pageSize: PAGE_SIZE,
      filters: { status: statusFilter, published: publishedFilter, search },
      loadError: err?.message || 'Could not load solutions'
    };
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  delete: async ({ request, locals, cookies }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'id required' });
    try {
      await apiRequest(
        `/cases/solutions/${id}/`,
        { method: 'DELETE' },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Delete solution error:', err);
      return fail(err?.status || 500, {
        error: err?.message || 'Failed to delete solution'
      });
    }
  },

  publish: async ({ request, locals, cookies }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'id required' });
    try {
      await apiRequest(
        `/cases/solutions/${id}/publish/`,
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

  unpublish: async ({ request, locals, cookies }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'id required' });
    try {
      await apiRequest(
        `/cases/solutions/${id}/unpublish/`,
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
  }
};
