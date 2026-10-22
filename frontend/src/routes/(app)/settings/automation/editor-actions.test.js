import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

// Both import nothing from `$app/*`, so the standalone vitest config can load them.
const newRule = await import('./new/+page.server.js');
const oneRule = await import('./[id]/+page.server.js');

const cookies = /** @type {any} */ ({ get: () => undefined });
const ID = '11111111-1111-4111-8111-111111111111';
const OTHER = '22222222-2222-4222-8222-222222222222';

const DRAFT = {
  name: 'Deal won: onboarding',
  object_key: 'deal',
  match: 'all',
  trigger: { event: 'updated', field: 'stage_kind', to: 'won' },
  conditions: [{ field: 'amount', op: 'gt', value: 0 }],
  actions: [{ type: 'notify', to: ['admins'], people: [], message: 'Won: {name}' }]
};

const CATALOGUE = { objects: [{ key: 'deal', label: 'Deal', fields: [] }] };

/** @param {number} status @param {any} body */
const refusal = (status, body) => Object.assign(new Error('refused'), { status, body });

/**
 * @param {Record<string, string>} fields
 * @param {string} [id]
 */
function event(fields, id) {
  const body = new FormData();
  for (const [key, value] of Object.entries(fields)) body.set(key, value);
  return /** @type {any} */ ({
    request: new Request('http://test/settings/automation?/save', { method: 'POST', body }),
    cookies,
    params: id === undefined ? {} : { id }
  });
}

/** Runs an action and returns what it answers, or the redirect it throws. */
async function run(/** @type {any} */ call) {
  try {
    return await call;
  } catch (/** @type {any} */ thrown) {
    return thrown;
  }
}

const calls = () =>
  apiRequest.mock.calls.map(([path, options]) => [path, options?.method ?? 'GET']);

beforeEach(() => {
  apiRequest.mockReset();
});

describe('new rule', () => {
  it('loads the catalogue', async () => {
    apiRequest.mockResolvedValue(CATALOGUE);
    expect(await newRule.load(/** @type {any} */ ({ cookies }))).toEqual({ catalogue: CATALOGUE });
    expect(calls()).toEqual([['/automation/catalogue/', 'GET']]);
  });

  it('shows a member the admins-only notice', async () => {
    apiRequest.mockRejectedValue(refusal(403, { detail: 'Admins only.' }));
    expect(await newRule.load(/** @type {any} */ ({ cookies }))).toEqual({ forbidden: true });
  });

  it('creates a rule switched off, then redirects to it', async () => {
    apiRequest.mockResolvedValue({ id: ID });
    const result = await run(newRule.actions.save(event({ rule: JSON.stringify(DRAFT) })));
    expect(result).toMatchObject({ status: 303, location: `/settings/automation/${ID}` });
    expect(calls()).toEqual([['/automation/rules/', 'POST']]);
    expect(apiRequest.mock.calls[0][1].body).toEqual({ ...DRAFT, is_active: false });
  });

  it('creates and switches on when switch_on is true', async () => {
    apiRequest.mockResolvedValue({ id: ID });
    const result = await run(
      newRule.actions.save(event({ rule: JSON.stringify(DRAFT), switch_on: 'true' }))
    );
    expect(result).toMatchObject({ status: 303 });
    expect(apiRequest.mock.calls[0][1].body.is_active).toBe(true);
  });

  it('switches on only through switch_on, never through the rule field', async () => {
    apiRequest.mockResolvedValue({ id: ID });
    const smuggled = { ...DRAFT, is_active: true, owner: { id: OTHER }, position: 0 };
    await run(newRule.actions.save(event({ rule: JSON.stringify(smuggled) })));
    expect(apiRequest.mock.calls[0][1].body).toEqual({ ...DRAFT, is_active: false });
  });
});

