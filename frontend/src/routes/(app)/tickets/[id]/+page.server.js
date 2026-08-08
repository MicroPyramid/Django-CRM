import { fail } from '@sveltejs/kit';
import {
  getTicket,
  getTicketTree,
  closeTicketWithChildren,
  replyToTicket,
  updateTicket
} from '$lib/server/v2/tickets.js';
import { getOrgSettings } from '$lib/server/v2/organization.js';
import { readableError } from '$lib/server/v2/form-errors.js';
import { openDescendants, subtreeTruncated, cascadedCount, closeResultMessage } from './close.js';

/**
 * The ticket, plus what closing it would take with it.
 *
 * The tree and the org settings are fetched ONLY for a ticket that has
 * children. Most tickets have none, and two extra requests on every ticket
 * open to answer a question that cannot arise is a cost paid for nothing.
 *
 * Neither extra is allowed to break the page: a ticket that will not render
 * because its tree call failed is a worse outcome than a close button that
 * falls back to the plain one. Both fall back quietly, and the close action
 * re-derives everything server-side anyway, so nothing here is trusted.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, params }) {
  const data = await getTicket({ cookies }, params.id);
  // `child_count` sits on the ticket itself here. The `server` block with a
  // `child_count` of its own belongs to the EDIT page's loader, and reading it
  // from this one is silently always-undefined, so the panel never appeared.
  if (!data.ticket?.child_count) return data;

  const [tree, settings] = await Promise.all([
    getTicketTree({ cookies }, params.id).catch(() => null),
    getOrgSettings({ cookies }).catch(() => null)
  ]);

  return {
    ...data,
    close: {
      descendants: openDescendants(tree?.root, params.id),
      truncated: subtreeTruncated(tree?.root, params.id),
      // `getOrgSettings` returns `{ org, can_edit }`, so the setting is one
      // level in. The checkbox's starting position, and the only place this
      // org setting reaches a web user. False when the org has not set it or
      // the fetch failed: a cascade nobody asked for must not start ticked.
      cascade_default: settings?.org?.auto_close_children_on_parent_close === true
    }
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Post a reply, or an internal note.
   *
   * A reply may also move the ticket; "answer and set to Pending" is one
   * decision, not two, so the status change goes with it when the composer
   * asked for one. The reply is posted first: if the status change is refused
   * (the close gate, say) the customer has still been answered, which is the
   * order that loses the least.
   */
  reply: async ({ cookies, params, request }) => {
    const form = await request.formData();
    const body = form.get('body')?.toString().trim() ?? '';
    const internal = form.get('internal') === 'on';
    const status = form.get('status')?.toString().trim() ?? '';

    const picked = form.get('attachment');
    const file =
      picked && typeof picked === 'object' && 'size' in picked && picked.size > 0 ? picked : null;

    // A ticket accepts a file on its own, the API saves the attachment in a
    // block separate from the comment, so this refuses only the empty case.
    if (!body && !file) {
      return fail(400, {
        body,
        internal,
        error: 'Write something or attach a file before sending.'
      });
    }

    try {
      await replyToTicket({ cookies }, params.id, { body, internal, file });
    } catch (/** @type {any} */ err) {
      return fail(400, { body, internal, error: readableError(err, 'Could not post this reply.') });
    }

    if (status) {
      try {
        await updateTicket({ cookies }, params.id, { status });
      } catch (/** @type {any} */ err) {
        return fail(400, {
          sent: true,
          error: readableError(err, `Reply posted, but the status stayed put.`)
        });
      }
    }

    return { sent: true, internal };
  },

  /**
   * Move the ticket without saying anything.
   *
   * Closing needs a date; `Case.clean()` has always said so and the serializer
   * now enforces it, so the button supplies today rather than bouncing the
   * user into a form to type a date they were never going to change. Where an
   * approval rule covers the ticket, the API refuses and says which rule.
   */
  setStatus: async ({ cookies, params, request }) => {
    const form = await request.formData();
    const status = form.get('status')?.toString().trim() ?? '';
    if (!status) return fail(400, { error: 'No status was chosen.' });

    /** @type {Record<string, any>} */
    const values = { status };
    if (status === 'Closed') values.closed_on = new Date().toISOString().slice(0, 10);

    try {
      await updateTicket({ cookies }, params.id, values);
    } catch (/** @type {any} */ err) {
      return fail(400, { error: readableError(err, 'Could not change the status.') });
    }

    return { moved: status };
  },

  /**
   * Close a parent ticket, and optionally its open descendants.
   *
   * A separate action from `setStatus` rather than a flag on it. `setStatus`
   * PATCHes the case; this posts to `close-with-children/`, which closes the
   * subtree in one transaction and writes a `PARENT_CLOSED_CASCADE` activity
   * row on each child. Folding the two together would mean a ticket with no
   * children took the heavier path for no reason, and the approval gate on the
   * ordinary close lives on the PATCH.
   *
   * `cascade` is read from the checkbox, so an unticked box sends `false` and
   * closes the parent alone. It is never omitted: the API reads the org
   * default only when the key is absent, which would let a setting decide
   * something the person confirming had just decided themselves.
   *
   * What is reported back is `cascaded_case_ids` from the response, not the
   * count that was on screen. Between rendering the page and pressing the
   * button somebody else may have closed those children, and claiming to have
   * closed three tickets that were already closed is a lie about a
   * destructive action.
   */
  closeWithChildren: async ({ cookies, params, request }) => {
    const form = await request.formData();
    const cascade = form.get('cascade') === 'on';
    const comment = form.get('resolution_comment')?.toString().trim() ?? '';

    let result;
    try {
      result = await closeTicketWithChildren({ cookies }, params.id, {
        cascade,
        resolution_comment: comment
      });
    } catch (/** @type {any} */ err) {
      return fail(400, { error: readableError(err, 'Could not close this ticket.') });
    }

    return {
      moved: 'Closed',
      closed: closeResultMessage({ cascade, cascaded: cascadedCount(result) })
    };
  }
};
