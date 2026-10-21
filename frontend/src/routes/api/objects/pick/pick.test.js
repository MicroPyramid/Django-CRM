import { describe, it, expect, vi, beforeEach } from 'vitest';

const searchLinkTargets = vi.fn();
vi.mock('#lib/server/v2/custom-objects.js', () => ({
  searchLinkTargets: (...a) => searchLinkTargets(...a)
}));

const { GET } = await import('./+server.js');

/**
 * @param {string} query
 * @param {string | null} token
 */
function call(query, token = 'tok') {
  return GET(
    /** @type {any} */ ({
      url: new URL(`http://x/api/objects/pick?${query}`),
      cookies: {
        get: (/** @type {string} */ n) => (n === 'jwt_access' ? (token ?? undefined) : undefined)
      }
    })
  );
}

beforeEach(() => searchLinkTargets.mockReset());

describe('GET /api/objects/pick', () => {
  it('refuses a caller with no session', async () => {
    const res = await call('target=lead&q=a', null);
    expect(res.status).toBe(401);
    expect(searchLinkTargets).not.toHaveBeenCalled();
  });

  it('answers the matches, uncached', async () => {
    searchLinkTargets.mockResolvedValueOnce([{ id: 'a', name: 'Ann' }]);
    const res = await call('target=lead&q=an');
    expect(await res.json()).toEqual([{ id: 'a', name: 'Ann' }]);
    expect(res.headers.get('Cache-Control')).toBe('private, no-store');
  });

  it('cuts the query to 100 characters', async () => {
    searchLinkTargets.mockResolvedValueOnce([]);
    await call(`target=lead&q=${encodeURIComponent('  ' + 'x'.repeat(150))}`);
    expect(searchLinkTargets.mock.calls[0][1]).toBe('lead');
    expect(searchLinkTargets.mock.calls[0][2]).toBe('x'.repeat(100));
  });

  it('answers 502 when the search fails', async () => {
    searchLinkTargets.mockRejectedValueOnce(new Error('down'));
    const res = await call('target=lead&q=a');
    expect(res.status).toBe(502);
    expect(await res.json()).toEqual({ error: 'Could not search.' });
  });
});
