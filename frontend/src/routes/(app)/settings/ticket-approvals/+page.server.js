import { fail } from '@sveltejs/kit';
import {
  getApprovalRules,
  createApprovalRule,
  updateApprovalRule,
  deleteApprovalRule
} from '$lib/server/v2/ticket-approvals.js';
import { getOrgPeopleAndTeams } from '$lib/server/v2/org-people.js';
import { readableError } from '$lib/server/v2/form-errors.js';

// The rule list and the create/edit form's approver picker are two independent
// fetches: `getApprovalRules` does not fold `getOrgPeopleAndTeams` into its own
// return, because `getSettingsHub` (the settings-hub aggregator) also calls
// `getApprovalRules` and only ever reads `.totals` off it. Folding the picker
// fetch in there would fire an extra, unused `/users/get-teams-and-users/`
// request on every settings-hub load. Fetched in parallel here instead, since
// this is the one place both are actually needed.
/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  const [data, options] = await Promise.all([
    getApprovalRules({ cookies }),
    getOrgPeopleAndTeams(cookies)
  ]);
  return { ...data, ...options };
}

/**
 * Everything both the create and edit form submit. `is_active` is
 * deliberately not read here: only the create form carries that checkbox
 * (the edit form's own row control, Turn off / Turn on, owns that state), so
 * reading `form.get('is_active')` here would answer `false` on every edit
 * submit, since an absent checkbox and an unchecked one look identical to
 * `FormData`. The `create` action below attaches `is_active` itself, straight
 * from the one form that renders it. `trigger_event` is never read from the
 * form at all: `ticket-approvals.js` sets it, since `pre_close` is the only
 * value the backend accepts.
 *
 * @param {FormData} form
 */
function readValues(form) {
  return {
    name: form.get('name')?.toString().trim() ?? '',
    match_priority: form.get('match_priority')?.toString() ?? '',
    match_case_type: form.get('match_case_type')?.toString() ?? '',
    match_team_id: form.get('match_team_id')?.toString() ?? '',
    approver_role: form.get('approver_role')?.toString() ?? '',
    approver_ids: form.getAll('approver_ids').map((v) => v.toString())
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  // Admin-only server-side (`ApprovalRuleListCreateView.post` calls
  // `_is_admin` first). `can_edit` only hides the control.
  async create(event) {
    const form = await event.request.formData();
    const values = { ...readValues(form), is_active: form.get('is_active') === 'true' };
    try {
      await createApprovalRule(event, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { create: { error: 'Only an admin can change approval rules.' } });
      }
      return fail(400, { create: { error: readableError(err, 'Could not add the rule.') } });
    }
    return { created: true };
  },

  async update(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    const values = readValues(form);
    try {
      await updateApprovalRule(event, id, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { update: { error: 'Only an admin can change approval rules.' } });
      }
      return fail(400, { update: { error: readableError(err, 'Could not save the rule.') } });
    }
    return { updated: true };
  },

  async deactivate(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    try {
      await updateApprovalRule(event, id, { is_active: false });
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { deactivate: { error: 'Only an admin can change approval rules.' } });
      }
      return fail(400, {
        deactivate: { error: readableError(err, 'Could not turn the rule off.') }
      });
    }
    return { deactivated: true };
  },

  // A rule's own action, not a reuse of `update`. `readValues` builds a full
  // rule payload from the form, and this control only ever submits an id: if
  // it posted through `update`, `name` would read back as `''` (`FormData`
  // has no key for it) and `createApprovalRule`/`updateApprovalRule`'s own
  // `buildBody` would forward that, blanking the name on every reactivation.
  // Calling `updateApprovalRule` directly with only `{ is_active: true }`
  // sidesteps `readValues` entirely, so the PUT body is `{ is_active: true }`
  // and nothing else.
  async activate(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    try {
      await updateApprovalRule(event, id, { is_active: true });
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { activate: { error: 'Only an admin can change approval rules.' } });
      }
      return fail(400, {
        activate: { error: readableError(err, 'Could not turn the rule on.') }
      });
    }
    return { activated: true };
  },

  // `ApprovalRuleDetailView.delete` has two outcomes behind the one verb: a
  // rule with no approval history is destroyed, and a rule with any history
  // (in any state, not just pending) is turned off instead, because
  // `Approval.rule` is `on_delete=PROTECT`. Both answer 2xx, so which one
  // happened is read off the response body by `deleteApprovalRule` and
  // reported here rather than assumed. The page renders a line saying the
  // rule was turned off when that is what happened, so an admin is never told
  // "deleted" about a row that is still in the list.
  async remove(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    let outcome;
    try {
      outcome = await deleteApprovalRule(event, id);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { remove: { error: 'Only an admin can change approval rules.' } });
      }
      return fail(400, { remove: { error: readableError(err, 'Could not delete the rule.') } });
    }
    return { removed: !outcome.turned_off, remove: { turned_off: outcome.turned_off } };
  }
};
