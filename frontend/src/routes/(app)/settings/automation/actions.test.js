import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

// Imports nothing from `$app/*`, so the standalone vitest config can load it.
const { load, actions } = await import('./+page.server.js');

const cookies = /** @type {any} */ ({ get: () => undefined });

const A = '11111111-1111-4111-8111-111111111111';
const B = '22222222-2222-4222-8222-222222222222';
const C = '33333333-3333-4333-8333-333333333333';
const OTHER = '44444444-4444-4444-8444-444444444444';

const RULES = [
  { id: A, name: 'A' },
  { id: B, name: 'B' },
  { id: C, name: 'C' }
];

/** @param {Record<string, string>} fields */
function event(fields) {
  const body = new FormData();
  for (const [key, value] of Object.entries(fields)) body.set(key, value);
  return /** @type {any} */ ({
    request: new Request('http://test/settings/automation?/move', { method: 'POST', body }),
    cookies
  });
}

beforeEach(() => {
  apiRequest.mockReset();
});

describe('load', () => {
  it('loads the rules, then the catalogue', async () => {
    apiRequest.mockImplementation(async (path) =>
      path === '/automation/rules/'
        ? { summary: '3 rules', results: RULES }
        : { objects: [{ key: 'lead' }] }
    );
    const data = await load(/** @type {any} */ ({ cookies }));
    expect(data).toEqual({
      summary: '3 rules',
      rules: RULES,
      catalogue: { objects: [{ key: 'lead' }] }
    });
    expect(apiRequest.mock.calls.map((c) => c[0])).toEqual([
      '/automation/rules/',
      '/automation/catalogue/'
    ]);
  });

  it('shows a member the admins-only notice without asking for the catalogue', async () => {
    apiRequest.mockImplementation(async () => {
      throw Object.assign(new Error('no'), { status: 403 });
    });
    const data = await load(/** @type {any} */ ({ cookies }));
    expect(data).toEqual({ forbidden: true });
    expect(apiRequest.mock.calls).toHaveLength(1);
  });
});

describe('move', () => {
  beforeEach(() => {
    apiRequest.mockImplementation(async (path) =>
      path === '/automation/rules/' ? { summary: null, results: RULES } : {}
    );
  });

  const reorderCalls = () => apiRequest.mock.calls.filter((c) => c[0].endsWith('/reorder/'));

  it('moves a rule by posting the whole new order', async () => {
    const result = await actions.move(event({ id: B, direction: 'up' }));
    expect(result).toEqual({ moved: true });
    expect(reorderCalls()).toHaveLength(1);
    expect(reorderCalls()[0][1]).toMatchObject({ method: 'POST', body: { ids: [B, A, C] } });
  });

  it.each([
    ['past the top', { id: A, direction: 'up' }],
    ['past the bottom', { id: C, direction: 'down' }],
    ['an unknown id', { id: OTHER, direction: 'up' }]
  ])('refuses a move %s without calling the reorder API', async (_n, fields) => {
    const result = /** @type {any} */ (await actions.move(event(fields)));
    expect(result.status).toBe(400);
    expect(reorderCalls()).toHaveLength(0);
  });

  it.each([
    ['a bad direction', { id: B, direction: 'sideways' }],
    ['a malformed id', { id: 'zz', direction: 'up' }],
    ['no id', { direction: 'up' }],
    ['no direction', { id: B }]
  ])('refuses %s before any API call', async (_n, fields) => {
    const result = /** @type {any} */ (await actions.move(event(fields)));
    expect(result.status).toBe(400);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('answers fail(400) with the server message when the reorder is refused', async () => {
    apiRequest.mockImplementation(async (path) => {
      if (path === '/automation/rules/') return { summary: null, results: RULES };
      throw Object.assign(new Error('x'), {
        status: 400,
        body: { error: true, errors: 'The list is out of date. Reload and try again.' }
      });
    });
    const result = /** @type {any} */ (await actions.move(event({ id: B, direction: 'down' })));
    expect(result.status).toBe(400);
    expect(result.data.error).toBe('The list is out of date. Reload and try again.');
  });
});
