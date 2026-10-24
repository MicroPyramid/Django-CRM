/**
 * The sign-in page remembers where a visitor came from, and creating an org
 * sends it once. Route modules are imported by path, as in
 * relay-callers.test.js.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SIGNUP_SOURCE_COOKIE } from './signup-source.js';

vi.mock('axios', () => ({ default: { post: vi.fn(), get: vi.fn() } }));
vi.mock('#lib/server/packs.js', () => ({ listPacks: vi.fn(), applyPack: vi.fn() }));
vi.mock('#lib/server/v2/apps.js', () => ({ installApp: vi.fn() }));

const axios = (await import('axios')).default;
const login = await import('../../routes/(no-layout)/login/+page.server.js');
const newOrg = await import('../../routes/(no-layout)/org/new/+page.server.js');

/** @param {Record<string, string>} initial */
function jar(initial = {}) {
  /** @type {Record<string, string>} */
  const store = { ...initial };
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

/** @param {() => unknown} run */
async function ignoringRedirect(run) {
  try {
    await run();
  } catch (/** @type {any} */ err) {
    if (!err?.status || err.status < 300 || err.status >= 400) throw err;
  }
}

/** @param {string} url @param {Record<string, string>} headers */
function loadLogin(url, headers, cookies) {
  return ignoringRedirect(() =>
    login.load(
      /** @type {any} */ ({
        url: new URL(url),
        request: new Request(url, { headers }),
        cookies,
        getClientAddress: () => '198.51.100.7'
      })
    )
  );
}

function createOrg(cookies) {
  const body = new FormData();
  body.set('org_name', 'Acme');
  return ignoringRedirect(() =>
    newOrg.actions.default(
      /** @type {any} */ ({
        request: new Request('http://app.test/org/new', { method: 'POST', body }),
        cookies,
        locals: { user: { id: 'u' } },
        getClientAddress: () => '198.51.100.7'
      })
    )
  );
}

const orgCreateBody = () =>
  vi.mocked(axios.post).mock.calls.find(([url]) => String(url).endsWith('/api/org/'))?.[1];

beforeEach(() => {
  vi.mocked(axios.post).mockReset();
  vi.mocked(axios.post).mockResolvedValue({ data: { org: { id: 'org-1' } } });
});

describe('the sign-in page', () => {
  it('remembers the tags and the referring host of a first visit', async () => {
    const cookies = jar();
    await loadLogin(
      'http://app.test/login?utm_source=site&utm_campaign=pricing',
      {
        referer: 'https://www.example.org/pricing'
      },
      cookies
    );
    expect(JSON.parse(cookies.store[SIGNUP_SOURCE_COOKIE])).toEqual({
      utm_source: 'site',
      utm_campaign: 'pricing',
      referrer: 'www.example.org'
    });
  });

  it("does not take Google's redirect back for a source", async () => {
    const cookies = jar();
    await loadLogin(
      'http://app.test/login?code=c&state=s',
      {
        referer: 'https://accounts.google.com/'
      },
      cookies
    );
    expect(cookies.store[SIGNUP_SOURCE_COOKIE]).toBeUndefined();
  });
});

describe('creating an org', () => {
  it('sends the remembered source once, then forgets it', async () => {
    const cookies = jar({
      jwt_access: 'token',
      [SIGNUP_SOURCE_COOKIE]: '{"utm_source":"site","referrer":"example.org"}'
    });
    await createOrg(cookies);
    expect(orgCreateBody()).toEqual({
      name: 'Acme',
      signup_source: { utm_source: 'site', referrer: 'example.org' }
    });
    expect(cookies.store[SIGNUP_SOURCE_COOKIE]).toBeUndefined();
  });

  it('sends no source when none was remembered', async () => {
    await createOrg(jar({ jwt_access: 'token' }));
    expect(orgCreateBody()).toEqual({ name: 'Acme' });
  });

  it('keeps the source when the create is refused', async () => {
    vi.mocked(axios.post).mockRejectedValueOnce(
      Object.assign(new Error('Bad Request'), {
        response: { status: 400, data: { errors: { name: ['taken'] } } }
      })
    );
    const cookies = jar({ jwt_access: 'token', [SIGNUP_SOURCE_COOKIE]: '{"utm_source":"site"}' });
    await createOrg(cookies);
    expect(cookies.store[SIGNUP_SOURCE_COOKIE]).toBe('{"utm_source":"site"}');
  });
});
