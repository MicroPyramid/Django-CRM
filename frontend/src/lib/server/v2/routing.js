/**
 * Ticket routing rules — the wiring behind `/settings/routing`.
 *
 * Server-only. Reads `GET /cases/routing-rules/`, ordered by priority (the
 * order IS the behaviour: the engine runs rules top-down and takes the first
 * match). Each rule carries its conditions, strategy, targets, and two things
 * the backend computes from the ROUTED activity log — `matched_last_30d` (how
 * often the rule fired) and the round-robin `state.last_assigned_index` (so the
 * page can name who is next). The response also carries org totals, including
 * `unrouted_last_30d` (cases no rule matched).
 *
 * Read-only page: "New rule" / drag-to-reorder are deferred builders, so there
 * is no write path to wire. The backend returns `target_assignees` as full
 * profile objects (name under `user_details.name`, plus `is_active`, which the
 * page flags on) and `target_team` as a full team object; the page wants
 * `{ id, name, is_active }` / `{ id, name }`, so flatten here.
 */
import { apiRequest } from '$lib/api-helpers.js';

/** Profile → the `{ id, name, is_active }` the rule card reads. */
function shapeAssignee(p) {
  return { id: p.id, name: p.user_details?.name ?? null, is_active: p.is_active };
}

/** Team → `{ id, name }`, or null. */
function shapeTeam(team) {
  if (!team) return null;
  return { id: team.id, name: team.name };
}

/**
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @returns {Promise<{ rules: any[], totals: any }>}
 */
export async function getRoutingRules({ cookies }) {
  const { rules, totals } = await apiRequest('/cases/routing-rules/', {}, { cookies });
  return {
    rules: (rules ?? []).map((r) => ({
      id: r.id,
      name: r.name,
      priority_order: r.priority_order,
      is_active: r.is_active,
      conditions: r.conditions ?? [],
      strategy: r.strategy,
      stop_processing: r.stop_processing,
      target_team: shapeTeam(r.target_team),
      target_assignees: (r.target_assignees ?? []).map(shapeAssignee),
      state: r.state ?? null,
      matched_last_30d: r.matched_last_30d ?? 0
    })),
    totals: totals ?? { count: 0, active: 0, unrouted_last_30d: 0 }
  };
}
