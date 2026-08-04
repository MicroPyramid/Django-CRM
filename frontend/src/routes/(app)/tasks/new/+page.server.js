import { fail, redirect } from '@sveltejs/kit';
import { createTask, getTaskFormOptions } from '$lib/server/v2/tasks.js';
import { readableError } from '$lib/server/v2/form-errors.js';
import { listTickets } from '$lib/server/v2/tickets.js';
import { listDeals } from '$lib/server/v2/deals.js';
import { listLeads } from '$lib/server/v2/leads.js';

/**
 * The new-task form.
 *
 * A task has one parent (account, deal, ticket or lead), and the form has to
 * offer all four, so this loads four catalogues. The accounts one comes free
 * with the task list endpoint; the other three are separate calls, run
 * concurrently. A picker that fails keeps its empty list rather than failing
 * the page: a form that can still write a task with no parent is more use
 * than a 500.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  const [options, tickets, deals, leads] = await Promise.allSettled([
    getTaskFormOptions(event),
    listTickets(event, new URLSearchParams({ limit: '100' })),
    // Open deals only, matching what this picker offered before `listDeals`
    // stopped assuming it: attaching a task to a deal you already closed is
    // an edge case the picker does not need to carry by default.
    listDeals(event, new URLSearchParams({ open: 'true', limit: '100' })),
    listLeads(event, new URLSearchParams({ limit: '100' }))
  ]);

  const settled = options.status === 'fulfilled' ? options.value : { owners: [], accounts: [] };

  return {
    owners: settled.owners,
    parents: {
      account: settled.accounts ?? [],
      opportunity:
        deals.status === 'fulfilled'
          ? deals.value.results.map((/** @type {any} */ d) => ({ id: d.id, name: d.name }))
          : [],
      case:
        tickets.status === 'fulfilled'
          ? tickets.value.results.map((/** @type {any} */ t) => ({ id: t.id, name: t.name }))
          : [],
      lead:
        leads.status === 'fulfilled'
          ? leads.value.results.map((/** @type {any} */ l) => ({
              id: l.id,
              name:
                `${l.first_name} ${l.last_name}`.trim() ||
                l.company_name ||
                l.email ||
                '(unnamed lead)'
            }))
          : []
    }
  };
}

/**
 * Read the one parent off the form.
 *
 * The form asks "attached to what?" once, a kind and an id, because the
 * model allows exactly one and now says so on every path. Four separate
 * pickers would have let somebody fill two and find out on submit.
 *
 * A chosen kind with no record is an error, not an empty parent. This
 * returned `{}` for that case and the task was created attached to nothing,
 * with a 303 that looked like it had worked, the same silent-success shape
 * the backend audit spent the morning removing. The `required` on the select
 * stops a browser getting here; it is not what makes it true.
 *
 * @param {FormData} form
 * @returns {{ parent?: Record<string, string>, error?: string }}
 */
function readParent(form) {
  const kind = form.get('parent_kind')?.toString() ?? '';
  if (!kind) return { parent: {} };
  const id = form.get(`parent_${kind}`)?.toString() ?? '';
  if (!id) {
    return {
      error: 'Pick which record this is attached to, or set "Attached to" back to Nothing.'
    };
  }
  return { parent: { [kind]: id } };
}

/** @type {import('./$types').Actions} */
export const actions = {
  create: async (event) => {
    const form = await event.request.formData();
    const kind = form.get('parent_kind')?.toString() ?? '';
    const { parent, error: parentError } = readParent(form);

    const values = {
      title: form.get('title')?.toString().trim() ?? '',
      status: form.get('status')?.toString() || 'New',
      priority: form.get('priority')?.toString() || 'Medium',
      // An empty date input submits "", which the API reads as a bad date
      // rather than as "none". Null is the one that means no due date.
      due_date: form.get('due_date')?.toString() || null,
      description: form.get('description')?.toString().trim() ?? '',
      assigned_to: form
        .getAll('assigned_to')
        .map((v) => v.toString())
        .filter(Boolean),
      ...(parent ?? {})
    };

    if (parentError) {
      return fail(400, { values: { ...values, parent_kind: kind }, error: parentError });
    }

    try {
      await createTask(event, values);
    } catch (/** @type {any} */ err) {
      return fail(400, {
        values: { ...values, parent_kind: kind },
        error: readableError(err, 'Could not save this task.')
      });
    }

    // `TaskListView.post` answers `{error: false, message: ...}` and not the
    // row, so there is no id to redirect to. The list is where the new task
    // is, and it is the page somebody working a queue wants next anyway.
    redirect(303, '/tasks');
  }
};
