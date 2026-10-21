import { error } from '@sveltejs/kit';
import { checkKey, getObject, listRecords, OBJECT_GONE } from '#lib/server/v2/custom-objects.js';
import { displayValue } from '#lib/server/v2/record-fields.js';

const LIST_COLUMNS = 4;

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, params, url }) {
  const key = checkKey(params.key);
  const q = (url.searchParams.get('q') ?? '').trim().slice(0, 100);
  const asked = Number(url.searchParams.get('page'));
  const pageNumber = Number.isInteger(asked) && asked >= 1 ? asked : 1;

  const definition = await getObject({ cookies }, key);
  if (definition.is_active === false) error(404, OBJECT_GONE);
  const columns = (definition.fields ?? [])
    .filter((/** @type {any} */ f) => f.field_type !== 'link')
    .slice(0, LIST_COLUMNS);

  const { count, results } = await listRecords({ cookies }, key, { q, page: pageNumber });
  return {
    definition,
    columns: columns.map((/** @type {any} */ f) => ({ key: f.key, label: f.label })),
    page: {
      count,
      results: results.map((/** @type {any} */ r) => ({
        id: r.id,
        name: r.name,
        cells: columns.map((/** @type {any} */ f) => displayValue(f, r.custom_fields?.[f.key])),
        assignees: (r.assigned_to ?? []).map((/** @type {any} */ p) => p.name || p.email)
      }))
    },
    q,
    pageNumber
  };
}
