/**
 * Inbound mailboxes — the wiring behind `/settings/inbound-email`.
 *
 * Server-only. Reads `GET /cases/mailboxes/`, the addresses that turn email
 * into tickets. Each row carries its defaults (priority, case type, assignee)
 * plus two backend-computed metrics — `cases_last_30d` (tickets opened from the
 * address in 30 days) and `last_received_at` (newest mail seen), both attributed
 * exactly via the `EmailMessage.mailbox` FK. Totals carry `count`, `active`, and
 * the org's `cases_last_30d`.
 *
 * NO SECRETS. `webhook_secret` is the credential that proves a delivery really
 * came from the provider — anything holding it can forge tickets into this org.
 * The backend already strips it for non-admins, but this layer drops it for
 * everyone: it is never needed to render the page, so it never reaches the
 * browser, admin or not. Rotation is an explicit action elsewhere, not a field
 * on a page you can browse to.
 *
 * Read-only page: "Add address" / "Edit" are deferred builders, so there is no
 * write path here. The backend returns `default_assignee` as a full profile
 * object (name under `user_details.name`); the page wants `{ id, name }`.
 */
import { apiRequest } from '$lib/api-helpers.js';

/** Profile → the `{ id, name }` the card reads, or null. */
function shapeAssignee(p) {
  if (!p) return null;
  return { id: p.id, name: p.user_details?.name ?? null };
}

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ mailboxes: any[], totals: any }>}
 */
export async function getMailboxes({ cookies }) {
  const { mailboxes, totals } = await apiRequest('/cases/mailboxes/', {}, { cookies });
  return {
    // Rebuild each row from a fixed allowlist of fields — webhook_secret and the
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
      last_received_at: m.last_received_at ?? null
    })),
    totals: totals ?? { count: 0, active: 0, cases_last_30d: 0 }
  };
}
