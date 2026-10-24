/**
 * Inbound mailboxes: the wiring behind `/settings/inbound-email`.
 *
 * Server-only. Reads `GET /cases/mailboxes/`, the addresses that turn email
 * into tickets or, with `creates: 'leads'`, into leads. Each row carries its defaults (priority, case type, assignee)
 * plus two backend-computed metrics, `cases_last_30d` (tickets opened from the
 * address in 30 days) and `last_received_at` (newest mail seen), both attributed
 * exactly via the `EmailMessage.mailbox` FK. Totals carry `count`, `active`, and
 * the org's `cases_last_30d`.
 *
 * NO SECRET COMES BACK. `webhook_secret` (Postmark's basic-auth password or
 * Mailgun's signing key) is write-only server-side. This layer never reads it
 * and sends it only when an admin typed one; `has_webhook_secret`, the boolean,
 * is all a row carries.
 *
 * `topic_arn` is not a secret, but it embeds the AWS account id, so the backend
 * returns it to admins only. It is the mailbox's SNS topic pin: the webhook
 * refuses every message whose TopicArn is not exactly this one, and a mailbox
 * with none accepts nothing until an admin enters it here or a confirmation
 * arrives from an AWS account the server allows (`INBOUND_SNS_ACCOUNT_IDS`).
 * So an admin reads, sets, changes and clears it on this page; a member gets
 * only `has_topic_arn`.
 *
 * Create, edit, turn off, turn on and delete are wired below. The backend
 * returns `default_assignee` as a full profile object (name under
 * `user_details.name`); the page wants `{ id, name }`.
 */
import { apiRequest } from '#lib/api-helpers.js';
import { viewerIsAdmin } from './organization.js';

/** Profile → the `{ id, name }` the card reads, or null. */
function shapeAssignee(p) {
  if (!p) return null;
  return { id: p.id, name: p.user_details?.name ?? null };
}

/**
 * Whether a mailbox's address was minted under the server's inbound domain.
 * Read from `is_generated` when the row carries it, else from the address.
 *
 * @param {any} m @param {string | null} domain
 */
function isGenerated(m, domain) {
  if (typeof m.is_generated === 'boolean') return m.is_generated;
  return Boolean(domain) && String(m.address ?? '').endsWith(`@${domain}`);
}

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ mailboxes: any[], totals: any, can_edit: boolean, generated_domain: string | null, can_create_leads: boolean }>}
 */
export async function getMailboxes({ cookies }) {
  const resp = await apiRequest('/cases/mailboxes/', {}, { cookies });
  const { mailboxes, totals } = resp;
  const domain = typeof resp?.generated_domain === 'string' ? resp.generated_domain : null;
  return {
    // Rebuild each row from a fixed allowlist of fields; webhook_secret and the
    // imap_* columns are deliberately not among them, so a secret can never ride
    // along into the page even if the serializer starts returning one.
    mailboxes: (mailboxes ?? []).map((m) => ({
      id: m.id,
      address: m.address,
      provider: m.provider,
      is_active: m.is_active,
      default_priority: m.default_priority,
      default_case_type: m.default_case_type,
      default_assignee: shapeAssignee(m.default_assignee),
      cases_last_30d: m.cases_last_30d ?? 0,
      last_received_at: m.last_received_at ?? null,
      // Whether the mailbox has its SNS TopicArn pin, not the ARN itself. An
      // active SES address with no pin rejects every notification, so without
      // this the page can only read `is_active` and draws a never-connected
      // address as one creating tickets. See `./delivery.js`. Defaults to
      // false, which reads as "not connected yet": failing closed is the safe
      // direction for a status this page draws a green pill from.
      has_topic_arn: m.has_topic_arn === true,
      // The ARN itself, which the backend sends to admins only. Null for a
      // member, whose page has no form to put it in.
      topic_arn: typeof m.topic_arn === 'string' ? m.topic_arn : null,
      // Whether a Postmark or Mailgun secret is stored, not the secret. Sent
      // to admins only; absent reads as false, which fails closed.
      has_webhook_secret: m.has_webhook_secret === true,
      creates: m.creates === 'leads' ? 'leads' : 'tickets',
      lead_source: m.lead_source ?? '',
      lead_source_detail: m.lead_source_detail ?? '',
      is_generated: isGenerated(m, domain)
    })),
    totals: totals ?? { count: 0, active: 0, cases_last_30d: 0 },
    // Set when the server mints addresses under its own inbound domain.
    generated_domain: domain,
    // An API that can make lead addresses says so with these fields; an older
    // one has neither, and the form then offers tickets only.
    can_create_leads:
      Object.hasOwn(resp ?? {}, 'generated_domain') ||
      (mailboxes ?? []).some((/** @type {any} */ m) => Object.hasOwn(m, 'creates')),
    // A display hint: POST/PUT/DELETE on `/cases/mailboxes/` each start with
    // `_is_admin(request.profile)` server-side and 403 regardless of what this
    // says. This only decides whether the page offers the controls. GET itself
    // is not role-gated, so a member can still see this list.
    can_edit: viewerIsAdmin(cookies)
  };
}

