/**
 * What one half of an escalation policy actually does when a ticket breaches.
 *
 * Client-side display logic, in its own module rather than inline in
 * `+page.svelte`, because the harness cannot import a `.svelte` file and this
 * is a rule with a right answer that lives in `cases/tasks.py`. The routing
 * route does the same with `rotation.js`.
 *
 * This got the answer wrong in three of the eight action/target/team
 * combinations while it was inline, always in the same direction: reporting a
 * half as live when the engine does nothing with it.
 *
 * **A half with no target does nothing, whatever its action and whatever the
 * notify team.** `_scan_org` guards both dispatches with
 * `if <breach> and policy.<half>_target_id is not None`, so with the target
 * null `_dispatch_breach` is never reached: no mail, no reassignment, and no
 * ESCALATED activity. The team is a CC assembled *inside* that dispatch, not a
 * recipient that can stand on its own, so a policy set to "notify the Support
 * team" with nobody in the target field notifies nobody at all. The old rule
 * treated a team as enough for `notify`, and did not check the target for
 * `notify_and_reassign` at all (which also rendered "Notify and reassign to"
 * with nothing after it).
 *
 * **And a `reassign` half never notifies the team.** `_dispatch_breach` builds
 * a recipient list only for `notify` and `notify_and_reassign`. The old rule
 * appended "and the X team" to every action, so a policy that silently moves a
 * ticket read as one that also tells a team about it.
 *
 * `mobile/lib/data/models/escalation_policy.dart` carries the same rules.
 */
import { ESCALATION_ACTION_LABEL, ESCALATION_PRIORITIES } from '$lib/v2/enums.js';

/**
 * "the Support team", but "the Support Team" when the name already says so.
 *
 * Seeded orgs name their team "Support Team", and appending the word
 * unconditionally reads "the Support Team team". The suffix is what makes a
 * team named "Support" read as a team rather than a person, so it stays for
 * every other name.
 *
 * @param {string} name
 */
export function teamPhrase(name) {
  const trimmed = (name ?? '').trim();
  const lower = trimmed.toLowerCase();
  const saysSo =
    lower === 'team' || lower === 'teams' || lower.endsWith(' team') || lower.endsWith(' teams');
  return saysSo ? `the ${trimmed}` : `the ${trimmed} team`;
}

/** Whether an action emails anybody at all. @param {string} action */
export function actionNotifies(action) {
  return action === 'notify' || action === 'notify_and_reassign';
}

/**
 * Whether this half fires. See the note above: an inactive policy is skipped
 * whole, and a half with no target is skipped whatever else is set.
 *
 * @param {any} policy
 * @param {'first_response' | 'resolution'} kind
 */
export function halfFires(policy, kind) {
  return Boolean(policy?.is_active) && Boolean(policy?.[`${kind}_target`]);
}

/**
 * What this half does, in a sentence, including when that is nothing.
 *
 * @param {any} policy
 * @param {'first_response' | 'resolution'} kind
 * @returns {{ text: string, dead: boolean }}
 */
export function escalationOutcome(policy, kind) {
  if (!policy?.is_active) return { text: 'Nothing. The policy is turned off', dead: true };

  const target = policy[`${kind}_target`];
  const team = policy.notify_team;

  if (!target) {
    // Naming the team here is the correction, not decoration. A team set with
    // no target reads as "somebody is told" and is the case where nobody is.
    return {
      text: team
        ? `Nothing. No target is set, and ${teamPhrase(team.name)} is not notified on its own`
        : 'Nothing. No target is set',
      dead: true
    };
  }

  const action = policy[`${kind}_action`];
  const label = ESCALATION_ACTION_LABEL[action] ?? action;
  const who =
    team && actionNotifies(action) ? `${target.name} and ${teamPhrase(team.name)}` : target.name;
  return { text: `${label} ${who}`, dead: false };
}

/**
 * A team configured on a half that will never notify it, or null.
 *
 * Only for a half that fires: when it does not, the outcome sentence has
 * already said the team is not involved and repeating it would be noise.
 *
 * @param {any} policy
 * @param {'first_response' | 'resolution'} kind
 * @returns {string | null}
 */
export function teamIgnoredNote(policy, kind) {
  const team = policy?.notify_team;
  if (!team || !halfFires(policy, kind)) return null;
  if (actionNotifies(policy[`${kind}_action`])) return null;
  const phrase = teamPhrase(team.name);
  return `${phrase[0].toUpperCase()}${phrase.slice(1)} is not notified here: this half only reassigns.`;
}

/** @type {('first_response' | 'resolution')[]} */
export const ESCALATION_HALVES = ['first_response', 'resolution'];

/** Policies that do nothing on either half. @param {any[]} policies */
export function deadPolicyCount(policies) {
  return (policies ?? []).filter((p) => ESCALATION_HALVES.every((kind) => !halfFires(p, kind)))
    .length;
}

/**
 * Breaches in the last 30 days that reached nobody, counting only the halves
 * that cannot fire.
 *
 * @param {any[]} policies
 */
export function breachesGoingNowhere(policies) {
  return (policies ?? []).reduce(
    (total, policy) =>
      total +
      ESCALATION_HALVES.reduce(
        (sum, kind) =>
          sum + (halfFires(policy, kind) ? 0 : (policy.breaches_last_30d?.[kind] ?? 0)),
        0
      ),
    0
  );
}

/**
 * Priorities with no policy at all.
 *
 * Two things read this. "New policy" may only offer these, because the
 * `(org, priority)` unique constraint (and `EscalationPolicySerializer
 * .validate`) refuses a second policy for a priority. And the page says out
 * loud that breaches at these priorities escalate to nobody, which is otherwise
 * invisible: the API attaches `breaches_last_30d` to policies, so an
 * unconfigured priority contributes no row and no number anywhere.
 *
 * @param {any[]} policies
 */
export function unconfiguredPriorities(policies) {
  const taken = new Set((policies ?? []).map((p) => p.priority));
  return ESCALATION_PRIORITIES.filter((priority) => !taken.has(priority));
}

/** "Urgent and High", "Urgent, High and Normal". @param {string[]} parts */
export function joinWithAnd(parts) {
  if (!parts.length) return '';
  if (parts.length === 1) return parts[0];
  return `${parts.slice(0, -1).join(', ')} and ${parts[parts.length - 1]}`;
}
