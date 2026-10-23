import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const mod = /** @type {any} */ (await import('./+page.server.js'));
const { load, actions } = mod;

const cookies = /** @type {any} */ ({ get: () => undefined });

/** @param {string} key @param {string} group @param {Record<string, any>} [more] */
const row = (key, group, more = {}) => ({
  key,
  label: key,
  group,
  covers: '',
  stops: '',
  enabled: true,
  available: true,
  needs: null,
  ...more
});

const ROWS = [
  row('deals', 'sell'),
  row('leads', 'sell'),
  row('goals', 'sell', { needs: 'deals' }),
  row('tasks', 'serve'),
  row('tickets', 'serve', { enabled: false, available: false }),
  row('invoices', 'bill')
];

/** @param {Record<string, string>} fields */
function event(fields) {
  const body = new FormData();
  for (const [key, value] of Object.entries(fields)) body.set(key, value);
  return /** @type {any} */ ({
    request: new Request('http://test/settings/modules', { method: 'POST', body }),
    cookies
  });
}

/** @param {boolean} [canEdit] */
function serve(canEdit = true) {
  apiRequest.mockImplementation(async (_path, options) =>
    options?.method === 'PUT'
      ? { modules: ROWS, can_edit: true }
      : { modules: ROWS, can_edit: canEdit }
  );
}

const puts = () => apiRequest.mock.calls.filter((c) => c[1]?.method === 'PUT');

beforeEach(() => {
  apiRequest.mockReset();
});

describe('load', () => {
  it('answers the rows for an admin', async () => {
    serve();
    expect(await load(event({}))).toEqual({ modules: ROWS });
  });

  it('shows a member the admins-only notice and does not write for one', async () => {
    serve(false);
    expect(await load(event({}))).toEqual({ forbidden: true });
    const result = await actions.switch(event({ key: 'tasks', on: 'false' }));
    expect(result.status).toBe(403);
    expect(puts()).toHaveLength(0);
  });

  it('answers failed when the list cannot be read', async () => {
    apiRequest.mockRejectedValue(new Error('down'));
    expect(await load(event({}))).toEqual({ failed: true });
  });
});

describe('switch', () => {
  it('switches a module off with the off list and the served order', async () => {
    serve();
    const result = await actions.switch(event({ key: 'leads', on: 'false' }));
    expect(result).toEqual({ saved: true });
    expect(puts()[0][1].body).toEqual({
      off: ['leads', 'tickets'],
      order: ROWS.map((r) => r.key)
    });
  });

  it('switches a module on by taking it out of the off list', async () => {
    serve();
    await actions.switch(event({ key: 'tickets', on: 'true' }));
    expect(puts()[0][1].body.off).toEqual([]);
  });

  it('returns every refusal and writes nothing else', async () => {
    apiRequest.mockImplementation(async (_path, options) => {
      if (options?.method === 'PUT') {
        throw Object.assign(new Error('bad'), { status: 400, body: { off: ['a', 'b'] } });
      }
      return { modules: ROWS, can_edit: true };
    });
    const result = await actions.switch(event({ key: 'leads', on: 'false' }));
    expect(result.status).toBe(400);
    expect(result.data).toEqual({ errors: ['a', 'b'], key: 'leads' });
    expect(puts()).toHaveLength(1);
  });

  it('refuses an unknown key or flag without a write', async () => {
    serve();
    expect((await actions.switch(event({ key: 'crm', on: 'false' }))).status).toBe(400);
    expect((await actions.switch(event({ key: 'leads', on: 'maybe' }))).status).toBe(400);
    expect(puts()).toHaveLength(0);
  });
});

describe('move', () => {
  it('moves a module and keeps the off list', async () => {
    serve();
    const result = await actions.move(event({ key: 'leads', direction: 'up' }));
    expect(result).toEqual({ saved: true });
    expect(puts()[0][1].body).toEqual({
      off: ['tickets'],
      order: ['leads', 'deals', 'goals', 'tasks', 'tickets', 'invoices']
    });
  });

  it('refuses a move past a group end or an unknown key without a write', async () => {
    serve();
    expect((await actions.move(event({ key: 'deals', direction: 'up' }))).status).toBe(400);
    expect((await actions.move(event({ key: 'tickets', direction: 'down' }))).status).toBe(400);
    expect((await actions.move(event({ key: 'crm', direction: 'up' }))).status).toBe(400);
    expect(puts()).toHaveLength(0);
  });
});
