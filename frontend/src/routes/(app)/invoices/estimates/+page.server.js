import { fail, redirect } from '@sveltejs/kit';
import { listEstimates, convertEstimate } from '$lib/server/v2/estimates.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * The estimates worklist. `load` returns `{ estimates, totals }` — the exact
 * names the page reads; the data layer's own field is `estimates`, so there is
 * no rename to get wrong here.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return await listEstimates({ cookies });
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Raise an invoice from an accepted estimate and open the new draft. The id
   * comes from the row, and the API decides whether this caller may convert it
   * — a member who is neither creator nor assignee gets 403, and a second
   * conversion gets 400.
   */
  convert: async ({ cookies, request }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'Which estimate? None was given.' });

    let created;
    try {
      created = await convertEstimate({ cookies }, id);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error:
          err?.status === 403
            ? 'This estimate is not yours to convert.'
            : readableError(err, 'Could not raise an invoice from this estimate.')
      });
    }

    const newId = created?.invoice?.id;
    if (newId) redirect(303, `/invoices/${newId}`);
    return { converted: true };
  }
};
