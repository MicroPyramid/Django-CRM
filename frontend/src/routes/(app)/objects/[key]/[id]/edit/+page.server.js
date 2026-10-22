import { error, fail, redirect } from '@sveltejs/kit';
import {
  checkId,
  checkKey,
  getObject,
  getRecord,
  OBJECT_GONE,
  recordWriteError,
  updateRecord
} from '#lib/server/v2/custom-objects.js';
import { getOrgPeopleAndTeams } from '#lib/server/v2/org-people.js';
import { readRecordForm } from '#lib/server/v2/record-form.js';
import { linkFieldsForEdit, pairForEdit } from '#lib/server/v2/record-fields.js';
import { recordHref } from '#lib/v2/custom-objects.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  const key = checkKey(params.key);
  const id = checkId(params.id);
  const [definition, record, { people }] = await Promise.all([
    getObject({ cookies }, key),
    getRecord({ cookies }, key, id),
    getOrgPeopleAndTeams(cookies)
  ]);
  if (definition.is_active === false) error(404, OBJECT_GONE);
  if (!record.can_edit) redirect(303, recordHref(`obj:${key}`, id) ?? `/objects/${key}`);
  const plain = definition.fields.filter((/** @type {any} */ f) => f.field_type !== 'link');
  return {
    definition,
    record,
    people,
    fields: pairForEdit(plain, record.custom_fields),
    linkFields: linkFieldsForEdit(definition.fields, record.links)
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  async save({ cookies, params, request }) {
    const key = checkKey(params.key);
    const id = checkId(params.id);
    const event = { cookies };
    const definition = await getObject(event, key);
    const form = await request.formData();
    const body = readRecordForm(form, definition);

    try {
      await updateRecord(event, key, id, body);
    } catch (/** @type {any} */ err) {
      return fail(400, {
        values: { name: body.name, custom_fields: body.custom_fields },
        error: recordWriteError(err, definition.fields, definition.name_label)
      });
    }
    redirect(303, recordHref(`obj:${key}`, id) ?? `/objects/${key}`);
  }
};
