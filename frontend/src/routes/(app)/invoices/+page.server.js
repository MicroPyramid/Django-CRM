import { fail } from '@sveltejs/kit';
import { listInvoices, sendInvoice } from '$lib/server/v2/invoices.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/**
 * The invoice list.
 *
 * Server load, so the JWT cookie stays server-side. Rows and the header pills
 * arrive from one API call. The totals are the API's job now, aggregated over
 * the whole visible queryset rather than summed from the page.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies }) {
  return await listInvoices({ cookies });
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Send a draft, or re-send an overdue invoice as a reminder, the same POST
   * either way. The mock's inline "Send" / "Send a reminder" buttons did
   * nothing; this is that button doing the thing. The API refuses to send a
   * Paid or Cancelled invoice with a 400, and those rows never show the button.
   */
  send: async ({ cookies, request }) => {
    const form = await request.formData();
    const id = form.get('id')?.toString();
    if (!id) return fail(400, { error: 'Which invoice?' });

    try {
      await sendInvoice({ cookies }, id);
    } catch (/** @type {any} */ err) {
      return fail(err?.status === 403 ? 403 : 400, {
        error:
          err?.status === 403
            ? 'That invoice is not yours to send.'
            : readableError(err, 'Could not send that invoice.')
      });
    }
    return { sent: id };
  }
};
