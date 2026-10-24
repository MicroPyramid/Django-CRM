/**
 * Signup installs the chosen industry app on the new org, with the org-scoped
 * token minted for that one call, and a failed install never fails signup.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));
vi.mock('axios', () => ({ default: { post: vi.fn(), get: vi.fn() } }));

const axios = (await import('axios')).default;
const newOrg = await import('./+page.server.js');

function jar() {
  /** @type {Record<string, string>} */
  const store = { jwt_access: 'caller-token' };
  return {
    store,
    get: vi.fn((/** @type {string} */ name) => store[name]),
    set: vi.fn((/** @type {string} */ name, /** @type {string} */ value) => {
      store[name] = value;
    }),
    delete: vi.fn((/** @type {string} */ name) => {
      delete store[name];
    })
  };
}

/** @param {Record<string, string>} fields */
function createOrg(fields, cookies = jar()) {
  const body = new FormData();
  body.set('org_name', 'Acme');
  for (const [k, v] of Object.entries(fields)) body.set(k, v);
  return newOrg.actions.default(
    /** @type {any} */ ({
      request: new Request('http://app.test/org/new', { method: 'POST', body }),
      cookies,
      locals: { user: { id: 'u' } },
      getClientAddress: () => '198.51.100.7'
    })
  );
}

const failure = (/** @type {number} */ status) =>
  Object.assign(new Error('x'), { status, body: {} });

beforeEach(() => {
  apiRequest.mockReset();
  vi.mocked(axios.post).mockReset();
  vi.mocked(axios.post).mockImplementation(async (url) =>
    String(url).endsWith('/api/org/')
      ? { data: { org: { id: 'org-1' } } }
      : { data: { access_token: 'new-org-token' } }
  );
});

describe('installing the chosen app at signup', () => {
  it('installs it with sample records, as the new org', async () => {
    apiRequest.mockResolvedValue({ app: { id: 'real-estate', status: 'installed' } });
    const cookies = jar();
    const result = await createOrg({ vertical: 'real-estate' }, cookies);

    expect(result).toEqual({ data: { name: 'Acme' } });
    expect(apiRequest).toHaveBeenCalledTimes(1);
    const [path, options, locals] = apiRequest.mock.calls[0];
    expect(path).toBe('/apps/real-estate/install/');
    expect(options).toMatchObject({ method: 'POST', body: { sample_data: true } });
    expect(locals.cookies.get('jwt_access')).toBe('new-org-token');
    // The minted token is never written to the caller's session.
    expect(cookies.store.jwt_access).toBe('caller-token');
  });

  it('applies the pack the old way on an API without apps', async () => {
    apiRequest.mockRejectedValueOnce(failure(404)).mockResolvedValueOnce({ report: {} });
    await createOrg({ vertical: 'real-estate' });
    expect(apiRequest.mock.calls.map((c) => c[0])).toEqual([
      '/apps/real-estate/install/',
      '/packs/real-estate/apply/'
    ]);
  });

  it('still creates the org when the install fails', async () => {
    const quiet = vi.spyOn(console, 'error').mockImplementation(() => {});
    apiRequest.mockRejectedValue(failure(500));
    expect(await createOrg({ vertical: 'real-estate' })).toEqual({ data: { name: 'Acme' } });
    expect(apiRequest.mock.calls.map((c) => c[0])).toEqual(['/apps/real-estate/install/']);
    quiet.mockRestore();
  });

  it('installs nothing when the org skips the choice', async () => {
    await createOrg({ vertical: '' });
    expect(apiRequest).not.toHaveBeenCalled();
    expect(vi.mocked(axios.post).mock.calls.map((c) => c[0])).toEqual([
      expect.stringMatching(/\/api\/org\/$/)
    ]);
  });
});
