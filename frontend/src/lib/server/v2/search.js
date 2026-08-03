/**
 * Global search for the ⌘K palette, the wiring behind /api/search.
 *
 * Server-only. One org-scoped backend call, `GET /search/`, returns typed hits
 * across every module (the org comes from the JWT, never the client, and each
 * type is already filtered to what the caller may open). This layer only maps
 * the backend `type` to the palette's group label and the detail route to open.
 */
import { apiRequest } from '$lib/api-helpers.js';

/** Backend `type` → palette group label + detail route. */
const MAP = {
  lead: { kind: 'Leads', href: (/** @type {string} */ id) => `/leads/${id}` },
  deal: { kind: 'Deals', href: (/** @type {string} */ id) => `/pipeline/${id}` },
  account: { kind: 'Accounts', href: (/** @type {string} */ id) => `/accounts/${id}` },
  contact: { kind: 'Contacts', href: (/** @type {string} */ id) => `/contacts/${id}` },
  ticket: { kind: 'Tickets', href: (/** @type {string} */ id) => `/tickets/${id}` },
  invoice: { kind: 'Invoices', href: (/** @type {string} */ id) => `/invoices/${id}` },
  solution: {
    kind: 'Knowledge base',
    href: (/** @type {string} */ id) => `/solutions/${id}`
  }
};

/**
 * Org-scoped search, shaped for the palette (`{ kind, id, title, meta, href }`).
 * The two-character floor matches the backend's, so a one-character query never
 * makes a round trip.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} q
 * @returns {Promise<{ results: any[] }>}
 */
export async function search({ cookies }, q) {
  const query = (q || '').trim();
  if (query.length < 2) return { results: [] };

  const data = await apiRequest(`/search/?q=${encodeURIComponent(query)}`, {}, { cookies });

  const results = (data.results || [])
    .map(
      /** @param {any} r */ (r) => {
        const m = MAP[/** @type {keyof typeof MAP} */ (r.type)];
        if (!m) return null;
        return {
          kind: m.kind,
          id: r.id,
          title: r.title,
          meta: r.subtitle || '',
          href: m.href(r.id)
        };
      }
    )
    .filter(Boolean);

  return { results };
}
