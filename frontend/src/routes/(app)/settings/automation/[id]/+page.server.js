import { error, fail, redirect } from '@sveltejs/kit';
import {
  getCatalogue,
  getRule,
  listRules,
  updateRule,
  ruleFromForm,
  refusedSave,
  tryRule,
  switchOff,
  deleteRule,
  RULE_GONE
} from '#lib/server/v2/automation.js';
import { UUID } from '#lib/v2/custom-objects.js';
import { checkId } from '#lib/server/v2/custom-objects.js';
import { readableError } from '#lib/server/v2/form-errors.js';

const RECORD_GONE = 'That record does not exist, or you cannot open it.';

/**
 * @param {any} err
 * @param {string} fallback
 */
function sentence(err, fallback) {
  return typeof err?.body?.detail === 'string' ? err.body.detail : readableError(err, fallback);
}

/** @param {any} err */
function statusOf(err) {
  return Number.isInteger(err?.status) && err.status >= 400 && err.status < 600 ? err.status : 400;
}

/**
 * The rule beside its row from the list, since only the list computes a
 * status. The list goes first so a member is refused once, not three times.
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  const { id } = event.params;
  if (!UUID.test(id)) error(404, RULE_GONE);
  const list = await listRules(event);
  if (list.forbidden) return { forbidden: true };
  const [catalogue, rule] = await Promise.all([getCatalogue(event), getRule(event, id)]);
  const row = (list.rules ?? []).find((/** @type {any} */ r) => r.id === rule.id) ?? null;
  return { catalogue, rule, row };
}

/** @type {import('./$types').Actions} */
export const actions = {
  async save(event) {
    const { id } = event.params;
    if (!UUID.test(id)) return fail(400, { save: { general: RULE_GONE, rows: {} } });
    const form = await event.request.formData();
    try {
      const body = ruleFromForm(form, { create: false });
      if (form.get('switch_on') === 'true') body.is_active = true;
      await updateRule(event, id, body);
    } catch (err) {
      return refusedSave(err);
    }
    return { saved: true };
  },

  /** Plans the saved rule on one record; nothing is written. */
  async try(event) {
    const { id } = event.params;
    if (!UUID.test(id)) return fail(404, { tryError: RULE_GONE });
    const form = await event.request.formData();
    const recordId = form.get('record_id');
    const name = form.get('record_name');
    try {
      checkId(/** @type {any} */ (recordId));
    } catch {
      return fail(404, { tryError: RECORD_GONE });
    }
    try {
      const steps = await tryRule(event, id, /** @type {string} */ (recordId));
      const recordName = typeof name === 'string' ? name.trim().slice(0, 120) : '';
      return { tried: { recordName, steps } };
    } catch (/** @type {any} */ err) {
      if (err?.status === 404) return fail(404, { tryError: RECORD_GONE });
      return fail(statusOf(err), { tryError: sentence(err, 'Could not try the rule.') });
    }
  },

  async switchOff(event) {
    const { id } = event.params;
    if (!UUID.test(id)) return fail(400, { switchOff: { general: RULE_GONE } });
    try {
      await switchOff(event, id);
    } catch (/** @type {any} */ err) {
      return fail(statusOf(err), {
        switchOff: { general: sentence(err, 'Could not switch the rule off.') }
      });
    }
    return { switchedOff: true };
  },

  async remove(event) {
    const { id } = event.params;
    if (!UUID.test(id)) return fail(400, { remove: { general: RULE_GONE } });
    try {
      await deleteRule(event, id);
    } catch (/** @type {any} */ err) {
      return fail(statusOf(err), {
        remove: { general: sentence(err, 'Could not delete the rule.') }
      });
    }
    redirect(303, '/settings/automation');
  }
};
