/**
 * Which approval rule gates a close, and who can clear it.
 *
 * Two things the list reads as, and are not:
 *
 * 1. **The rules are not cumulative.** `find_matching_rule` collects every
 *    active rule matching the case, sorts by specificity (how many of
 *    priority / type / team are set), and returns exactly one. So a broad rule
 *    and a narrow rule are not two gates on the same ticket, they are one gate
 *    and a fallback. Among rules whose conditions are identical the sort is
 *    stable over `-created_at`, so the newest wins and the older ones can
 *    never run at all. That last case is exact and is what [shadowedRuleIds]
 *    reports; a partial overlap between different conditions is a real
 *    fallback rather than a dead rule, so nothing here guesses at those.
 *
 * 2. **Named approvers do not narrow a rule, they widen it.** The form has
 *    always said so and the row said the opposite: `Approval
 *    .can_be_acted_on_by` returns True for a named approver OR for anyone
 *    holding `approver_role`, so naming two people on an admin rule leaves
 *    every admin able to clear it. The row used to list only the two names.
 *
 * Nothing here is a security control. `ApprovalApproveView` decides who may
 * act, and separately refuses an approval whose requester is its approver.
 *
 * `mobile/lib/data/models/approval_rule.dart` carries the same rules.
 */

/**
 * The `approver_role` values that any profile can actually hold.
 *
 * `APPROVER_ROLE_CHOICES` offers ADMIN and MANAGER; `Profile.role` is only
 * ADMIN or USER. MANAGER is reserved for a role model that does not exist yet,
 * so today it matches nobody, which is why a MANAGER rule with no named
 * approvers gates tickets that no one can close.
 */
export const ROLES_THAT_EXIST = ['ADMIN'];

/** @param {any} rule */
export function roleClears(rule) {
  return ROLES_THAT_EXIST.includes(rule?.approver_role);
}

/** The named approvers' emails, blanks dropped. @param {any} rule */
function namedApprovers(rule) {
  return (rule?.approvers ?? []).map((a) => a?.email).filter(Boolean);
}

/**
 * Everyone who can clear this rule, as the sentence a person would say.
 *
 * @param {any} rule
 */
export function approverSentence(rule) {
  const named = namedApprovers(rule);
  if (roleClears(rule)) {
    return named.length ? `any admin, or ${named.join(' or ')}` : 'any admin';
  }
  return named.length ? named.join(' or ') : 'nobody';
}

/**
 * True when this rule gates closes that no one in the org can clear.
 *
 * Only meaningful for an active rule: an inactive one gates nothing, so it
 * cannot strand anything.
 *
 * @param {any} rule
 */
export function clearableByNobody(rule) {
  return Boolean(rule?.is_active) && !roleClears(rule) && namedApprovers(rule).length === 0;
}

/**
 * What the rule matches, as the sentence a person would say.
 *
 * @param {any} rule
 */
export function ruleMatchSentence(rule) {
  const parts = [
    rule?.match_priority ? `${rule.match_priority} priority` : null,
    rule?.match_case_type ? rule.match_case_type.toLowerCase() : null,
    rule?.match_team ? `${rule.match_team.name} team` : null
  ].filter(Boolean);
  return parts.length ? parts.join(' · ') : 'Every ticket';
}

/**
 * How many filters a rule sets. Mirrors `ApprovalRule.specificity`, which is
 * the sort key that decides which of several matching rules runs.
 *
 * @param {any} rule
 */
export function ruleSpecificity(rule) {
  return [rule?.match_priority, rule?.match_case_type, rule?.match_team?.id].filter(Boolean).length;
}

/**
 * A key identical for two rules that match exactly the same tickets.
 *
 * `trigger_event` is deliberately not in it: `pre_close` is the only value the
 * backend accepts, so including a constant would only look like a comparison.
 *
 * @param {any} rule
 */
export function ruleSignature(rule) {
  return [rule?.match_priority ?? '', rule?.match_case_type ?? '', rule?.match_team?.id ?? ''].join(
    '|'
  );
}

/**
 * The active rules that can never be the one that runs.
 *
 * A rule is here when another ACTIVE rule matches exactly the same tickets and
 * was created later: same conditions means both always match together, and the
 * stable sort hands the newest one the case every time.
 *
 * Inactive rules are neither reported nor counted as shadowers. One gates
 * nothing, so it cannot be beaten, and it cannot beat anything either.
 *
 * @param {any[]} rules
 * @returns {Set<string>}
 */
export function shadowedRuleIds(rules) {
  const active = (rules ?? []).filter((r) => r?.is_active);
  /** @type {Set<string>} */
  const shadowed = new Set();
  for (const rule of active) {
    const signature = ruleSignature(rule);
    const beatenBy = active.some(
      (other) =>
        other.id !== rule.id &&
        ruleSignature(other) === signature &&
        isNewer(other.created_at, rule.created_at)
    );
    if (beatenBy) shadowed.add(rule.id);
  }
  return shadowed;
}

/**
 * The rule that actually runs for a shadowed rule's tickets.
 *
 * @param {any} rule
 * @param {any[]} rules
 */
export function shadowedBy(rule, rules) {
  const signature = ruleSignature(rule);
  const winners = (rules ?? [])
    .filter(
      (other) =>
        other?.is_active &&
        other.id !== rule?.id &&
        ruleSignature(other) === signature &&
        isNewer(other.created_at, rule?.created_at)
    )
    .sort((a, b) => (isNewer(a.created_at, b.created_at) ? -1 : 1));
  return winners[0] ?? null;
}

/**
 * Whether `a` was created after `b`. A missing or unparseable timestamp is
 * treated as older, so a row the API did not date never claims to beat one it
 * did, and a rule is never flagged dead on the strength of a blank.
 *
 * @param {string | null | undefined} a
 * @param {string | null | undefined} b
 */
function isNewer(a, b) {
  const left = Date.parse(a ?? '');
  const right = Date.parse(b ?? '');
  if (Number.isNaN(left) || Number.isNaN(right)) return false;
  return left > right;
}
