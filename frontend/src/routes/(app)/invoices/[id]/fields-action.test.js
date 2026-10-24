import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { actions } = /** @type {any} */ (await import('./+page.server.js'));

const cookies = /** @type {any} */ ({ get: () => 'token' });

function post() {
  const form = new FormData();
  form.append('cf__rendered', 'venue');
  form.append('cf_venue', 'Hall');
  return {
    cookies,
    params: { id: 'inv1' },
    request: new Request('http://x', { method: 'POST', body: form })
  };
}

describe('invoice ?/fields', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('fails readably, and writes nothing, when the definitions cannot be read', async () => {
    apiRequest.mockRejectedValue(new Error('down'));
    const result = await actions.fields(post());
    expect(result.status).toBe(503);
    expect(result.data.fieldsError).toMatch(/could not be read/);
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });
});
