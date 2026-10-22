import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const {
  getCatalogue,
  listRules,
  getRule,
  createRule,
  updateRule,
  switchOff,
  deleteRule,
  tryRule,
  listRuns,
  reorderRules,
  automationSummary,
  NOT_AVAILABLE,
  ruleBody,
  moveRule,
  ruleErrors
} = await import('#lib/server/v2/automation.js');

const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });
const ID = '11111111-2222-3333-4444-555555555555';
const status = (s, body) => Object.assign(new Error('x'), { status: s, body });

beforeEach(() => apiRequest.mockReset());

describe('requests', () => {
  it('builds each request on its route', async () => {
    apiRequest.mockResolvedValue({ results: [], steps: [], count: 0 });
    const rule = { name: 'A' };
    /** @type {[() => Promise<any>, string, string | undefined, any][]} */
    const table = [
      [() => getCatalogue(event), '/automation/catalogue/', undefined, undefined],
      [() => listRules(event), '/automation/rules/', undefined, undefined],
      [() => getRule(event, ID), `/automation/rules/${ID}/`, undefined, undefined],
      [() => createRule(event, rule), '/automation/rules/', 'POST', rule],
      [() => updateRule(event, ID, rule), `/automation/rules/${ID}/`, 'PATCH', rule],
      [() => switchOff(event, ID), `/automation/rules/${ID}/`, 'PATCH', { is_active: false }],
      [() => deleteRule(event, ID), `/automation/rules/${ID}/`, 'DELETE', undefined],
      [
        () => tryRule(event, ID, 'rec'),
        `/automation/rules/${ID}/try/`,
        'POST',
        { record_id: 'rec' }
      ],
      [
        () => listRuns(event, ID, 40),
        `/automation/rules/${ID}/runs/?limit=20&offset=40`,
        undefined,
        undefined
      ],
      [() => reorderRules(event, [ID]), '/automation/rules/reorder/', 'POST', { ids: [ID] }]
    ];
    for (const [call, path, method, body] of table) {
      apiRequest.mockClear();
      await call();
      const [endpoint, options] = apiRequest.mock.calls[0];
      expect(endpoint).toBe(path);
      expect(options.method).toBe(method);
      expect(options.body).toEqual(body);
    }
  });

  it('shapes the try and runs answers', async () => {
    apiRequest.mockResolvedValueOnce({ steps: [{ action: 0 }] });
    expect(await tryRule(event, ID, 'r')).toEqual([{ action: 0 }]);
    apiRequest.mockResolvedValueOnce({ count: 1, results: [{ id: 'r1' }] });
    expect(await listRuns(event, ID, 20)).toEqual({
      count: 1,
      runs: [{ id: 'r1' }],
      offset: 20,
      pageSize: 20
    });
  });

  it('coerces the offset so a raw query value adds no parameter', async () => {
    apiRequest.mockResolvedValue({ count: 0, results: [] });
    const out = await listRuns(event, ID, /** @type {any} */ ('40&limit=100'));
    expect(out.offset).toBe(0);
    expect(apiRequest.mock.calls[0][0]).toBe(`/automation/rules/${ID}/runs/?limit=20&offset=0`);
    await listRuns(event, ID, /** @type {any} */ ('40'));
    expect(apiRequest.mock.calls[1][0]).toContain('offset=40');
    await listRuns(event, ID, -5);
    expect(apiRequest.mock.calls[2][0]).toContain('offset=0');
    await listRuns(event, ID, Number('9'.repeat(22)));
    expect(apiRequest.mock.calls[3][0]).toContain('offset=0');
  });

  it('expects a 403 and a 404 on one rule so a member or a stale id logs no error', async () => {
    apiRequest.mockResolvedValue({ id: ID });
    await getRule(event, ID);
    expect(apiRequest.mock.calls[0][1].expectedStatuses).toEqual([403, 404]);
  });

  it('expects a 403 and a 404 on the list and the catalogue, so a member or an API without automation logs no error', async () => {
    apiRequest.mockResolvedValue({ results: [] });
    await listRules(event);
    await getCatalogue(event);
    expect(apiRequest.mock.calls[0][1].expectedStatuses).toEqual([403, 404]);
    expect(apiRequest.mock.calls[1][1].expectedStatuses).toEqual([403, 404]);
  });

  it('turns a 404 on the list or the catalogue into a page 404 that says rules are not offered', async () => {
    expect(NOT_AVAILABLE).toBe('Automation rules are not available here.');
    for (const call of [() => listRules(event), () => getCatalogue(event)]) {
      apiRequest.mockRejectedValueOnce(status(404));
      await expect(call()).rejects.toMatchObject({ status: 404, body: { message: NOT_AVAILABLE } });
    }
    apiRequest.mockRejectedValueOnce(status(403));
    await expect(getCatalogue(event)).rejects.toMatchObject({ status: 403 });
  });

  it('refuses a malformed id before any request', async () => {
    await expect(getRule(event, '../x')).rejects.toMatchObject({ status: 404 });
    await expect(deleteRule(event, 'nope')).rejects.toMatchObject({ status: 404 });
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('turns a 403 list into forbidden, and a 404 rule into a SvelteKit 404', async () => {
    apiRequest.mockRejectedValueOnce(status(403));
    expect(await listRules(event)).toEqual({ forbidden: true });
    apiRequest.mockResolvedValueOnce({ summary: 'S', results: [{ id: 'a' }] });
    expect(await listRules(event)).toEqual({ summary: 'S', rules: [{ id: 'a' }] });
    apiRequest.mockRejectedValueOnce(status(500));
    await expect(listRules(event)).rejects.toMatchObject({ status: 500 });
    apiRequest.mockRejectedValueOnce(status(404));
    await expect(getRule(event, ID)).rejects.toMatchObject({
      status: 404,
      body: { message: 'That rule does not exist, or you do not have access to it.' }
    });
  });
});

describe('automationSummary', () => {
  it('answers null for the summary on 403, 500 and a network error', async () => {
    for (const err of [status(403), status(500), new TypeError('fetch failed')]) {
      apiRequest.mockRejectedValueOnce(err);
      expect(await automationSummary(event)).toBeNull();
    }
  });

  it('answers false on a 404: this API has no automation', async () => {
    apiRequest.mockRejectedValueOnce(status(404));
    expect(await automationSummary(event)).toBe(false);
  });

  it('counts active, failing and attention', async () => {
    apiRequest.mockResolvedValue({
      results: [
        { is_active: true, status: 'on', failures_7d: 2 },
        { is_active: false, status: 'paused', failures_7d: 0 },
        { is_active: false, status: 'off', failures_7d: 0 },
        { is_active: true, status: 'needs_attention', failures_7d: 0 }
      ]
    });
    expect(await automationSummary(event)).toEqual({ active: 2, failing: 2, attention: true });
    expect(apiRequest.mock.calls[0][1].quietErrors).toBe(true);
  });

  it('is calm when every rule is on and clean', async () => {
    apiRequest.mockResolvedValue({
      results: [{ is_active: true, status: 'on', failures_7d: 0 }]
    });
    expect(await automationSummary(event)).toEqual({ active: 1, failing: 0, attention: false });
  });
});

describe('ruleBody', () => {
  const raw = () => ({
    name: 'A',
    object_key: 'deal',
    owner: 'x',
    trigger: { event: 'updated', field: 'stage_kind', to: 'won', extra: 1 },
    match: 'all',
    conditions: [{ field: 'amount', op: 'gt', value: '0', junk: true }],
    actions: [
      { type: 'notify', to: ['admins'], people: [], message: 'Won: {name}', target: 'record' }
    ]
  });

  it('rebuilds a rule key by key and drops everything else', () => {
    expect(ruleBody(raw(), { create: false })).toEqual({
      name: 'A',
      trigger: { event: 'updated', field: 'stage_kind', to: 'won' },
      match: 'all',
      conditions: [{ field: 'amount', op: 'gt', value: '0' }],
      actions: [{ type: 'notify', to: ['admins'], people: [], message: 'Won: {name}' }]
    });
  });

  it('keeps object_key only on create', () => {
    expect(ruleBody(raw(), { create: true }).object_key).toBe('deal');
    expect('object_key' in ruleBody(raw(), { create: false })).toBe(false);
  });

  it('keeps the keys of every action type', () => {
    const body = ruleBody(
      {
        actions: [
          { type: 'set_field', target: 'record', field: 'f', value: null, x: 1 },
          { type: 'assign', mode: 'round_robin', people: ['p'], x: 1 },
          {
            type: 'create_task',
            title: 't',
            due_in_days: 2,
            priority: 'high',
            assign_to: 'me',
            person: 'p',
            x: 1
          },
          { type: 'webhook', endpoint: 'e', x: 1 }
        ]
      },
      { create: false }
    );
    expect(body.actions).toEqual([
      { type: 'set_field', target: 'record', field: 'f', value: null },
      { type: 'assign', mode: 'round_robin', people: ['p'] },
      {
        type: 'create_task',
        title: 't',
        due_in_days: 2,
        priority: 'high',
        assign_to: 'me',
        person: 'p'
      },
      { type: 'webhook', endpoint: 'e' }
    ]);
  });

  it('passes a stored id the catalogue no longer lists through unchanged', () => {
    const body = ruleBody(
      { actions: [{ type: 'webhook', endpoint: 'gone-id' }] },
      { create: false }
    );
    expect(body.actions[0].endpoint).toBe('gone-id');
  });

  it('refuses a body that is not an object, or a conditions value that is not a list', () => {
    for (const bad of [null, 'x', [], 3]) {
      expect(() => ruleBody(bad, { create: false })).toThrow('Could not read the rule.');
    }
    expect(() => ruleBody({ conditions: 'x' }, { create: false })).toThrow(
      'Could not read the rule.'
    );
    expect(() => ruleBody({ actions: {} }, { create: false })).toThrow('Could not read the rule.');
  });
});

describe('moveRule', () => {
  it('moves a rule up and down, and refuses the ends and unknown ids', () => {
    const ids = ['a', 'b', 'c'];
    expect(moveRule(ids, 'b', 'up')).toEqual(['b', 'a', 'c']);
    expect(moveRule(ids, 'b', 'down')).toEqual(['a', 'c', 'b']);
    expect(moveRule(ids, 'a', 'up')).toBeNull();
    expect(moveRule(ids, 'c', 'down')).toBeNull();
    expect(moveRule(ids, 'z', 'up')).toBeNull();
    expect(moveRule(ids, 'b', 'left')).toBeNull();
    expect(ids).toEqual(['a', 'b', 'c']);
  });
});

describe('ruleErrors', () => {
  it('maps row paths to row keys, first message per row', () => {
    const err = status(400, {
      errors: {
        'conditions[0].value': ['Enter a number.'],
        'actions[1].type': ['Unknown action.'],
        'actions[1].people': ['Second.'],
        'trigger.field': ['This field is not available.']
      }
    });
    expect(ruleErrors(err)).toEqual({
      general: null,
      rows: {
        'conditions.0': 'Enter a number.',
        'actions.1': 'Unknown action.',
        trigger: 'This field is not available.'
      }
    });
  });

  it('keeps name, match and the list-level limits as they are', () => {
    const err = status(400, {
      errors: {
        name: ['Name it.'],
        match: ['Pick one.'],
        conditions: ['Too many.'],
        actions: ['Add one.'],
        trigger: ['Bad.']
      }
    });
    expect(ruleErrors(err).rows).toEqual({
      name: 'Name it.',
      match: 'Pick one.',
      conditions: 'Too many.',
      actions: 'Add one.',
      trigger: 'Bad.'
    });
  });

  it('shows a 403 detail as the general error', () => {
    const err = status(403, { detail: 'Not available on this install', code: 'plan_limit' });
    expect(ruleErrors(err)).toEqual({ general: 'Not available on this install', rows: {} });
  });

  it('still gives a message when a 400 maps to no rows', () => {
    for (const errors of [{}, { name: [] }, { name: [3] }]) {
      const out = ruleErrors(status(400, { errors }));
      expect(out.rows).toEqual({});
      expect(typeof out.general).toBe('string');
      expect(out.general).not.toBe('');
    }
  });

  it('falls back to a readable message for anything else', () => {
    const out = ruleErrors(status(500, {}));
    expect(out.rows).toEqual({});
    expect(typeof out.general).toBe('string');
  });
});
