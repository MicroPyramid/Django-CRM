import { fail } from '@sveltejs/kit';
import { listTasks, setTaskDone } from '$lib/server/v2/tasks.js';

/**
 * The task queue.
 *
 * `open` is the default view because a task list is a to-do list: the finished
 * ones are history, and history belongs behind a filter rather than at the top
 * of the thing you work from. `?all=1` shows everything, which is the URL the
 * "Show completed" control points at.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  const showAll = event.url.searchParams.get('all') === '1';
  const params = new URLSearchParams();
  const search = event.url.searchParams.get('q');
  if (search) params.set('search', search);
  const priority = event.url.searchParams.get('priority');
  if (priority) params.set('priority', priority);

  const { results, totals, owners } = await listTasks(event, params);

  return {
    // Filtered here rather than with `?status=`, because the totals the header
    // reads have to cover both; "3 of 11 open" needs the 11.
    tasks: showAll ? results : results.filter((task) => !task.is_done),
    totals,
    owners,
    showAll,
    filters: { q: search ?? '', priority: priority ?? '' },
    canDelete: event.locals.profile?.role === 'ADMIN'
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Tick a row off, or put it back.
   *
   * The mock did this in local state with a note saying it must never look
   * saved without being saved. This is that PATCH: the row reverts on failure
   * because the page reloads from the API either way.
   */
  toggle: async (event) => {
    const form = await event.request.formData();
    const id = form.get('id')?.toString();
    const done = form.get('done')?.toString() === 'true';
    if (!id) return fail(400, { error: 'Which task?' });

    try {
      await setTaskDone(event, id, done);
    } catch (/** @type {any} */ err) {
      // 403 is the interesting one: the list can show a task you may read
      // through a shared parent but not edit.
      return fail(err?.status === 403 ? 403 : 400, {
        error:
          err?.status === 403
            ? 'That task is not yours to change.'
            : (err?.body?.errors ?? 'That did not save. Try again.')
      });
    }
    return { done };
  }
};
