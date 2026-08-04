import { fail } from '@sveltejs/kit';
import {
  getRoutingRules,
  createRoutingRule,
  updateRoutingRule,
  deleteRoutingRule,
  readConditionRows
} from '$lib/server/v2/routing.js';
import { getOrgPeopleAndTeams } from '$lib/server/v2/org-people.js';
import { readableError } from '$lib/server/v2/form-errors.js';

// The rule list and the create/edit form's people/team pickers are two
// independent fetches: `getRoutingRules` no longer folds `getOrgPeopleAndTeams`
// into its own return, because `getSettingsHub` (the settings-hub aggregator)
// also calls `getRoutingRules` and only ever reads `.totals` off it. Folding
// the picker fetch in there fired an extra, unused `/users/get-teams-and-users/`
// request on every settings-hub load. Fetched in parallel here instead, since
// this is the one place both are actually needed.
/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  const [data, options] = await Promise.all([
    getRoutingRules({ cookies }),
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
 * from the one form that renders it.
 *
 * The condition rows are read by `readConditionRows` in `routing.js`, not
 * here: the form submits one indexed name per row (`condition_field_0` and so
 * on) and the reader pairs them by index, so a control that submits nothing
 * cannot shift its neighbours. Keeping it in the module is what makes that
 * rule testable, since the harness cannot import a route file.
 *
 * @param {FormData} form
 */
function readValues(form) {
  return {
    name: form.get('name')?.toString().trim() ?? '',
    priority_order: form.get('priority_order')?.toString() ?? '0',
    stop_processing: form.get('stop_processing') === 'true',
    strategy: form.get('strategy')?.toString() ?? '',
    target_assignee_ids: form.getAll('target_assignee_ids').map((v) => v.toString()),
    target_team_id: form.get('target_team_id')?.toString() ?? '',
    conditions: readConditionRows(form)
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  // Admin-only server-side (`RoutingRuleListCreateView.post` calls
  // `_is_admin` first). `can_edit` only hides the control.
  async create(event) {
    const form = await event.request.formData();
    const values = { ...readValues(form), is_active: form.get('is_active') === 'true' };
    try {
      await createRoutingRule(event, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { create: { error: 'Only an admin can add routing rules.' } });
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
      await updateRoutingRule(event, id, values);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { update: { error: 'Only an admin can change routing rules.' } });
      }
      return fail(400, { update: { error: readableError(err, 'Could not save the rule.') } });
    }
    return { updated: true };
  },

  async deactivate(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    try {
      await updateRoutingRule(event, id, { is_active: false });
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { deactivate: { error: 'Only an admin can turn routing rules off.' } });
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
  // has no key for it) and `createRoutingRule`/`updateRoutingRule`'s own
  // `buildBody` would forward that, blanking the name on every reactivation.
  // Calling `updateRoutingRule` directly with only `{ is_active: true }`
  // sidesteps `readValues` entirely, so the PUT body is `{ is_active: true }`
  // and nothing else.
  async activate(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    try {
      await updateRoutingRule(event, id, { is_active: true });
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { activate: { error: 'Only an admin can turn routing rules on.' } });
      }
      return fail(400, {
        activate: { error: readableError(err, 'Could not turn the rule on.') }
      });
    }
    return { activated: true };
  },

  // `RoutingRuleDetailView.delete` is a hard delete, unlike `/custom-fields/`.
  // The row control that posts here says so before it does.
  async remove(event) {
    const form = await event.request.formData();
    const id = form.get('id')?.toString() ?? '';
    try {
      await deleteRoutingRule(event, id);
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { remove: { error: 'Only an admin can delete routing rules.' } });
      }
      return fail(400, { remove: { error: readableError(err, 'Could not delete the rule.') } });
    }
    return { removed: true };
  }
};
