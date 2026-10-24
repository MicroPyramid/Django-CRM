/**
 * Settings hub: the wiring behind `/settings`.
 *
 * Server-only. The hub summarises every settings destination, so it needs a
 * number from each. Rather than a bespoke `/settings/summary/` endpoint, which
 * would have to reproduce, in Python across eight apps, the per-destination
 * rollups the pages already derive (escalation's "breaches going nowhere",
 * inbound's "silently dropping"). This fans out to the same server layers each
 * sub-page uses and assembles their totals. The calls run concurrently, so the
 * hub costs one round of parallel requests, not a dozen sequential ones.
 *
 * People, API tokens and the reopen policy are admin-only: their endpoints 403
 * a member. `listTeam` / `listOrgTokens` already fold that into a `forbidden`
 * sentinel; the reopen fetch throws, so it is caught below. Either way the hub
 * still lists those destinations for a member. It just omits the value and any
 * warning it cannot compute, the same way the shell omits the team badge a
 * member cannot count. Every other destination is readable by any member, so a
 * throw from one of those is a real failure and is left to propagate.
 */
import { automationSummary } from './automation.js';
import { getBusinessHours } from './business-hours.js';
import { getCustomFields } from './custom-fields.js';
import { getEscalationPolicies } from './escalation.js';
import { getHelpCenterSettings } from './help-center-settings.js';
import { getMailboxes } from './inbound-email.js';
import { getMacros } from './macros.js';
import { getOrgSettings } from './organization.js';
import { getReopenPolicy } from './reopen.js';
import { getRoutingRules } from './routing.js';
import { getTags } from './tags.js';
import { listTeam } from './team.js';
import { getApprovalRules } from './ticket-approvals.js';
import { listOrgTokens } from './tokens.js';
import { getWebForms } from './web-forms.js';
import { leadSourcesSummary } from './lead-sources.js';
import { intakesSummary } from './lead-intakes.js';
import { moduleOffError } from './modules.js';
import { isOn, mailboxesOn } from '#lib/v2/modules.js';

/** @typedef {import('#lib/v2/modules.js').ModuleRow[] | null} ModuleList */

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;

/**
 * Escalation "breaches that went nowhere", counted exactly as the escalation
 * page's `breachesGoingNowhere` does, so the hub's warning matches the page it
 * links to. A half is dead when the policy is off, reassigns to nobody, or
 * notifies nobody (no person and no team).
 * @param {any[]} policies
 */
function escalationRollup(policies) {
  let active = 0;
  let breaches = 0;
  for (const p of policies) {
    if (p.is_active) active += 1;
    /** @param {string} action @param {any} target */
    const halfDead = (action, target) => {
      if (!p.is_active) return true;
      if (action === 'reassign' && !target) return true;
      if (action === 'notify' && !target && !p.notify_team) return true;
      return false;
    };
    if (halfDead(p.first_response_action, p.first_response_target)) {
      breaches += p.breaches_last_30d?.first_response ?? 0;
    }
    if (halfDead(p.resolution_action, p.resolution_target)) {
      breaches += p.breaches_last_30d?.resolution ?? 0;
    }
  }
  return { active, count: policies.length, breaches_unhandled_30d: breaches };
}

/**
 * Mailboxes switched off that are still receiving mail, a customer ignored,
 * as opposed to an address deliberately retired. Matches the inbound page's
 * reasoning about which "off" is worth a warning.
 * @param {any[]} mailboxes @param {number} now
 */
function silentlyDropping(mailboxes, now) {
  return mailboxes.filter(
    (m) =>
      !m.is_active &&
      m.last_received_at &&
      now - new Date(m.last_received_at).getTime() < THIRTY_DAYS_MS
  ).length;
}

/**
 * Reopen policy → its `policy`, or null when the caller is a member (the
 * endpoint is admin-only and throws 403). Any other error still propagates.
 * @param {Promise<any>} promise
 */
async function reopenOrNull(promise) {
  try {
    return (await promise).policy;
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) return null;
    throw err;
  }
}

/**
 * The hub's numbers. A switched-off module's pages answer 404, so its calls
 * are skipped and its keys are null; the page hides those rows. Only those
 * calls wait for the list; the rest start at once.
 *
 * @param {{ cookies: import('@sveltejs/kit').Cookies }} event
 * @param {ModuleList | Promise<ModuleList>} [modules] the served list, or null
 */
export async function getSettingsHub(event, modules = null) {
  const listP = Promise.resolve(modules);
  /**
   * A module's call, run only while `on` says the list allows it. A
   * `module_off` answer (the list could not be read, or it went stale) is
   * null too, not a hub error.
   *
   * @template T
   * @param {(list: ModuleList) => boolean} on
   * @param {() => Promise<T>} call
   * @returns {Promise<T | null>}
   */
  const when = (on, call) =>
    listP.then((list) =>
      on(list)
        ? call().catch((/** @type {unknown} */ err) => {
            if (moduleOffError(err)) return null;
            throw err;
          })
        : null
    );
  /** @template T @param {string} key @param {() => Promise<T>} call */
  const ifOn = (key, call) => when((list) => isOn(list, key), call);
  const [
    org,
    calendar,
    tokens,
    team,
    routing,
    escalation,
    mailbox,
    reopenPolicy,
    approval,
    macro,
    tag,
    field,
    webForm,
    helpCenter,
    automation,
    leadSources,
    leadIntakes
  ] = await Promise.all([
    getOrgSettings(event),
    ifOn('tickets', () => getBusinessHours(event)),
    listOrgTokens(event),
    listTeam(event),
    ifOn('tickets', () => getRoutingRules(event)),
    ifOn('tickets', () => getEscalationPolicies(event)),
    when(mailboxesOn, () => getMailboxes(event)),
    ifOn('tickets', () => reopenOrNull(getReopenPolicy(event))),
    ifOn('tickets', () => getApprovalRules(event)),
    ifOn('tickets', () => getMacros(event)),
    getTags(event),
    getCustomFields(event),
    getWebForms(event),
    ifOn('knowledge_base', () => getHelpCenterSettings(event)),
    // Never throws: null when the rules cannot be read, so the hub still loads.
    automationSummary(event),
    // Neither throws; false where the API has no such list. Sources are
    // read whatever is switched off: deals use them too.
    leadSourcesSummary(event),
    ifOn('leads', () => intakesSummary(event))
  ]);

  const now = Date.now();
  return {
    org: org.org,
    calendar: calendar ? calendar.calendar : null,
    // Admin-only oversight: null for a member (endpoint 403'd), so the hub
    // shows the destination without a value it is not allowed to compute.
    tokenTotals: tokens.forbidden ? null : tokens.totals,
    peopleTotals: team.forbidden ? null : team.totals,
    routingTotals: routing ? routing.totals : null,
    escalationTotals: escalation ? escalationRollup(escalation.policies) : null,
    mailboxTotals: mailbox
      ? { ...mailbox.totals, silently_dropping: silentlyDropping(mailbox.mailboxes, now) }
      : null,
    mailboxLeads: mailbox ? mailbox.can_create_leads === true : false,
    reopen: reopenPolicy,
    approvalRules: approval ? approval.rules : null,
    approvalTotals: approval ? approval.totals : null,
    macroTotals: macro ? macro.totals : null,
    tagTotals: tag.totals,
    fieldTotals: field.totals,
    webFormTotals: webForm.totals,
    helpCenter,
    automation,
    leadSources,
    leadIntakes
  };
}
