import { fail } from '@sveltejs/kit';
import { createIntake, listIntakes } from '#lib/server/v2/lead-intakes.js';
import { getLeadSources } from '#lib/server/v2/lead-sources.js';
import { getWebForms } from '#lib/server/v2/web-forms.js';
import { getMailboxes } from '#lib/server/v2/inbound-email.js';
import { getModules } from '#lib/server/v2/modules.js';
import { readableError } from '#lib/server/v2/form-errors.js';
import { mailboxesOn } from '#lib/v2/modules.js';
import { INTAKE_PRESETS } from '#lib/v2/lead-intakes.js';

/**
 * Every way a lead arrives, on one page: webhooks (admins only), web forms
 * and lead addresses. Web forms and addresses keep their own settings pages;
 * this lists them and links there. A section whose read fails shows nothing
 * rather than taking the others down, and mailboxes are only asked for while
 * Tickets or Leads is on, since their API is served only then.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  const modules = getModules(event).then((answer) => answer?.modules ?? null);
  const [intakes, { sources }, forms, mailboxes] = await Promise.all([
    listIntakes(event),
    getLeadSources(event),
    getWebForms(event).catch(() => null),
    modules.then((list) => (mailboxesOn(list) ? getMailboxes(event).catch(() => null) : null))
  ]);
  return {
    intakes: intakes.intakes,
    intakesState: intakes.state,
    sources,
    webForms: forms ? forms.forms.filter((/** @type {any} */ f) => f.target !== 'ticket') : null,
    webFormsTruncated: forms?.truncated ?? false,
    leadAddresses: mailboxes
      ? mailboxes.mailboxes.filter((/** @type {any} */ m) => m.creates === 'leads')
      : null,
    leadAddressesOffered: mailboxes?.can_create_leads ?? false
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * The response carries the full key, which goes to the page for this render
   * only. The webhook's mapping, tags and owner are set on its own page.
   */
  async create(event) {
    const form = await event.request.formData();
    /** @type {Record<string, string>} */
    const values = {
      name: form.get('name')?.toString().trim() ?? '',
      preset: form.get('preset')?.toString() ?? ''
    };
    // None chosen leaves the server's default in place.
    const source = form.get('default_source')?.toString() ?? '';
    if (source) values.default_source = source;
    if (!values.name) return fail(400, { create: { error: 'Give the webhook a name.', values } });
    if (!INTAKE_PRESETS.some((p) => p.value === values.preset)) {
      return fail(400, { create: { error: 'Choose what will send the leads.', values } });
    }
    try {
      return { created: await createIntake(event, values) };
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { create: { error: 'Only an admin can add webhooks.', values } });
      }
      return fail(400, {
        create: { error: readableError(err, 'Could not add the webhook.'), values }
      });
    }
  }
};
