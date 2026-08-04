import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const {
  createRoutingRule,
  updateRoutingRule,
  deleteRoutingRule,
  readConditionRows,
  CONDITION_FIELDS,
  CONDITION_OPS
} = await import('./routing.js');

const cookies = /** @type {any} */ ({ get: () => 'token' });
const event = /** @type {any} */ ({ cookies });

const base = {
  name: 'Urgent to Ada',
  priority_order: '5',
  is_active: true,
  stop_processing: true,
  strategy: 'direct',
  target_assignee_ids: ['p1'],
  target_team_id: '',
  conditions: [{ field: 'priority', op: 'eq', value: 'Urgent' }]
};

describe('createRoutingRule', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('sends only allow-listed keys on create', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      org: 'ATTACKER-ORG',
      created_by: 'ATTACKER'
    });
    const [url, opts] = apiRequest.mock.calls[0];
    expect(url).toBe('/cases/routing-rules/');
    expect(opts.method).toBe('POST');
    expect(Object.keys(opts.body).sort()).toEqual([
      'conditions',
      'is_active',
      'name',
      'priority_order',
      'stop_processing',
      'strategy',
      'target_assignee_ids'
    ]);
    expect(opts.body.priority_order).toBe(5);
    expect(opts.body.org).toBeUndefined();
    expect(opts.body.created_by).toBeUndefined();
  });

  it('coerces priority_order to a number', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, { ...base, priority_order: '12' });
    expect(apiRequest.mock.calls[0][1].body.priority_order).toBe(12);
    expect(typeof apiRequest.mock.calls[0][1].body.priority_order).toBe('number');
  });

  it('falls back to 0 for a non-numeric priority_order', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, { ...base, priority_order: 'not-a-number' });
    expect(apiRequest.mock.calls[0][1].body.priority_order).toBe(0);
  });

  it('coerces is_active and stop_processing to booleans', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      is_active: 'true',
      stop_processing: ''
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.is_active).toBe(true);
    expect(typeof body.is_active).toBe('boolean');
    expect(body.stop_processing).toBe(false);
    expect(typeof body.stop_processing).toBe('boolean');
  });

  it('drops condition rows with a blank field', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      conditions: [
        { field: '', op: 'eq', value: 'ignored' },
        { field: '   ', op: 'eq', value: 'also ignored' },
        { field: 'priority', op: 'eq', value: 'Urgent' }
      ]
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([{ field: 'priority', op: 'eq', value: 'Urgent' }]);
  });

  it('still sends a value key when a row has a field but no value key', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      conditions: [{ field: 'priority', op: 'eq' }]
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([{ field: 'priority', op: 'eq', value: '' }]);
  });

  it('defaults a condition row missing an operator to eq', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      conditions: [{ field: 'priority', op: '', value: 'Urgent' }]
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([{ field: 'priority', op: 'eq', value: 'Urgent' }]);
  });

  it('splits an "in" condition value on commas into a trimmed array', async () => {
    // `cases/routing.py`'s evaluator requires a list/tuple for `in` and
    // silently returns False for every ticket otherwise. A comma-separated
    // string is the only way one text input can express a list.
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      conditions: [{ field: 'priority', op: 'in', value: 'Urgent, High ,Medium' }]
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([
      { field: 'priority', op: 'in', value: ['Urgent', 'High', 'Medium'] }
    ]);
  });

  it('keeps an already-array "in" condition value as an array', async () => {
    // A rule whose `in` condition was seeded or created directly through the
    // API (not through this editor) already carries an array. Editing an
    // unrelated field on that same rule must not turn it into a string.
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      conditions: [{ field: 'priority', op: 'in', value: ['Urgent', 'High'] }]
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([{ field: 'priority', op: 'in', value: ['Urgent', 'High'] }]);
  });

  it('turns an empty "in" condition value into an empty array, and still sends the key', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      conditions: [{ field: 'priority', op: 'in' }]
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([{ field: 'priority', op: 'in', value: [] }]);
  });

  it('does not split an "eq" condition value that contains a comma', async () => {
    // A tag or account name can legitimately contain a comma. Only `in`
    // means "list"; every other operator's value is a literal string.
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      conditions: [{ field: 'tags', op: 'eq', value: 'North America, EMEA' }]
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([{ field: 'tags', op: 'eq', value: 'North America, EMEA' }]);
  });

  it('rejects a condition field the backend does not accept, before the request', async () => {
    await expect(
      createRoutingRule(event, {
        ...base,
        conditions: [{ field: 'severity', op: 'eq', value: 'high' }]
      })
    ).rejects.toThrow(/not a field a rule can match on/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('accepts a custom_fields.-prefixed condition field', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      conditions: [{ field: 'custom_fields.severity', op: 'eq', value: 'high' }]
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([{ field: 'custom_fields.severity', op: 'eq', value: 'high' }]);
  });

  it('rejects a condition operator the backend does not accept, before the request', async () => {
    await expect(
      createRoutingRule(event, {
        ...base,
        conditions: [{ field: 'priority', op: 'startswith', value: 'high' }]
      })
    ).rejects.toThrow(/not an operator a rule can use/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('drops target_team_id for a non-by_team strategy', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, { ...base, strategy: 'round_robin', target_team_id: 't1' });
    expect(apiRequest.mock.calls[0][1].body.target_team_id).toBeUndefined();
  });

  it('drops target_assignee_ids and keeps target_team_id for by_team', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      strategy: 'by_team',
      target_team_id: 't1',
      target_assignee_ids: ['p1', 'p2']
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.target_assignee_ids).toBeUndefined();
    expect(body.target_team_id).toBe('t1');
  });

  it('turns an empty-string target_team_id into null for by_team', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, { ...base, strategy: 'by_team', target_team_id: '' });
    expect(apiRequest.mock.calls[0][1].body.target_team_id).toBeNull();
  });

  it('filters falsy entries out of target_assignee_ids', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      strategy: 'direct',
      target_assignee_ids: ['p1', '', null, 'p2']
    });
    expect(apiRequest.mock.calls[0][1].body.target_assignee_ids).toEqual(['p1', 'p2']);
  });

  it('omits target_assignee_ids entirely when nobody is selected', async () => {
    // `[]` is not `None`, and `RoutingRuleSerializer.validate` only raises
    // when `assignees is None and self.instance is None`. Sending `[]` from an
    // empty multi-select therefore disarms the backend's own create guard: the
    // rule saves 201 with an empty pool, and with `stop_processing` on it eats
    // every matching ticket and assigns nobody. Omitting the key is what lets
    // the serializer answer.
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, { ...base, strategy: 'direct', target_assignee_ids: [] });
    const { body } = apiRequest.mock.calls[0][1];
    expect('target_assignee_ids' in body).toBe(false);
  });

  it('omits target_assignee_ids when every selected entry is blank', async () => {
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, {
      ...base,
      strategy: 'round_robin',
      target_assignee_ids: ['', null, undefined]
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect('target_assignee_ids' in body).toBe(false);
  });

  it('refuses a rule with no name before making a request', async () => {
    await expect(createRoutingRule(event, { ...base, name: '' })).rejects.toThrow(/needs a name/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('updateRoutingRule', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('PUTs to the detail endpoint', async () => {
    apiRequest.mockResolvedValue({});
    await updateRoutingRule(event, 'r1', base);
    const [url, opts] = apiRequest.mock.calls[0];
    expect(url).toBe('/cases/routing-rules/r1/');
    expect(opts.method).toBe('PUT');
  });

  it('omits nothing and adds nothing outside UPDATE_FIELDS on a full edit', async () => {
    apiRequest.mockResolvedValue({});
    await updateRoutingRule(event, 'r1', {
      ...base,
      strategy: 'round_robin',
      org: 'ATTACKER-ORG',
      created_by: 'ATTACKER'
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(Object.keys(body).sort()).toEqual([
      'conditions',
      'is_active',
      'name',
      'priority_order',
      'stop_processing',
      'strategy',
      'target_assignee_ids'
    ]);
    expect(body.org).toBeUndefined();
    expect(body.created_by).toBeUndefined();
  });

  it('sends exactly one key for a minimal { is_active: true } body', async () => {
    apiRequest.mockResolvedValue({});
    await updateRoutingRule(event, 'r1', { is_active: true });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body).toEqual({ is_active: true });
  });

  it('sends exactly one key for a minimal { is_active: false } body', async () => {
    apiRequest.mockResolvedValue({});
    await updateRoutingRule(event, 'r1', { is_active: false });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body).toEqual({ is_active: false });
  });

  it('refuses an edit that leaves a people strategy with no assignee', async () => {
    // The backend cannot answer this one. Its guard is behind
    // `self.instance is None`, and `put` is `partial=True`, so the request
    // would return 200 and leave the stored assignees exactly as they were:
    // a success for a change that did not happen, on a control the admin just
    // operated. Refused here, before the round trip.
    await expect(
      updateRoutingRule(event, 'r1', { ...base, strategy: 'direct', target_assignee_ids: [] })
    ).rejects.toThrow(/direct rule needs at least one assignee/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('names the strategy that refused, for each people strategy', async () => {
    await expect(
      updateRoutingRule(event, 'r1', { ...base, strategy: 'round_robin', target_assignee_ids: [] })
    ).rejects.toThrow(/round robin rule needs at least one assignee/i);
    await expect(
      updateRoutingRule(event, 'r1', { ...base, strategy: 'least_busy', target_assignee_ids: [] })
    ).rejects.toThrow(/least busy rule needs at least one assignee/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('refuses an edit whose assignee entries are all blank', async () => {
    await expect(
      updateRoutingRule(event, 'r1', {
        ...base,
        strategy: 'direct',
        target_assignee_ids: ['', null]
      })
    ).rejects.toThrow(/needs at least one assignee/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('allows an edit switching to by_team with an empty people list', async () => {
    // This path must stay open: switching a rule to by_team is exactly when
    // the people multi-select is empty and should be. `buildBody` drops the
    // assignee key for `by_team` before the emptiness check, so the guard
    // never sees it.
    apiRequest.mockResolvedValue({});
    await updateRoutingRule(event, 'r1', {
      ...base,
      strategy: 'by_team',
      target_team_id: 't1',
      target_assignee_ids: []
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.target_team_id).toBe('t1');
    expect('target_assignee_ids' in body).toBe(false);
  });

  it('allows a partial edit that never submitted an assignee list', async () => {
    // A caller that names a strategy without touching the picker is asking to
    // leave the assignees alone, which `partial=True` does. Only a submitted
    // and empty list is a discarded change.
    apiRequest.mockResolvedValue({});
    await updateRoutingRule(event, 'r1', { name: 'Renamed', strategy: 'direct' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body).toEqual({ name: 'Renamed', strategy: 'direct' });
  });

  it('leaves the turn-on and turn-off paths untouched by the guard', async () => {
    apiRequest.mockResolvedValue({});
    await updateRoutingRule(event, 'r1', { is_active: true });
    await updateRoutingRule(event, 'r1', { is_active: false });
    expect(apiRequest).toHaveBeenCalledTimes(2);
  });

  it('does not refuse a create with the same empty list', async () => {
    // Deliberately asymmetric. On create the backend's own guard fires and
    // its message is the better one, which is the whole point of omitting the
    // key rather than sending `[]`.
    apiRequest.mockResolvedValue({});
    await createRoutingRule(event, { ...base, strategy: 'direct', target_assignee_ids: [] });
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });

  it('throws when the id is missing', async () => {
    await expect(updateRoutingRule(event, '', base)).rejects.toThrow(/which rule/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('deleteRoutingRule', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('DELETEs the detail endpoint', async () => {
    apiRequest.mockResolvedValue({});
    await deleteRoutingRule(event, 'r1');
    const [url, opts] = apiRequest.mock.calls[0];
    expect(url).toBe('/cases/routing-rules/r1/');
    expect(opts.method).toBe('DELETE');
  });

  it('throws when the id is missing', async () => {
    await expect(deleteRoutingRule(event, '')).rejects.toThrow(/which rule/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('CONDITION_FIELDS and CONDITION_OPS', () => {
  // These are derived from `CONDITION_FIELD_LABEL`/`CONDITION_OP_LABEL` in
  // `$lib/v2/enums.js` rather than hand-restated, because the page's selects
  // read those maps directly (a `.svelte` file cannot import from
  // `$lib/server/`) and two hand-maintained copies of the same set drift.
  // This pins the derived lists to exactly what
  // `RoutingRuleSerializer.validate_conditions` accepts, so an addition to
  // the label maps that the backend does not also accept fails here instead
  // of shipping a field or operator the page offers and the API 400s.
  it('matches the fields RoutingRuleSerializer.validate_conditions accepts', () => {
    expect(CONDITION_FIELDS).toEqual([
      'priority',
      'case_type',
      'account',
      'tags',
      'from_email_domain',
      'mailbox_id'
    ]);
  });

  it('matches the operators RoutingRuleSerializer.validate_conditions accepts', () => {
    expect(CONDITION_OPS).toEqual(['eq', 'in', 'contains', 'regex']);
  });
});

describe('readConditionRows', () => {
  /**
   * One row's three inputs, as the form submits them.
   *
   * `omit` names a control that submitted nothing, which is what a `<select>`
   * with no matching option does: `selectedIndex` is -1 and the browser
   * contributes no entry for it at all.
   *
   * @param {FormData} form
   * @param {number} i
   * @param {{ field?: string, op?: string, value?: string }} row
   */
  function appendRow(form, i, row) {
    if (row.field !== undefined) form.append(`condition_field_${i}`, row.field);
    if (row.op !== undefined) form.append(`condition_op_${i}`, row.op);
    if (row.value !== undefined) form.append(`condition_value_${i}`, row.value);
  }

  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('pairs each row by its index', () => {
    const form = new FormData();
    appendRow(form, 0, { field: 'priority', op: 'eq', value: 'Urgent' });
    appendRow(form, 1, { field: 'tags', op: 'in', value: 'vip, gold' });
    expect(readConditionRows(form)).toEqual([
      { field: 'priority', op: 'eq', value: 'Urgent' },
      { field: 'tags', op: 'in', value: 'vip, gold' }
    ]);
  });

  it('does not shift the next row when a row submits no field', () => {
    // The defect this indexing replaced: three parallel `getAll` arrays paired
    // POSITIONALLY, so one absent `condition_field` moved every later row's
    // operator and value up by one. Here row 1 keeps its own op and value.
    const form = new FormData();
    appendRow(form, 0, { op: 'eq', value: 'EMEA' });
    appendRow(form, 1, { field: 'priority', op: 'in', value: 'High, Urgent' });
    expect(readConditionRows(form)).toEqual([
      { field: '', op: 'eq', value: 'EMEA' },
      { field: 'priority', op: 'in', value: 'High, Urgent' }
    ]);
  });

  it('reads rows in index order however the entries were appended', () => {
    const form = new FormData();
    appendRow(form, 2, { field: 'account', op: 'eq', value: 'Acme' });
    appendRow(form, 0, { field: 'priority', op: 'eq', value: 'Urgent' });
    expect(readConditionRows(form).map((r) => r.field)).toEqual(['priority', 'account']);
  });

  it('ignores form keys that are not indexed condition inputs', () => {
    const form = new FormData();
    form.append('name', 'Urgent to Ada');
    form.append('condition_field', 'priority');
    form.append('condition_field_x', 'priority');
    appendRow(form, 0, { field: 'tags', op: 'eq', value: 'vip' });
    expect(readConditionRows(form)).toEqual([{ field: 'tags', op: 'eq', value: 'vip' }]);
  });

  it('carries a custom_fields. condition through an edit unchanged', async () => {
    // The whole round trip: the page renders a stored `custom_fields.<key>`
    // as its own option so the select has something to match, the form
    // submits it under an indexed name, and the rule saves with the same two
    // conditions it had. Before this, an admin who opened Edit only to rename
    // a rule lost the custom-field condition and shifted the other row.
    apiRequest.mockResolvedValue({});
    const form = new FormData();
    appendRow(form, 0, { field: 'custom_fields.region', op: 'eq', value: 'EMEA' });
    appendRow(form, 1, { field: 'priority', op: 'in', value: 'High, Urgent' });
    await updateRoutingRule(event, 'r1', {
      name: 'Renamed, conditions untouched',
      strategy: 'direct',
      target_assignee_ids: ['p1'],
      conditions: readConditionRows(form)
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([
      { field: 'custom_fields.region', op: 'eq', value: 'EMEA' },
      { field: 'priority', op: 'in', value: ['High', 'Urgent'] }
    ]);
  });

  it('drops only the row that submitted no field, leaving the rest intact', async () => {
    apiRequest.mockResolvedValue({});
    const form = new FormData();
    appendRow(form, 0, { op: 'eq', value: 'EMEA' });
    appendRow(form, 1, { field: 'priority', op: 'in', value: 'High, Urgent' });
    await updateRoutingRule(event, 'r1', {
      name: 'Renamed',
      strategy: 'direct',
      target_assignee_ids: ['p1'],
      conditions: readConditionRows(form)
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.conditions).toEqual([{ field: 'priority', op: 'in', value: ['High', 'Urgent'] }]);
  });
});
