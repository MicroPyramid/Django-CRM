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
 * THE ONE WRITE: SET DEFAULT, THEN A SECOND: CREATE
 * `is_default` is a singleton, the model clears it on every other row inside a
 * transaction, so making a template the default is a swap, not a toggle.
 * Creating a template is the second write, `createInvoiceTemplate` below.
 * Editing one stays out of scope: the detail GET uses the same stripping
 * serializer as the list, so an edit form could never pre-fill the raw markup,
 * and that gap is left as an honest, disabled control rather than a silent
 * dead button (see the list page). `template_html` / `template_css` are also
 * left out of the create form on purpose, for the same reason: see
 * `CREATE_FIELDS` below.
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

const HEX_COLOR = /^#[0-9a-fA-F]{6}$/;

/**
 * Every field this form is allowed to write.
 *
 * `template_html` and `template_css` are deliberately absent even though
 * `InvoiceTemplateCreateSerializer` accepts them. Every read serializer strips
 * them on purpose and substitutes `has_custom_html` / `has_custom_css` /
 * `custom_html_bytes`, and the detail GET uses that same stripping serializer,
 * so a value written here could never be read back or edited afterwards. It
 * also feeds the WeasyPrint PDF renderer. A write-once, never-readable markup
 * field is a trap, so this form does not offer one. Never render either value
 * with `{@html}`.
 */
export const CREATE_FIELDS = [
  'name',
  'primary_color',
  'secondary_color',
  'default_notes',
  'default_terms',
  'footer_text',
  'is_default'
];

/**
 * Create an invoice template.
 *
 * Admin-only server-side: `_forbid_non_admin_template_write` 403s anyone whose
 * `profile.role` is not ADMIN and who is not a superuser. The page hides the
 * control using `can_manage`, but that is a display hint decoded from the JWT;
 * the backend re-derives the role and is the check that matters.
 *
 * The colour checks below mirror nothing on the server. Neither colour field
 * has a format validator; the model is `max_length=7` only, so `"purple"` is
 * stored happily and then renders as an invalid CSS colour in the PDF. That is
 * a backend gap, flagged rather than worked around.
 *
 * `is_default` is not a plain field write: the model's `save()` clears the flag
 * on every other template in the org inside a transaction, so setting it here
 * demotes whichever template is currently default.
 *
 * When a logo is supplied the body must be multipart, because `logo` is an
 * ImageField. `apiRequest` already detects a `FormData` body and leaves
 * `Content-Type` unset so the browser adds the boundary.
 *
 * `InvoiceTemplateListView.post` (`backend/invoices/api_views.py`) wraps its
 * result in an envelope, `{ error, message, template }`, exactly the trap
 * `createTag` documents in `tags.js`: a `create*` function that resolves to
 * the envelope instead of the record is the one the next caller reaches for
 * `.id` on and gets `undefined`. This unwraps to `.template` deliberately,
 * with the same `?? resp` fallback as `createTag`, so a change in the
 * backend's response shape degrades to the raw envelope rather than throwing.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {Record<string, any>} values
 * @param {File | null} [logoFile]
 * @returns {Promise<any>}
 */
export async function createInvoiceTemplate({ cookies }, values, logoFile = null) {
  const name = (values.name ?? '').toString().trim();
  if (!name) throw new Error('Give the template a name.');

  for (const key of ['primary_color', 'secondary_color']) {
    const colour = values[key];
    if (colour !== undefined && colour !== '' && !HEX_COLOR.test(String(colour))) {
      throw new Error('Colours must be a six digit hex value, for example #3B82F6.');
    }
  }

  /** @type {Record<string, any>} */
  const fields = {};
  for (const key of CREATE_FIELDS) {
    if (values[key] === undefined) continue;
    // An empty colour is omitted rather than sent as `''`. The model has no
    // `blank=True` on either colour, so DRF would answer a literal empty string
    // with "This field may not be blank", while omitting the key lets the model
    // default apply. Only reachable if `input type="color"` degrades to a text
    // field, but the failure would be a raw 400 with no useful message.
    if ((key === 'primary_color' || key === 'secondary_color') && values[key] === '') continue;
    fields[key] = key === 'name' ? name : values[key];
  }

  if (logoFile) {
    const body = new FormData();
    for (const [key, value] of Object.entries(fields)) {
      body.append(key, typeof value === 'boolean' ? String(value) : value);
    }
    body.append('logo', logoFile);
    const resp = await apiRequest('/invoices/templates/', { method: 'POST', body }, { cookies });
    return resp.template ?? resp;
  }

  const resp = await apiRequest(
    '/invoices/templates/',
    { method: 'POST', body: fields },
    { cookies }
  );
  return resp.template ?? resp;
}
