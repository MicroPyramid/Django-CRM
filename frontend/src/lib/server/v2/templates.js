/**
 * Invoice templates: the eighteenth v2 module and the highest-risk of the
 * invoices sub-pages. Server-only, like every v2 module: the access token is an
 * httpOnly cookie and the org is a JWT claim the backend reads, never a param.
 *
 * WHAT A TEMPLATE IS, AND WHY THIS PAGE IS CAREFUL
 * A template is org-wide shared config: how every invoice looks when it reaches
 * a customer. `template_html` / `template_css` are org-authored HTML/CSS that
 * WeasyPrint renders into a PDF on the SERVER. They must never reach this app's
 * DOM: the moment either lands in a `{@html}` a PDF setting becomes stored XSS.
 * The backend list/detail serializer now strips both fields (a `has_custom_html`
 * boolean and a byte count stand in for them), so, unlike the old mock, which
 * omitted the blobs at the client boundary. The markup never leaves the DB in
 * the first place. `toRow` whitelists fields anyway, as a second wall.
 *
 * THE FINDING THIS MODULE CARRIED
 * Both template endpoints were `(IsAuthenticated, HasOrgContext)` only: any
 * member could create, edit, delete, or re-point the org default, and could
 * write raw `template_html`/`template_css` that feeds the server-side PDF
 * render. That was fixed on the backend (admin-only writes + a `url_fetcher`
 * that stops the WeasyPrint SSRF/local-file-read); this page is the client that
 * draws the one write a worklist should own.
 *
 * THE ONE WRITE: SET DEFAULT
 * `is_default` is a singleton, the model clears it on every other row inside a
 * transaction, so making a template the default is a swap, not a toggle. That
 * is the action wired here. Creating or editing a template is a full builder
 * (colours, logo upload, and the raw markup), the same class of deferred
 * surface as the invoice builder (#48); it is not wired in this pass.
 *
 * TOTALS ARE COMPUTED HERE
 * The list endpoint has no `totals` envelope. `count` comes from the response;
 * `unused` (templates no invoice uses and that are not the default. Safe to
 * delete) is derived from the rows. `limit=1000`; an org has a handful of
 * templates, and that ceiling is called out where it is set.
 */
import { apiRequest } from '$lib/api-helpers.js';

const num = (/** @type {any} */ value) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
};

/**
 * A list row from `InvoiceTemplateListSerializer`. Whitelisted on purpose: the
 * raw `template_html`/`template_css` are not on the wire, and this makes sure
 * nothing downstream can start depending on them if that ever regresses.
 *
 * @param {any} row
 */
function toRow(row) {
  return {
    id: row.id,
    name: row.name || '(untitled template)',
    is_default: Boolean(row.is_default),
    primary_color: row.primary_color || '#000000',
    secondary_color: row.secondary_color || '#000000',
    has_logo: Boolean(row.has_logo),
    has_custom_html: Boolean(row.has_custom_html),
    custom_html_bytes: num(row.custom_html_bytes),
    default_notes: row.default_notes || '',
    default_terms: row.default_terms || '',
    footer_text: row.footer_text || '',
    used_on_invoices: num(row.used_on_invoices),
    updated_at: row.updated_at || null,
    updated_by: row.updated_by || '—'
  };
}

/**
 * The two header figures, derived from the visible rows.
 *
 * @param {any[]} rows
 * @param {number | undefined} count
 */
function computeTotals(rows, count) {
  let unused = 0;
  for (const t of rows) {
    if (!t.is_default && t.used_on_invoices === 0) unused += 1;
  }
  return { count: count ?? rows.length, unused };
}

/**
 * The template catalogue. Reading is open to any member (they see how their
 * invoices print); the writes below are the admin-gated part.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 */
export async function listInvoiceTemplates({ cookies }) {
  const query = new URLSearchParams();
  // One page covers every real org; the derived totals need the whole set.
  query.set('limit', '1000');

  const response = await apiRequest(`/invoices/templates/?${query.toString()}`, {}, { cookies });
  const rows = (response.results ?? []).map(toRow);

  return { templates: rows, totals: computeTotals(rows, response.count) };
}

/**
 * Make one template the org default. A partial update flipping `is_default`;
 * the model swaps the flag off whatever held it. The API admin-gates this.
 * This layer does not decide, it just asks, and a non-admin gets a 403.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {string} id
 */
export async function setDefaultTemplate({ cookies }, id) {
  return apiRequest(
    `/invoices/templates/${id}/`,
    { method: 'PUT', body: { is_default: true } },
    { cookies }
  );
}
