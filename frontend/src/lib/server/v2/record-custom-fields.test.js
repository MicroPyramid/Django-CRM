import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const {
  fieldDefinitions,
  fieldsForNew,
  fieldsForDetail,
  fieldsForEdit,
  readCustomFields,
  saveRefusal
} = await import('./record-custom-fields.js');

const cookies = /** @type {any} */ ({ get: () => 'token' });

const DEFS = [
  { key: 'venue', label: 'Venue', field_type: 'text', display_order: 2, is_required: true },
  {
    key: 'stage',
    label: 'Stage',
    field_type: 'dropdown',
    display_order: 1,
    options: [{ value: 'booked', label: 'Booked' }]
  },
  { key: 'paid', label: 'Deposit paid', field_type: 'checkbox', display_order: 3 }
];

/** @param {Record<string, string>} fields */
function formOf(fields) {
  const form = new FormData();
  for (const [k, v] of Object.entries(fields)) form.append(k, v);
  return form;
}

beforeEach(() => {
  apiRequest.mockReset();
});

describe('fieldDefinitions', () => {
  it('asks for the active fields of one target, without counts, in display order', async () => {
    apiRequest.mockResolvedValue({ definitions: DEFS });
    const defs = await fieldDefinitions(cookies, 'RecurringInvoice');
    expect(apiRequest.mock.calls[0][0]).toBe(
      '/custom-fields/?target_model=RecurringInvoice&active_only=true&include_counts=false'
    );
    expect(defs.map((d) => d.key)).toEqual(['stage', 'venue', 'paid']);
  });

  it('answers no fields when the read fails', async () => {
    apiRequest.mockRejectedValue(new Error('down'));
    expect(await fieldDefinitions(cookies, 'Contact')).toEqual([]);
    expect(await fieldsForNew(cookies, 'Contact')).toEqual([]);
  });

  it('gives a New page empty inputs that carry the required flag', async () => {
    apiRequest.mockResolvedValue({ definitions: DEFS });
    const inputs = await fieldsForNew(cookies, 'Contact');
    expect(inputs.find((f) => f.key === 'venue')).toMatchObject({ value: '', is_required: true });
    expect(inputs.find((f) => f.key === 'paid')?.value).toBe(false);
  });
});

describe('fieldsForDetail', () => {
  it('shows every active field, filled or not, from the detail response', () => {
    const shown = fieldsForDetail({ custom_field_definitions: DEFS }, { stage: 'booked' });
    expect(shown.map((f) => [f.key, f.value, f.filled])).toEqual([
      ['stage', 'Booked', true],
      ['venue', '', false],
      ['paid', '', false]
    ]);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('shows no block when the org has no active fields, whatever the record holds', () => {
    expect(fieldsForDetail({ custom_field_definitions: [] }, { old: 'kept' })).toEqual([]);
    expect(fieldsForDetail({}, null)).toEqual([]);
  });
});

describe('fieldsForEdit', () => {
  it('keeps a stale dropdown value as an extra option', () => {
    const [stage] = fieldsForEdit({ custom_field_definitions: DEFS }, { stage: 'cancelled' });
    expect(stage.value).toBe('cancelled');
    expect(stage.options.map((/** @type {any} */ o) => o.value)).toEqual(['booked', 'cancelled']);
  });
});

describe('readCustomFields', () => {
  it('reads only the fields the form rendered, with an explicit false for a cleared box', async () => {
    apiRequest.mockResolvedValue({ definitions: DEFS });
    const { values, definitions } = await readCustomFields(
      cookies,
      'Contact',
      formOf({ cf__rendered: 'venue,paid', cf_venue: ' Hall ', cf_stage: 'booked' })
    );
    expect(values).toEqual({ venue: 'Hall', paid: false });
    expect(definitions.map((d) => d.key)).toEqual(['venue', 'paid']);
  });

  it('sends nothing and asks nothing when the form rendered no fields', async () => {
    expect(await readCustomFields(cookies, 'Contact', formOf({ cf_venue: 'x' }))).toEqual({
      values: undefined,
      definitions: []
    });
    expect(await readCustomFields(cookies, 'Contact', formOf({ cf__rendered: '' }))).toEqual({
      values: undefined,
      definitions: []
    });
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('refuses instead of sending nothing when the definitions cannot be read', async () => {
    apiRequest.mockRejectedValue(new Error('down'));
    const result = await readCustomFields(
      cookies,
      'Contact',
      formOf({ cf__rendered: 'venue', cf_venue: 'Hall' })
    );
    expect(result.values).toBeUndefined();
    expect(result.refusal?.error).toMatch(/could not be read/);
    expect(result.refusal?.fieldErrors).toEqual({});
  });

  it('drops a rendered key the org no longer defines', async () => {
    apiRequest.mockResolvedValue({ definitions: DEFS });
    const { values } = await readCustomFields(
      cookies,
      'Contact',
      formOf({ cf__rendered: 'gone', cf_gone: 'x' })
    );
    expect(values).toBeUndefined();
  });
});

describe('saveRefusal', () => {
  it('puts each custom_fields.<key> message beside its field', () => {
    const err = {
      status: 400,
      body: { error: true, errors: { custom_fields: { venue: 'is required', zzz: ['bad'] } } }
    };
    expect(saveRefusal(err, DEFS, 'Could not save.')).toEqual({
      error: 'Venue is required. zzz bad.',
      fieldErrors: { venue: 'Venue is required.', zzz: 'zzz bad.' }
    });
  });

  it('says a malformed custom_fields payload in one sentence', () => {
    const err = { body: { errors: { custom_fields: 'must be an object' } } };
    expect(saveRefusal(err, DEFS, 'x')).toEqual({
      error: 'Custom fields must be an object.',
      fieldErrors: {}
    });
  });

  it('falls back to the readable error for anything else', () => {
    const err = Object.assign(new Error('email: taken'), {
      body: { errors: { email: ['taken'] } }
    });
    expect(saveRefusal(err, DEFS, 'Could not save.')).toEqual({
      error: 'email: taken',
      fieldErrors: {}
    });
  });
});
