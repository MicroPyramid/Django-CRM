import { redirect } from '@sveltejs/kit';
import { getCatalogue, createRule, ruleFromForm, refusedSave } from '#lib/server/v2/automation.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  try {
    return { catalogue: await getCatalogue({ cookies }) };
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) return { forbidden: true };
    throw err;
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  async save(event) {
    const form = await event.request.formData();
    /** @type {any} */
    let created;
    try {
      const body = ruleFromForm(form, { create: true });
      body.is_active = form.get('switch_on') === 'true';
      created = await createRule(event, body);
    } catch (err) {
      return refusedSave(err);
    }
    redirect(303, `/settings/automation/${created.id}`);
  }
};
