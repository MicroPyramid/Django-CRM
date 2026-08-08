/**
 * The data layer behind `/help`.
 *
 * The page a user opens is `/help`; the API it wraps is `/api/support/`, which
 * is why this module and its exports keep the support name. Anything that
 * names a destination a person can see says help, anything that names the
 * enterprise `platform_support` API says support.
 */
import { error } from '@sveltejs/kit';

import { apiRequest } from '$lib/api-helpers.js';

export const SUPPORT_CATEGORIES = [
  { value: 'technical', label: 'Technical issue' },
  { value: 'billing', label: 'Billing' },
  { value: 'account', label: 'Account access' },
  { value: 'feature_request', label: 'Feature request' },
  { value: 'other', label: 'Other' }
];

/** @param {any} message @param {string} ticketId */
function toMessage(message, ticketId) {
  return {
    id: message.id,
    author: message.author_label,
    authorType: message.author_type,
    body: message.body ?? '',
    attachmentName: message.attachment_name || null,
    attachmentUrl: message.attachment_download_url
      ? `/help/${ticketId}/attachments/${message.id}`
      : null,
    createdAt: message.created_at
  };
}

/** @param {any} ticket */
function toTicket(ticket) {
  return {
    id: ticket.id,
    reference: ticket.reference,
    subject: ticket.subject,
    category: ticket.category,
    categoryLabel: ticket.category_label,
    status: ticket.status,
    statusLabel: ticket.status_label,
    priority: ticket.priority,
    priorityLabel: ticket.priority_label,
    assigned: Boolean(ticket.assigned),
    messageCount: ticket.message_count ?? ticket.messages?.length ?? 0,
    firstResponseAt: ticket.first_response_at ?? null,
    lastActivityAt: ticket.last_activity_at,
    createdAt: ticket.created_at,
    messages: (ticket.messages ?? []).map((message) => toMessage(message, ticket.id))
  };
}

/** @param {{ cookies: import('@sveltejs/kit').Cookies }} event */
export async function listSupportTickets({ cookies }) {
  const response = await apiRequest('/support/?limit=100', {}, { cookies });
  return {
    count: response.count ?? response.tickets?.length ?? 0,
    tickets: (response.tickets ?? []).map(toTicket)
  };
}

/**
 * Everything `/help` renders, and which of its two tiers to render.
 *
 * The self-serve half of that page is community code. The ticket queue behind
 * it is not: `/api/support/` is served by the enterprise `platform_support`
 * app, so a community deployment answers 404. A 404 therefore means "this
 * deployment has no support queue", not "something broke", and the page falls
 * back to the routes that do work. Anything else is rethrown, because an org
 * that does have support must see a real outage as an outage rather than be
 * quietly downgraded to the community page while their tickets sit unread.
 *
 * Lives here rather than in `+page.server.js` so the vitest harness can reach
 * it. That harness resolves `$lib` and nothing else, and its include glob
 * cannot match a path containing `(app)` anyway, so a test placed next to the
 * route would never run. See the docstring in `vitest.config.js`.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 */
export async function loadHelpPage({ cookies }) {
  try {
    return { available: true, ...(await listSupportTickets({ cookies })) };
  } catch (/** @type {any} */ err) {
    if (err?.status !== 404) throw err;
    return { available: false, count: 0, tickets: [] };
  }
}

/** @param {{ cookies: import('@sveltejs/kit').Cookies }} event @param {string} id */
export async function getSupportTicket({ cookies }, id) {
  if (!id) throw new Error('A support ticket id is required.');
  try {
    return toTicket(await apiRequest(`/support/${encodeURIComponent(id)}/`, {}, { cookies }));
  } catch (/** @type {any} */ err) {
    // On the status, not the wording. The API answers a ticket belonging to
    // somebody else with the same 404 as one that does not exist, which is
    // deliberate: a 403 here would confirm the id is real. Without this the
    // page answered 500, which every other v2 detail page already avoids.
    if (err?.status === 404) {
      error(404, 'That request does not exist, or somebody else opened it.');
    }
    throw err;
  }
}

/**
 * Create a ticket from a form while allow-listing every field. Organization,
 * requester, status, priority and assignee are deliberately impossible to
 * forward from this client, and the API rejects them too.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {{ subject: string, category: string, body: string, attachment?: File | null }} values
 */
export async function createSupportTicket({ cookies }, values) {
  const body = new FormData();
  body.set('subject', values.subject.trim());
  body.set('category', values.category);
  body.set('body', values.body.trim());
  if (values.attachment?.size) body.set('attachment', values.attachment);
  return toTicket(await apiRequest('/support/', { method: 'POST', body }, { cookies }));
}

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} id
 * @param {{ body: string, attachment?: File | null }} values
 */
export async function replyToSupportTicket({ cookies }, id, values) {
  if (!id) throw new Error('A support ticket id is required.');
  const body = new FormData();
  body.set('body', values.body.trim());
  if (values.attachment?.size) body.set('attachment', values.attachment);
  return toTicket(
    await apiRequest(
      `/support/${encodeURIComponent(id)}/replies/`,
      { method: 'POST', body },
      { cookies }
    )
  );
}
