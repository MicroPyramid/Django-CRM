import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { actions } = /** @type {any} */ (await import('./+page.server.js'));

const ID = '0b9f4c6e-3f0a-4a5b-9a77-1c2d3e4f5a6b';
const cookies = /** @type {any} */ ({ get: () => undefined });

/** @param {Record<string, string>} fields */
function event(fields) {
  const body = new FormData();
  for (const [key, value] of Object.entries(fields)) body.set(key, value);
  return /** @type {any} */ ({
    request: new Request('http://test/settings/lead-sources', { method: 'POST', body }),
    cookies
  });
}

const SOURCES = {
  sources: [
    { id: 'a', key: 'call', label: 'Call', is_active: true, order: 0 },
    { id: 'b', key: 'email', label: 'Email', is_active: true, order: 1 },
    { id: 'c', key: 'fax', label: 'Fax', is_active: false, order: 2 }
  ]
};

const status = (/** @type {number} */ n) => Object.assign(new Error('failed'), { status: n });

beforeEach(() => {
  apiRequest.mockReset();
});

describe('add', () => {
  it('sends the label and answers it', async () => {
    apiRequest.mockResolvedValueOnce({});
    expect(await actions.add(event({ label: ' Spring fair ' }))).toEqual({ added: 'Spring fair' });
    expect(apiRequest.mock.calls[0][1]).toEqual({ method: 'POST', body: { label: 'Spring fair' } });
  });

  it('keeps what was typed when the API refuses it', async () => {
    apiRequest.mockRejectedValueOnce(
      Object.assign(new Error('label: exists'), { status: 400, body: {} })
    );
    const answer = await actions.add(event({ label: 'Call' }));
    expect(answer.status).toBe(400);
    expect(answer.data.add).toMatchObject({ label: 'Call', error: 'label: exists' });
  });

  it('tells a member it is admin-only', async () => {
    apiRequest.mockRejectedValueOnce(status(403));
    const answer = await actions.add(event({ label: 'X' }));
    expect(answer.status).toBe(403);
    expect(answer.data.add.error).toBe('Only an admin can change lead sources.');
  });
});

describe('retire', () => {
  it('sends is_active alone', async () => {
    apiRequest.mockResolvedValueOnce({});
    await actions.retire(event({ id: ID, is_active: 'false' }));
    expect(apiRequest.mock.calls[0]).toEqual([
      `/leads/sources/${ID}/`,
      { method: 'PATCH', body: { is_active: false } },
      { cookies }
    ]);
  });

  it('refuses a value that is not true or false', async () => {
    const answer = await actions.retire(event({ id: ID, is_active: 'maybe' }));
    expect(answer.status).toBe(400);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('move', () => {
  it('re-reads the list and posts every key in the new order', async () => {
    apiRequest.mockResolvedValueOnce(SOURCES).mockResolvedValueOnce({});
    expect(await actions.move(event({ key: 'fax', direction: 'up' }))).toEqual({ moved: 'fax' });
    expect(apiRequest.mock.calls[1][0]).toBe('/leads/sources/order/');
    expect(apiRequest.mock.calls[1][1].body).toEqual({ keys: ['call', 'fax', 'email'] });
  });

  it('posts nothing for a move off the end', async () => {
    apiRequest.mockResolvedValueOnce(SOURCES);
    const answer = await actions.move(event({ key: 'call', direction: 'up' }));
    expect(answer.status).toBe(400);
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });
});
