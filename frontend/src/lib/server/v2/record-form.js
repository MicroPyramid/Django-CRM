/**
 * The write body for a custom object record, read off a submitted form.
 * Only what the form was built to send is read: the field lists come from the
 * object's definition, never from the form's own keys.
 */
import { collectFromForm, collectLinks, collectAssignees } from '#lib/server/v2/record-fields.js';

/**
 * @param {FormData} form
 * @param {{ fields?: any[] }} definition The object with its active fields.
 * @returns {{ name: string, custom_fields: Record<string, any>, links?: Record<string, string[]>, assigned_to?: string[] }}
 */
export function readRecordForm(form, definition) {
  const fields = (definition.fields ?? []).filter((f) => f.is_active !== false);
  // Only the fields the form rendered are read, so a checkbox ticked after the page loaded is not overwritten.
  const rendered = new Set((form.get('cf__rendered')?.toString() ?? '').split(','));
  const plain = fields.filter((f) => f.field_type !== 'link' && rendered.has(f.key));
  const linkFields = fields.filter((f) => f.field_type === 'link');

  const body = {
    name: form.get('name')?.toString().trim() ?? '',
    custom_fields: collectFromForm(form, plain)
  };
  const links = collectLinks(form, linkFields);
  if (Object.keys(links).length > 0) body.links = links;
  const assignedTo = collectAssignees(form);
  if (assignedTo !== undefined) body.assigned_to = assignedTo;
  return body;
}
