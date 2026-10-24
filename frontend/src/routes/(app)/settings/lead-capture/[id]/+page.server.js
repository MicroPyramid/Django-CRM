import { fail, redirect } from '@sveltejs/kit';
import {
  deleteIntake,
  getIntake,
  replaceIntakeKey,
  testIntake,
  updateIntake
} from '#lib/server/v2/lead-intakes.js';
import { getLeadSources } from '#lib/server/v2/lead-sources.js';
import { getOrgPeopleAndTeams } from '#lib/server/v2/org-people.js';
import { getTags } from '#lib/server/v2/tags.js';
import { fieldDefinitions } from '#lib/server/v2/record-custom-fields.js';
import { readableError } from '#lib/server/v2/form-errors.js';

/**
 * One webhook: where to post, its settings and mapping, and its newest
 * deliveries. Another org's id or a missing one is a 404; a member gets the
 * same "admins only" state as the list.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  const detail = await getIntake(event, event.params.id);
  if (detail.forbidden) return { forbidden: true };
  const [{ sources }, people, tags, definitions] = await Promise.all([
    getLeadSources(event),
    getOrgPeopleAndTeams(event.cookies),
    getTags(event).then(
      (answer) => answer.tags,
      () => []
    ),
    fieldDefinitions(event.cookies, 'Lead')
  ]);
  return {
    ...detail,
    sources,
    people: people.people,
    tags: tags.map((/** @type {any} */ t) => ({ id: t.id, name: t.name, is_active: t.is_active })),
    customFields: definitions.map((/** @type {any} */ d) => ({ key: d.key, label: d.label }))
  };
}

/**
 * The mapping arrives as one JSON string, since rows are added and removed in
 * the browser. A malformed one is "not sent", never "empty", so a broken
 * input cannot wipe the stored mapping.
 *
 * @param {FormData} form
 * @returns {any[] | undefined}
 */
function readMapping(form) {
  const raw = form.get('mapping')?.toString();
  if (!raw) return undefined;
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : undefined;
  } catch {
    return undefined;
  }
}

/**
 * Turn an API refusal into the sentence the page shows, under `key`.
 * @param {string} key @param {any} err @param {string} fallback
 */
function refused(key, err, fallback) {
  if (err?.status === 403) {
    return fail(403, { [key]: { error: 'Only an admin can change webhooks.' } });
  }
  if (err?.status === 404) return fail(404, { [key]: { error: 'That webhook no longer exists.' } });
  return fail(400, { [key]: { error: readableError(err, fallback) } });
}

/** @type {import('./$types').Actions} */
export const actions = {
  async save(event) {
    const form = await event.request.formData();
    /** @type {Record<string, any>} */
    const values = {
      name: form.get('name')?.toString() ?? '',
      default_source: form.get('default_source')?.toString() ?? '',
      source_detail: form.get('source_detail')?.toString() ?? '',
      // Nobody is a real choice, so an empty select is sent as null.
      assignee: form.get('assignee')?.toString() || null,
      tags: form.getAll('tags').map(String).filter(Boolean)
    };
    const mapping = readMapping(form);
    if (mapping !== undefined) values.mapping = mapping;
    if (!values.name.trim()) return fail(400, { save: { error: 'A webhook needs a name.' } });
    try {
      await updateIntake(event, event.params.id, values);
    } catch (err) {
      return refused('save', err, 'Could not save the webhook.');
    }
    return { saved: true };
  },

  // Only `is_active`, so switching on or off never carries the settings form.
  async toggle(event) {
    const form = await event.request.formData();
    try {
      await updateIntake(event, event.params.id, { is_active: form.get('is_active') === 'true' });
    } catch (err) {
      return refused('toggle', err, 'Could not change the webhook.');
    }
    return { toggled: true };
  },

  async test(event) {
    try {
      await testIntake(event, event.params.id);
    } catch (err) {
      return refused('test', err, 'Could not send a test.');
    }
    return { tested: true };
  },

  async key(event) {
    try {
      const { key } = await replaceIntakeKey(event, event.params.id);
      return { replaced: { key } };
    } catch (err) {
      return refused('key', err, 'Could not replace the key.');
    }
  },

  async remove(event) {
    try {
      await deleteIntake(event, event.params.id);
    } catch (err) {
      return refused('remove', err, 'Could not delete the webhook.');
    }
    redirect(303, '/settings/lead-capture');
  }
};