/** `webhook_secret` is write-only and is sent only when the admin typed one
 *  (`webhookSecretEdit`): an empty field would blank the stored column, and
 *  the form is never prefilled with it.
 *
 *  `topic_arn` is here, and an empty string is how an admin clears it. The
 *  form only hands one over when the admin changed it (`topicArnEdit`), so
 *  saving an edit opened before the webhook pinned the mailbox leaves the new
 *  pin alone rather than blanking it. */
const UPDATE_FIELDS = [
  'address',
  'provider',
  'default_priority',
  'default_case_type',
  'default_assignee_id',
  'is_active',
  'topic_arn',
  'webhook_secret',
  'creates',
  'lead_source',
  'lead_source_detail'
];

/** `address` is the mailbox's identity and its uniqueness key. It is not
 *  frozen by the backend (`validate_address` only checks duplicates on
 *  create, and `put` is partial), so an edit may change it. It stays in the
 *  update allow-list for that reason, with a hint on the form saying mail to
 *  the old address stops becoming tickets.
 *
 *  `generate_address` asks the server to mint the address, so it is a create
 *  field only. */
const CREATE_FIELDS = [...UPDATE_FIELDS, 'generate_address'];

/** @param {string[]} allowed @param {{ [key: string]: any }} values */
function buildBody(allowed, values) {
  /** @type {Record<string, any>} */
  const body = {};
  for (const field of allowed) {
    if (values[field] === undefined) continue;
    body[field] = values[field];
  }
  // Two nullable fields whose "none selected" option is an empty `<option>`
  // value. `''` fails the ChoiceField and the PK lookup alike; `null` is what
  // clears them, and both are `allow_null=True` on the serializer.
  for (const nullable of ['default_case_type', 'default_assignee_id']) {
    if (body[nullable] === '') body[nullable] = null;
  }
  if (body.is_active !== undefined) body.is_active = Boolean(body.is_active);
  if (body.address !== undefined) {
    body.address = String(body.address).trim().toLowerCase();
  }
  if (body.topic_arn !== undefined) body.topic_arn = String(body.topic_arn ?? '').trim();
  if (body.webhook_secret !== undefined) {
    const secret = String(body.webhook_secret ?? '').trim();
    if (secret) body.webhook_secret = secret;
    else delete body.webhook_secret;
  }
  if (body.creates !== undefined) body.creates = body.creates === 'leads' ? 'leads' : 'tickets';
  for (const key of ['lead_source', 'lead_source_detail']) {
    if (body[key] !== undefined) body[key] = String(body[key] ?? '').trim();
  }
  if (body.generate_address !== undefined) {
    if (body.generate_address === true) {
      // The server picks the address and routes it through its own catch-all,
      // so nothing typed for the address or its SNS pin goes with it.
      delete body.address;
      delete body.topic_arn;
      delete body.webhook_secret;
      body.provider = 'ses';
    } else delete body.generate_address;
  }
  return body;
}

/**
 * The `topic_arn` a form save should send, or undefined to leave it alone.
 *
 * Only a change is sent. The form is prefilled with the ARN as it stood when
 * the page loaded, and the webhook can pin a mailbox after that (a
 * confirmation from an allowed AWS account), so resending the stale value, or
 * the empty one, would silently undo a pin nobody on this page chose to undo.
 * Clearing the field on purpose is a change, and sends `''`.
 *
 * @param {FormDataEntryValue | null | undefined} submitted the field's value
 * @param {FormDataEntryValue | null | undefined} loaded what it was prefilled with
 * @returns {string | undefined}
 */
export function topicArnEdit(submitted, loaded) {
  if (submitted == null) return undefined;
  const next = String(submitted).trim();
  return next === String(loaded ?? '').trim() ? undefined : next;
}

/**
 * The `webhook_secret` a form save should send, or undefined to leave the
 * stored one alone. Only what the admin typed goes; blank is not a request to
 * clear it.
 *
 * @param {FormDataEntryValue | null | undefined} submitted
 * @returns {string | undefined}
 */
export function webhookSecretEdit(submitted) {
  if (submitted == null) return undefined;
  const next = String(submitted).trim();
  return next || undefined;
}

/** @param {{ cookies: import('@sveltejs/kit').Cookies }} event */
export async function createMailbox({ cookies }, values) {
  const body = buildBody(CREATE_FIELDS, values);
  if (!body.address && !body.generate_address) throw new Error('A mailbox needs an address.');
  return await apiRequest('/cases/mailboxes/', { method: 'POST', body }, { cookies });
}

/** @param {{ cookies: import('@sveltejs/kit').Cookies }} event */
export async function updateMailbox({ cookies }, id, values) {
  if (!id) throw new Error('Which mailbox? No mailbox id was given.');
  const body = buildBody(UPDATE_FIELDS, values);
  return await apiRequest(`/cases/mailboxes/${id}/`, { method: 'PUT', body }, { cookies });
}

/**
 * Delete a mailbox, permanently.
 *
 * `InboundMailboxDetailView.delete` calls `obj.delete()`. Hard delete, and it
 * takes the row's topic pin and its webhook lookup with it, so mail already in
 * flight from AWS is refused the moment this runs.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 */
export async function deleteMailbox({ cookies }, id) {
  if (!id) throw new Error('Which mailbox? No mailbox id was given.');
  return await apiRequest(`/cases/mailboxes/${id}/`, { method: 'DELETE' }, { cookies });
}
