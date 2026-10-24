import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const list = /** @type {any} */ (await import('./+page.server.js'));
const detail = /** @type {any} */ (await import('./[id]/+page.server.js'));

const ID = '0b9f4c6e-3f0a-4a5b-9a77-1c2d3e4f5a6b';
const KEY = 'lk_9f8e7d6c5b4a39281706f5e4d3c2b1a0';
const URL_ = `https://api.example.test/api/public/leads/${ID}/`;
const cookies = /** @type {any} */ ({ get: () => undefined });

/** @param {[string, string][]} entries @param {Record<string, string>} [params] */
function post(entries, params = {}) {
  const body = new FormData();
  for (const [key, value] of entries) body.append(key, value);
  return /** @type {any} */ ({
    request: new Request('http://test/settings/lead-capture', { method: 'POST', body }),
    cookies,
    params,
    locals: {}
  });
}

const status = (/** @type {number} */ n) => Object.assign(new Error('failed'), { status: n });

beforeEach(() => {
  apiRequest.mockReset();
});

describe('creating a webhook', () => {
  it('hands the page the URL and the key, once', async () => {
    apiRequest.mockResolvedValueOnce({
      id: ID,
      name: 'Ads',
      url: URL_,
      key: KEY,
      key_hint: 'b1a0'
    });
    const answer = await list.actions.create(
      post([
        ['name', ' Ads '],
        ['preset', 'google_ads'],
        ['default_source', 'google ads']
      ])
    );
    expect(answer).toEqual({ created: { id: ID, name: 'Ads', url: URL_, key: KEY } });
    expect(apiRequest.mock.calls[0][1].body).toEqual({
      name: 'Ads',
      preset: 'google_ads',
      default_source: 'google ads'
    });
  });

  it('leaves the source to the server when none was chosen', async () => {
    apiRequest.mockResolvedValueOnce({ id: ID, key: KEY });
    await list.actions.create(
      post([
        ['name', 'Ads'],
        ['preset', 'tally'],
        ['default_source', '']
      ])
    );
    expect('default_source' in apiRequest.mock.calls[0][1].body).toBe(false);
  });

  it('refuses an unknown preset or a blank name before asking', async () => {
    const bad = await list.actions.create(
      post([
        ['name', 'Ads'],
        ['preset', 'zapier']
      ])
    );
    expect(bad.status).toBe(400);
    const blank = await list.actions.create(
      post([
        ['name', ' '],
        ['preset', 'generic']
      ])
    );
    expect(blank.status).toBe(400);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('tells a member it is admin-only', async () => {
    apiRequest.mockRejectedValueOnce(status(403));
    const answer = await list.actions.create(
      post([
        ['name', 'Ads'],
        ['preset', 'generic']
      ])
    );
    expect(answer.status).toBe(403);
    expect(answer.data.create.error).toBe('Only an admin can add webhooks.');
  });
});

describe('the webhook page', () => {
  it('shows a member the admins-only state', async () => {
    apiRequest.mockRejectedValue(status(403));
    expect(await detail.load(post([], { id: ID }))).toEqual({ forbidden: true });
  });

  it('saves the settings and the mapping in one PATCH', async () => {
    apiRequest.mockResolvedValueOnce({});
    const answer = await detail.actions.save(
      post(
        [
          ['name', 'Ads'],
          ['default_source', 'google ads'],
          ['source_detail', 'Spring'],
          ['assignee', ''],
          ['tags', 't1'],
          ['tags', 't2'],
          ['mapping', JSON.stringify([{ from: 'user_column_data.EMAIL', to: 'email' }])]
        ],
        { id: ID }
      )
    );
    expect(answer).toEqual({ saved: true });
    expect(apiRequest.mock.calls[0]).toEqual([
      `/leads/intakes/${ID}/`,
      {
        method: 'PATCH',
        body: {
          name: 'Ads',
          default_source: 'google ads',
          source_detail: 'Spring',
          assignee: null,
          tags: ['t1', 't2'],
          mapping: [{ from: 'user_column_data.EMAIL', to: 'email' }]
        }
      },
      { cookies }
    ]);
  });

  it('leaves the stored mapping alone when the hidden input is malformed', async () => {
    apiRequest.mockResolvedValueOnce({});
    await detail.actions.save(
      post(
        [
          ['name', 'Ads'],
          ['mapping', '{not json']
        ],
        { id: ID }
      )
    );
    expect('mapping' in apiRequest.mock.calls[0][1].body).toBe(false);
  });

  it('switches on and off with is_active alone', async () => {
    apiRequest.mockResolvedValueOnce({});
    await detail.actions.toggle(post([['is_active', 'false']], { id: ID }));
    expect(apiRequest.mock.calls[0][1].body).toEqual({ is_active: false });
  });

  it('hands the new key to the page once on a replace', async () => {
    apiRequest.mockResolvedValueOnce({ key: KEY });
    expect(await detail.actions.key(post([], { id: ID }))).toEqual({ replaced: { key: KEY } });
  });

  it('sends a test and reports a refusal in words', async () => {
    apiRequest.mockResolvedValueOnce({ result: 'test' });
    expect(await detail.actions.test(post([], { id: ID }))).toEqual({ tested: true });
    apiRequest.mockRejectedValueOnce(status(404));
    const gone = await detail.actions.test(post([], { id: ID }));
    expect(gone.data.test.error).toBe('That webhook no longer exists.');
  });

  it('goes back to the list after a delete', async () => {
    apiRequest.mockResolvedValueOnce(null);
    await expect(detail.actions.remove(post([], { id: ID }))).rejects.toMatchObject({
      status: 303,
      location: '/settings/lead-capture'
    });
  });
});

describe('the lead capture page', () => {
  const ADDRESS = { id: 'm1', address: 'leads@acme.test', creates: 'leads', is_active: true };

  /** @param {any[]} modules */
  function serve(modules) {
    apiRequest.mockImplementation(async (/** @type {string} */ path) => {
      if (path === '/org/modules/') return { modules, can_edit: true };
      if (path === '/cases/mailboxes/') {
        return { mailboxes: [ADDRESS], totals: {}, can_create_leads: true };
      }
      if (path.startsWith('/webforms/')) return { results: [], totals: {} };
      if (path === '/leads/sources/') return { sources: [] };
      if (path === '/leads/intakes/') return { intakes: [] };
      throw status(404);
    });
  }
  const asked = () => apiRequest.mock.calls.map((c) => c[0]);

  it('reads the lead addresses while Tickets is off', async () => {
    serve([{ key: 'tickets', available: false, enabled: false }]);
    const page = await list.load({ cookies, locals: {} });
    expect(asked()).toContain('/cases/mailboxes/');
    expect(page.leadAddresses.map((/** @type {any} */ m) => m.address)).toEqual([
      'leads@acme.test'
    ]);
    expect(page.leadAddressesOffered).toBe(true);
  });

  it('does not ask for them while Tickets and Leads are both off', async () => {
    serve([
      { key: 'tickets', available: false, enabled: false },
      { key: 'leads', available: false, enabled: false }
    ]);
    const page = await list.load({ cookies, locals: {} });
    expect(asked()).not.toContain('/cases/mailboxes/');
    expect(page.leadAddresses).toBeNull();
  });
});
