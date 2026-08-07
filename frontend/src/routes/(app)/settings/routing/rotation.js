/**
 * Who the next round-robin ticket goes to.
 *
 * Client-side display logic, in its own module rather than inline in
 * `+page.svelte`, because the harness cannot import a `.svelte` file and this
 * is a rule with a right answer that lives in `cases/routing.py`. The pipeline
 * route does the same with `board-fields.js`.
 *
 * Two things this got wrong while it was inline, both of which named the wrong
 * agent:
 *
 * `last_assigned_index` is the NEXT index despite its name. `_round_robin`
 * reads `pool[state.last_assigned_index % len(pool)]` and only then stores
 * `idx + 1`, so adding one here skipped a person. The engine's own dry-run
 * preview is `pool[(state.last_assigned_index if state else 0) % len(pool)]`,
 * missing state included, which is why a rule whose rotation has never run
 * reports the first agent rather than nothing.
 *
 * And the cursor indexes `_active_pool`, which is
 * `target_assignees.filter(is_active=True).order_by('id')`, not the
 * serializer's list. Indexing the unfiltered list could name a deactivated
 * profile as next, which is the one answer that is certainly wrong: the engine
 * will never pick them.
 *
 * `mobile/lib/data/models/routing_rule.dart` carries the same rule.
 */

/**
 * The people the engine actually rotates over: active only, ordered by id.
 *
 * A plain code-unit compare rather than `localeCompare`, which is
 * locale-dependent. This has to match a byte ordering exactly, and it does:
 * Postgres orders `uuid` by its bytes, and the canonical lowercase hex form
 * compares the same way lexically.
 *
 * @param {any} rule
 * @returns {any[]}
 */
export function rotationPool(rule) {
  return (rule?.target_assignees ?? [])
    .filter((/** @type {any} */ p) => p.is_active)
    .sort((/** @type {any} */ a, /** @type {any} */ b) =>
      String(a.id) < String(b.id) ? -1 : String(a.id) > String(b.id) ? 1 : 0
    );
}

/**
 * The agent the next matching ticket would go to, or null.
 *
 * Only knowable for round_robin, where RoutingRuleState holds the cursor. For
 * the other strategies it depends on the ticket or on live workload, and
 * guessing would be worse than silence.
 *
 * @param {any} rule
 * @returns {any | null}
 */
export function nextInRotation(rule) {
  if (rule?.strategy !== 'round_robin') return null;
  const pool = rotationPool(rule);
  if (!pool.length) return null;
  return pool[(rule.state?.last_assigned_index ?? 0) % pool.length];
}
