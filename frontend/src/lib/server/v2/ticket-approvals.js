/**
 * Approval rules — the wiring behind `/settings/ticket-approvals`.
 *
 * Server-only. Reads `GET /cases/approval-rules/`, the rules that gate a ticket
 * close and who can clear them. Each rule carries its match conditions, the
 * approver role / named approvers, and a backend-computed `pending_count` (the
 * Approval rows in state "pending" bound to it). Totals carry `count`, `active`,
 * and `pending` (the org's total waiting approvals).
 *
 * Read-only page: "New rule" is a deferred builder, so there is no write path.
 * The backend returns `approvers` as `[{ id, email }]`; the page renders them as
 * a sentence (`approvers.join(' or ')`), so flatten to the email strings here.
 * `match_team` already arrives as `{ id, name }` or null.
 */
import { apiRequest } from '$lib/api-helpers.js';

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ rules: any[], totals: any }>}
 */
export async function getApprovalRules({ cookies }) {
  const { rules, totals } = await apiRequest('/cases/approval-rules/', {}, { cookies });
  return {
    rules: (rules ?? []).map((r) => ({
      id: r.id,
      name: r.name,
      is_active: r.is_active,
      approver_role: r.approver_role,
      approvers: (r.approvers ?? []).map((a) => a.email).filter(Boolean),
      match_priority: r.match_priority,
      match_case_type: r.match_case_type,
      match_team: r.match_team ?? null,
      pending_count: r.pending_count ?? 0
    })),
    totals: totals ?? { count: 0, active: 0, pending: 0 }
  };
}
