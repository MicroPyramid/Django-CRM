/**
 * The shell's token refresh and org switch send the visitor's signed address
 * (`#lib/server/relay.js`): the API writes an audit row for each, and without
 * it the row records this server.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// What Sentry captured: its wrapper captures, then calls the app's handler.
const captured = vi.hoisted(() => /** @type {unknown[]} */ ([]));
vi.mock('@sentry/sveltekit', () => ({
  sentryHandle:
    () =>
    (/** @type {any} */ { event, resolve }) =>
      resolve(event),
  handleErrorWithSentry: (/** @type {any} */ handler) => (/** @type {any} */ input) => {
    captured.push(input.error);
    return handler(input);
  }
}));
// `sequence` needs SvelteKit's request store, which only a running server has.
// Sentry's handle is a pass-through here, so the app's own handle is the last.
vi.mock('@sveltejs/kit/hooks', () => ({
  sequence: (/** @type {any[]} */ ...handles) => handles[handles.length - 1]
}));
vi.mock('axios', () => ({ default: { post: vi.fn(), get: vi.fn() } }));

const axios = (await import('axios')).default;
// The stub that vitest.config.js aliases `$app/env/private` to, so this is the module the code
// under test reads. Imported by path because only the stub has a setter.
const { setRelaySecret } = await import('../test/stubs/app-env-private.js');
const { handle, handleError } = await import('./hooks.server.js');

const SECRET = 'r'.repeat(48);
const VISITOR = '198.51.100.7';
const BROWSER = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/142.0 Safari/537.36';
const SIGNED = {
  'X-Forwarded-For': VISITOR,
  'X-BottleCRM-Relay-Secret': SECRET,
  'X-BottleCRM-Client-IP': VISITOR,
  'X-BottleCRM-User-Agent': BROWSER
};
const ORG = '11111111-2222-3333-4444-555555555555';

/** @param {Record<string, unknown>} claims */
const jwt = (claims) =>
  ['h', Buffer.from(JSON.stringify(claims)).toString('base64url'), 's'].join('.');
const hourFromNow = () => Math.floor(Date.now() / 1000) + 3600;

/** @param {Record<string, string>} jar */
function event(jar) {
  return /** @type {any} */ ({
    url: new URL('http://app.test/login'),
    request: new Request('http://app.test/login', { headers: { 'user-agent': BROWSER } }),
    route: { id: '/(no-layout)/login' },
    locals: {},
    cookies: {
      get: (/** @type {string} */ name) => jar[name],
      set: vi.fn(),
      delete: vi.fn()
    },
    getClientAddress: () => VISITOR
  });
}

const resolve = vi.fn(async () => new Response('ok'));

/** @param {string} path */
const callTo = (path) =>
  vi.mocked(axios.post).mock.calls.find(([url]) => String(url).endsWith(path));

beforeEach(() => {
  setRelaySecret(SECRET);
  vi.mocked(axios.post).mockReset();
});

afterEach(() => {
  setRelaySecret(undefined);
});

describe('hooks.server.js relays the visitor', () => {
  it('on a token refresh', async () => {
    vi.mocked(axios.post).mockResolvedValue({
      data: { access: jwt({ user_id: 'u', exp: hourFromNow() }) }
    });

    await handle({
      event: event({ jwt_access: jwt({ user_id: 'u', exp: 1 }), jwt_refresh: 'r-1' }),
      resolve
    });

    const [, body, config] = /** @type {any[]} */ (callTo('/auth/refresh-token/'));
    expect(body).toEqual({ refresh: 'r-1' });
    expect(config.headers).toEqual(SIGNED);
  });

  it('on an org switch', async () => {
    vi.mocked(axios.post).mockResolvedValue({
      data: {
        access_token: jwt({ user_id: 'u', org_id: ORG, exp: hourFromNow() }),
        refresh_token: 'r-2',
        current_org: { id: ORG, name: 'Acme' }
      }
    });

    await handle({
      event: event({
        jwt_access: jwt({ user_id: 'u', exp: hourFromNow() }),
        jwt_refresh: 'r-1',
        org: ORG
      }),
      resolve
    });

    const [, , config] = /** @type {any[]} */ (callTo('/auth/switch-org/'));
    expect(config.headers).toMatchObject(SIGNED);
    expect(config.headers.Authorization).toMatch(/^Bearer /);
  });

  it('sends only the pre-1.12 X-Forwarded-For without a secret', async () => {
    setRelaySecret(undefined);
    vi.mocked(axios.post).mockResolvedValue({ data: {} });

    await handle({
      event: event({ jwt_access: jwt({ user_id: 'u', exp: 1 }), jwt_refresh: 'r-3' }),
      resolve
    });

    expect(/** @type {any[]} */ (callTo('/auth/refresh-token/'))[2].headers).toEqual({
      'X-Forwarded-For': VISITOR
    });
  });
});

describe('hooks.server.js handleError', () => {
  beforeEach(() => {
    captured.length = 0;
  });
  afterEach(() => vi.restoreAllMocks());

  it('keeps a switched-off module out of Sentry, and still reports any other error', () => {
    const detail = 'Tickets is switched off for this organization.';
    const moduleOff = Object.assign(new Error(detail), {
      status: 404,
      body: { detail, code: 'module_off', module: 'tickets' }
    });
    vi.spyOn(console, 'error').mockImplementation(() => {});
    handleError(/** @type {any} */ ({ kind: 'unknown', error: moduleOff }));
    expect(captured).toEqual([]);
    const other = new Error('boom');
    handleError(/** @type {any} */ ({ kind: 'unknown', error: other }));
    expect(captured).toEqual([other]);
  });

  it('shows a module the API calls switched off as the module page', () => {
    const detail = 'Tickets is switched off for this organization.';
    const error = Object.assign(new Error(detail), {
      status: 404,
      body: { detail, code: 'module_off', module: 'tickets' }
    });
    const log = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(handleError(/** @type {any} */ ({ kind: 'unknown', error }))).toEqual({
      status: 404,
      message: detail,
      code: 'module_off',
      module: 'tickets'
    });
    expect(log).not.toHaveBeenCalled();
  });

  it('still prints the stack of any other unexpected error, and only the stack', () => {
    const error = Object.assign(new Error('boom'), { config: { headers: { Authorization: 'x' } } });
    const log = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(handleError(/** @type {any} */ ({ kind: 'unknown', error }))).toBeUndefined();
    expect(log).toHaveBeenCalledWith(error.stack);
    expect(
      handleError(/** @type {any} */ ({ kind: 'app', error: { status: 404 } }))
    ).toBeUndefined();
    expect(log).toHaveBeenCalledTimes(1);
  });
});
