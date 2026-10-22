import { error, fail, redirect } from '@sveltejs/kit';
import {
  checkKey,
  createRecord,
  getObject,
  OBJECT_GONE,
  recordWriteError
} from '#lib/server/v2/custom-objects.js';
import { getOrgPeopleAndTeams } from '#lib/server/v2/org-people.js';
import { readRecordForm } from '#lib/server/v2/record-form.js';
import { linkFieldsForEdit, pairForEdit } from '#lib/server/v2/record-fields.js';
import { recordHref } from '#lib/v2/custom-objects.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params }) {
  const key = checkKey(params.key);
  const [definition, { people }] = await Promise.all([
    getObject({ cookies }, key),
    getOrgPeopleAndTeams(cookies)
  ]);
  if (definition.is_active === false) error(404, OBJECT_GONE);
  const plain = definition.fields.filter((/** @type {any} */ f) => f.field_type !== 'link');
  return {
    definition,
    people,
    fields: pairForEdit(plain, {}),
    linkFields: linkFieldsForEdit(definition.fields, null)
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  async create({ cookies, params, request }) {
    const key = checkKey(params.key);
    const event = { cookies };
    const definition = await getObject(event, key);
    const form = await request.formData();
    const body = readRecordForm(form, definition);

    /** @type {any} */
    let created;
    try {
      created = await createRecord(event, key, body);
    } catch (/** @type {any} */ err) {
      return fail(400, {
        values: {
          name: body.name,
          custom_fields: body.custom_fields,
          assigned_to: body.assigned_to
        },
        error: recordWriteError(err, definition.fields, definition.name_label)
      });
    }
    redirect(303, recordHref(`obj:${key}`, created?.id) ?? `/objects/${key}`);
  }
};