describe('one rule', () => {
  const ROW = { ...DRAFT, id: ID, status: 'off', status_text: 'Off', runs_7d: 0 };

  /** @param {Record<string, any>} answers */
  const answer = (answers) =>
    apiRequest.mockImplementation(async (path) => {
      if (path in answers) {
        const value = answers[path];
        if (value instanceof Error) throw value;
        return value;
      }
      throw new Error(`unexpected ${path}`);
    });

  it('loads the catalogue, the rule and its row from the list', async () => {
    answer({
      '/automation/rules/': { summary: null, results: [{ ...ROW, id: OTHER }, ROW] },
      '/automation/catalogue/': CATALOGUE,
      [`/automation/rules/${ID}/`]: { ...DRAFT, id: ID }
    });
    const data = await oneRule.load(/** @type {any} */ ({ cookies, params: { id: ID } }));
    expect(data).toEqual({ catalogue: CATALOGUE, rule: { ...DRAFT, id: ID }, row: ROW });
  });

  it('gives no row when the list does not carry the rule', async () => {
    answer({
      '/automation/rules/': { summary: null, results: [] },
      '/automation/catalogue/': CATALOGUE,
      [`/automation/rules/${ID}/`]: { ...DRAFT, id: ID }
    });
    const data = /** @type {any} */ (
      await oneRule.load(/** @type {any} */ ({ cookies, params: { id: ID } }))
    );
    expect(data.row).toBeNull();
  });

  it('shows a member the admins-only notice after one request', async () => {
    apiRequest.mockRejectedValue(refusal(403, { detail: 'Admins only.' }));
    const data = await oneRule.load(/** @type {any} */ ({ cookies, params: { id: ID } }));
    expect(data).toEqual({ forbidden: true });
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });

  it('answers 404 for a rule the API does not have', async () => {
    answer({
      '/automation/rules/': { summary: null, results: [] },
      '/automation/catalogue/': CATALOGUE,
      [`/automation/rules/${ID}/`]: refusal(404, { detail: 'No such automation rule.' })
    });
    const thrown = await run(oneRule.load(/** @type {any} */ ({ cookies, params: { id: ID } })));
    expect(thrown.status).toBe(404);
  });

  it('answers 404 for a malformed rule id without calling the API', async () => {
    const thrown = await run(oneRule.load(/** @type {any} */ ({ cookies, params: { id: 'zz' } })));
    expect(thrown.status).toBe(404);
    const refused = await run(oneRule.actions.save(event({ rule: JSON.stringify(DRAFT) }, 'zz')));
    expect(refused.status).toBe(400);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('saves an existing rule without object_key, and asks to switch on only when told', async () => {
    apiRequest.mockResolvedValue({ ...DRAFT, id: ID });
    const { object_key: _key, ...rest } = DRAFT;

    const saved = await oneRule.actions.save(event({ rule: JSON.stringify(DRAFT) }, ID));
    expect(saved).toEqual({ saved: true });
    expect(calls()).toEqual([[`/automation/rules/${ID}/`, 'PATCH']]);
    expect(apiRequest.mock.calls[0][1].body).toEqual(rest);

    await oneRule.actions.save(event({ rule: JSON.stringify(DRAFT), switch_on: 'true' }, ID));
    expect(apiRequest.mock.calls[1][1].body).toEqual({ ...rest, is_active: true });

    await oneRule.actions.save(event({ rule: JSON.stringify(DRAFT), switch_on: 'false' }, ID));
    expect(apiRequest.mock.calls[2][1].body).not.toHaveProperty('is_active');
  });
});

describe('save refusals, on both pages', () => {
  const pages = /** @type {const} */ ([
    ['new', () => newRule.actions.save, undefined],
    ['one', () => oneRule.actions.save, ID]
  ]);

  it.each(pages)(
    'returns the row errors of a 400 and keeps nothing else (%s)',
    async (_n, save, id) => {
      apiRequest.mockRejectedValue(
        refusal(400, {
          errors: {
            'conditions[0].value': ['Enter a number.'],
            'trigger.to': ['Enter a value.'],
            name: ['This field may not be blank.']
          }
        })
      );
      const result = /** @type {any} */ (await save()(event({ rule: JSON.stringify(DRAFT) }, id)));
      expect(result.status).toBe(400);
      expect(result.data).toEqual({
        save: {
          general: null,
          rows: {
            'conditions.0': 'Enter a number.',
            trigger: 'Enter a value.',
            name: 'This field may not be blank.'
          }
        }
      });
    }
  );

  it.each(pages)('returns the plan refusal as the general error (%s)', async (_n, save, id) => {
    const detail = 'This install allows 2 active automation rules.';
    apiRequest.mockRejectedValue(refusal(403, { detail, code: 'plan_limit' }));
    const result = /** @type {any} */ (
      await save()(event({ rule: JSON.stringify(DRAFT), switch_on: 'true' }, id))
    );
    expect(result.status).toBe(403);
    expect(result.data).toEqual({ save: { general: detail, rows: {} } });
  });

  it.each(pages)('says something when the API cannot be reached (%s)', async (_n, save, id) => {
    apiRequest.mockRejectedValue(new Error('fetch failed'));
    const result = /** @type {any} */ (await save()(event({ rule: JSON.stringify(DRAFT) }, id)));
    expect(result.status).toBe(400);
    expect(result.data.save.general).toBe('fetch failed');
  });

  it.each(pages)(
    'refuses a rule field that is not JSON without calling the API (%s)',
    async (_n, save, id) => {
      for (const fields of [
        {},
        { rule: '' },
        { rule: '{"name": ' },
        { rule: 'null' },
        { rule: '[]' },
        { rule: '"a rule"' },
        { rule: JSON.stringify({ ...DRAFT, conditions: 'all' }) },
        { rule: JSON.stringify({ ...DRAFT, trigger: 'created' }) }
      ]) {
        const result = /** @type {any} */ (await save()(event(fields, id)));
        expect(result.status).toBe(400);
        expect(result.data).toEqual({ save: { general: 'Could not read the rule.', rows: {} } });
      }
      expect(apiRequest).not.toHaveBeenCalled();
    }
  );
});

describe('try, switch off and delete', () => {
  const STEPS = [
    { action: 0, type: 'notify', status: 'planned', text: 'Would notify Asha' },
    { action: 1, type: 'webhook', status: 'skipped', text: 'Nobody to notify' }
  ];
  const GONE = 'That record does not exist, or you cannot open it.';

  it('tries the saved rule on the chosen record', async () => {
    apiRequest.mockResolvedValue({ steps: STEPS });
    const result = await oneRule.actions.try(
      event({ record_id: OTHER, record_name: 'Acme renewal' }, ID)
    );
    expect(result).toEqual({ tried: { recordName: 'Acme renewal', steps: STEPS } });
    expect(calls()).toEqual([[`/automation/rules/${ID}/try/`, 'POST']]);
    expect(apiRequest.mock.calls[0][1].body).toEqual({ record_id: OTHER });
  });

  it('echoes only a plain, short record name', async () => {
    apiRequest.mockResolvedValue({ steps: [] });
    const long = /** @type {any} */ (
      await oneRule.actions.try(event({ record_id: OTHER, record_name: 'x'.repeat(500) }, ID))
    );
    expect(long.tried.recordName.length).toBeLessThanOrEqual(120);
    const none = /** @type {any} */ (await oneRule.actions.try(event({ record_id: OTHER }, ID)));
    expect(none.tried.recordName).toBe('');
  });

  it('refuses a malformed record id without calling the API', async () => {
    for (const fields of [{ record_id: 'zz' }, { record_id: '' }, {}]) {
      const result = /** @type {any} */ (await oneRule.actions.try(event(fields, ID)));
      expect(result.status).toBe(404);
      expect(result.data).toEqual({ tryError: GONE });
    }
    const badRule = /** @type {any} */ (
      await oneRule.actions.try(event({ record_id: OTHER }, 'zz'))
    );
    expect(badRule.status).toBe(404);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('turns a 404 from try into "That record does not exist, or you cannot open it."', async () => {
    apiRequest.mockRejectedValue(refusal(404, { detail: 'No such record.' }));
    const result = /** @type {any} */ (await oneRule.actions.try(event({ record_id: OTHER }, ID)));
    expect(result.status).toBe(404);
    expect(result.data).toEqual({ tryError: GONE });
  });

  it('says something when try cannot reach the API', async () => {
    apiRequest.mockRejectedValue(new Error('fetch failed'));
    const result = /** @type {any} */ (await oneRule.actions.try(event({ record_id: OTHER }, ID)));
    expect(result.status).toBe(400);
    expect(result.data.tryError).toBe('fetch failed');
  });

  it('switches off with is_active false only', async () => {
    apiRequest.mockResolvedValue({ id: ID, is_active: false });
    const result = await oneRule.actions.switchOff(
      event({ rule: JSON.stringify(DRAFT), is_active: 'true', name: 'x' }, ID)
    );
    expect(result).toEqual({ switchedOff: true });
    expect(calls()).toEqual([[`/automation/rules/${ID}/`, 'PATCH']]);
    expect(apiRequest.mock.calls[0][1].body).toEqual({ is_active: false });
  });

  it('reports a refused switch off', async () => {
    apiRequest.mockRejectedValue(refusal(403, { detail: 'Admins only.' }));
    const result = /** @type {any} */ (await oneRule.actions.switchOff(event({}, ID)));
    expect(result.status).toBe(403);
    expect(result.data.switchOff).toEqual({ general: 'Admins only.' });
  });

  it('deletes and returns to the list', async () => {
    apiRequest.mockResolvedValue(undefined);
    const result = await run(oneRule.actions.remove(event({}, ID)));
    expect(result).toMatchObject({ status: 303, location: '/settings/automation' });
    expect(calls()).toEqual([[`/automation/rules/${ID}/`, 'DELETE']]);
  });

  it('stays on the rule when the delete is refused, and never calls with a bad id', async () => {
    apiRequest.mockRejectedValue(refusal(403, { detail: 'Admins only.' }));
    const result = /** @type {any} */ (await oneRule.actions.remove(event({}, ID)));
    expect(result.status).toBe(403);
    expect(result.data.remove).toEqual({ general: 'Admins only.' });
    apiRequest.mockClear();
    const bad = /** @type {any} */ (await oneRule.actions.remove(event({}, 'zz')));
    expect(bad.status).toBe(400);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
