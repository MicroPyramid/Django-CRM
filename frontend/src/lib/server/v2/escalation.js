/**
 * Escalation policies — the wiring behind `/settings/escalation`.
 *
 * Server-only. Reads `GET /cases/escalation-policies/`, at most one row per
 * priority. Each row carries the policy's two halves (first_response /
 * resolution action + target), the team to notify, and — the reason the page
 * exists — `breaches_last_30d`, a server-side count of SLA breaches per
 * priority over the last 30 days. That count is condition-based, not sourced
 * from the escalation event log, so it still surfaces breaches under a dead
 * policy (off, or reassigning to nobody), which is the page's whole point.
 *
 * Read-only page: "Edit policy" is a deferred builder, so there is no write
 * path to wire here. The backend returns targets as full profile objects
 * (`user_details.name`) and the team as a full team object; the page only wants
 * `{ id, name }`, so flatten to that here rather than teach the component the
 * backend's nesting.
 */
import { apiRequest } from '$lib/api-helpers.js';

/** Profile → the `{ id, name }` the card renders, or null when unset. */
function shapeTarget(target) {
  if (!target) return null;
  return { id: target.id, name: target.user_details?.name ?? null };
}

/** Team → `{ id, name }`, or null. */
function shapeTeam(team) {
  if (!team) return null;
  return { id: team.id, name: team.name };
}

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ policies: any[] }>}
 */
export async function getEscalationPolicies({ cookies }) {
  const { policies } = await apiRequest('/cases/escalation-policies/', {}, { cookies });
  return {
    policies: (policies ?? []).map((p) => ({
      id: p.id,
      priority: p.priority,
      is_active: p.is_active,
      first_response_action: p.first_response_action,
      resolution_action: p.resolution_action,
      first_response_target: shapeTarget(p.first_response_target),
      resolution_target: shapeTarget(p.resolution_target),
      notify_team: shapeTeam(p.notify_team),
      breaches_last_30d: p.breaches_last_30d ?? { first_response: 0, resolution: 0 }
    }))
  };
}
