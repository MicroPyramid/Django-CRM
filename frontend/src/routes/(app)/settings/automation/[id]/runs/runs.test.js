import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { load } = await import('./+page.server.js');

const ID = '11111111-1111-4111-8111-111111111111';
const cookies = /** @type {any} */ ({ get: () => undefined });

/** @param {string} id @param {string} [query] */
function event(id, query = '') {
  return /** @type {any} */ ({
    params: { id },
    url: new URL(`http://test/settings/automation/${id}/runs${query}`),
    cookies
  });
}

beforeEach(() => {
  apiRequest.mockReset();
  apiRequest.mockImplementation(async (path) =>
    path.includes('/runs/') ? { count: 45, results: [{ id: 'r1' }] } : { id: ID, name: 'Rule' }
  );
});

const runPath = () => apiRequest.mock.calls.map((c) => c[0]).find((p) => p.includes('/runs/'));

describe('load', () => {
  it('asks for 20 runs at the offset in the URL', async () => {
    const data = /** @type {any} */ (await load(event(ID, '?offset=40')));
    expect(runPath()).toBe(`/automation/rules/${ID}/runs/?limit=20&offset=40`);
    expect(data).toMatchObject({ offset: 40, pageSize: 20, count: 45, rule: { name: 'Rule' } });
    expect(data.runs).toHaveLength(1);
  });

  it('treats a bad offset as 0', async () => {
    for (const q of ['?offset=abc', '?offset=-5', '?offset=', '', `?offset=${'9'.repeat(22)}`]) {
      apiRequest.mockClear();
      const data = /** @type {any} */ (await load(event(ID, q)));
      expect(data.offset).toBe(0);
      expect(runPath()).toBe(`/automation/rules/${ID}/runs/?limit=20&offset=0`);
    }
  });

  it('answers 404 for a malformed id without calling the API', async () => {
    await expect(load(event('nope'))).rejects.toMatchObject({ status: 404 });
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('answers 404 for an unknown rule', async () => {
    apiRequest.mockRejectedValue({ status: 404 });
    await expect(load(event(ID))).rejects.toMatchObject({ status: 404 });
  });

  it('gives a member the forbidden notice after one request', async () => {
    apiRequest.mockRejectedValue({ status: 403 });
    expect(await load(event(ID))).toEqual({ forbidden: true });
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });
});
