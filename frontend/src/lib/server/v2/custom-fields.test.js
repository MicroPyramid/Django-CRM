import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { createCustomField, updateCustomField, deactivateCustomField } =
  await import('$lib/server/v2/custom-fields.js');

const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });

const base = {
  target_model: 'Case',
  key: 'severity',
  label: 'Severity',
  field_type: 'text',
  is_required: false,
  is_filterable: true,
  display_order: 3
};

describe('createCustomField', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('POSTs the definition to /custom-fields/', async () => {
    apiRequest.mockResolvedValue({ id: 'cf1', ...base });

    const result = await createCustomField(event, base);

    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/custom-fields/');
    expect(options.method).toBe('POST');
    expect(options.body.key).toBe('severity');
    expect(options.body.target_model).toBe('Case');
    expect(options.body.display_order).toBe(3);
    expect(result.id).toBe('cf1');
  });

  it('omits options entirely for a non-dropdown field', async () => {
    // `validate_definition_options` rejects a non-empty `options` on any type
    // other than dropdown, so sending [] or null on a text field is not
    // harmless noise, it is the difference between 201 and 400.
    apiRequest.mockResolvedValue({});

    await createCustomField(event, {
      ...base,
      field_type: 'text',
      options: [{ value: 'a', label: 'A' }]
    });

    expect(apiRequest.mock.calls[0][1].body.options).toBeUndefined();
  });

  it('sends dropdown options as {value,label} pairs', async () => {
    apiRequest.mockResolvedValue({});

    await createCustomField(event, {
      ...base,
      field_type: 'dropdown',
      options: [
        { value: '', label: 'Very High' },
        { value: 'low', label: 'Low' }
      ]
    });

    // A blank value is a new row; the label is slugified into one. An
    // existing value is preserved verbatim, because the stored values on
    // every record reference it.
    expect(apiRequest.mock.calls[0][1].body.options).toEqual([
      { value: 'very-high', label: 'Very High' },
      { value: 'low', label: 'Low' }
    ]);
  });

  it('rejects a dropdown with no options before making a request', async () => {
    await expect(
      createCustomField(event, { ...base, field_type: 'dropdown', options: [] })
    ).rejects.toThrow(/at least one option/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('never forwards a client-supplied org', async () => {
    apiRequest.mockResolvedValue({});
    await createCustomField(event, { ...base, org: 'attacker-org' });
    expect(apiRequest.mock.calls[0][1].body.org).toBeUndefined();
  });
});

describe('updateCustomField', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('PUTs to the detail endpoint without key, target_model or field_type', async () => {
    // Values live on each record keyed by `key`, and every stored value for a
    // field was written and checked against its `field_type`.
    // `CustomFieldDefinitionSerializer.validate()` freezes all three
    // server-side (a differing value in the PUT body is a 400); this layer is
    // what refuses to send any of them in the first place. `field_type` here
    // changes to `number`, not `dropdown`, on purpose: a `dropdown` value
    // would route through the options-shaping branch, which is a different
    // behaviour covered below.
    apiRequest.mockResolvedValue({});

    await updateCustomField(event, 'cf1', {
      ...base,
      key: 'renamed',
      target_model: 'Lead',
      field_type: 'number'
    });

    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/custom-fields/cf1/');
    expect(options.method).toBe('PUT');
    expect(options.body.key).toBeUndefined();
    expect(options.body.target_model).toBeUndefined();
    expect(options.body.field_type).toBeUndefined();
    expect(options.body.label).toBe('Severity');
  });

  it('still attaches options when editing an existing dropdown field', async () => {
    // `field_type` never reaches the outgoing body (it's frozen), but the
    // caller still has to say "this definition is a dropdown" so `buildBody`
    // knows to shape and attach `options`. Losing that signal on edit would
    // silently drop a dropdown's choices from every save.
    apiRequest.mockResolvedValue({});

    await updateCustomField(event, 'cf1', {
      ...base,
      field_type: 'dropdown',
      options: [{ value: 'low', label: 'Low' }]
    });

    const [, options] = apiRequest.mock.calls[0];
    expect(options.body.field_type).toBeUndefined();
    expect(options.body.options).toEqual([{ value: 'low', label: 'Low' }]);
  });

  it('supports a minimal reactivation body of just is_active', async () => {
    // The "Turn on" control posts only an id; its action calls this with
    // `{ is_active: true }` and nothing else, deliberately bypassing the
    // full-form field reader so a field the form never submitted can't read
    // back as an empty string and blank something out (see the `activate`
    // action's comment in +page.server.js).
    apiRequest.mockResolvedValue({});

    await updateCustomField(event, 'cf1', { is_active: true });

    const [, options] = apiRequest.mock.calls[0];
    expect(options.body).toEqual({ is_active: true });
  });
});

describe('deactivateCustomField', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('DELETEs the detail endpoint', async () => {
    apiRequest.mockResolvedValue({ error: false, message: 'Custom field deactivated' });

    await deactivateCustomField(event, 'cf1');

    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/custom-fields/cf1/');
    expect(options.method).toBe('DELETE');
  });

  it('refuses an empty id before making a request', async () => {
    await expect(deactivateCustomField(event, '')).rejects.toThrow(/which/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
