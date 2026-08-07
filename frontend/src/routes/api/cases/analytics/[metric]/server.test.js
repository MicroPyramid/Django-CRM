import { describe, it, expect, vi } from 'vitest';

/**
 * The analytics proxy forwards the upstream status.
 *
 * `apiRequest` throws on any non-2xx, and an uncaught throw inside a
 * `+server.js` handler becomes a 500 whatever the real cause was. So a
 * `?from=banana`, which the API refuses with a 400 naming the field and the
 * reason, reached the caller as "internal server error" with both discarded.
 *
 * This file imports the route module directly. `vitest.config.js` warns that
 * route modules are outside this harness, but that warning is about
 * `+page.server.js`, which pulls `$app/forms` in through its actions. A
 * `+server.js` importing only `@sveltejs/kit` and `$lib` resolves fine, and
 * `./$types` is a JSDoc reference rather than a runtime import.
 */

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...args) => apiRequest(...args) }));

const { GET } = await import('./+server.js');

/**
 * The handler arg SvelteKit would build, with only the parts this route reads.
 *
 * Typed `any` deliberately. A real `RequestEvent` carries ten more properties
 * (`fetch`, `request`, `getClientAddress`, `platform` and the rest) that this
 * route never touches, and building them would be scaffolding that asserts
 * nothing. `svelte-check` runs over this file, so without the annotation it
 * reports every call site as a type error.
 *
 * @returns {any}
 */
function event(metric, query = '') {
  return {
    params: { metric },
    url: new URL(`http://localhost/api/cases/analytics/${metric}/${query}`),
    cookies: { get: () => 'token' },
    locals: { org: { id: 'org-1' } }
  };
}

/* No `beforeEach` resetting the mock. Both `mockReset` and `mockClear` make
   vitest report the previous test's rejected promise as unhandled, because
   clearing the recorded results loses the bookkeeping that says it was awaited.
   Every test sets its own implementation, and the two that assert on call
   history read `lastCall` or a delta, so accumulated history is harmless. */

/** An error shaped the way `api-helpers.js` throws one: message plus the two
 * properties it attaches, which are what the proxy reads back off it. */
function upstreamFailure(status, body) {
  const err = /** @type {Error & { status: number, body: unknown }} */ (
    new Error('upstream said no')
  );
  err.status = status;
  err.body = body;
  return err;
}

describe('the upstream status survives the proxy', () => {
  it('forwards a 400 as a 400', async () => {
    apiRequest.mockRejectedValue(upstreamFailure(400, { from: ["'banana' is not a valid date."] }));

    const response = await GET(event('frt', '?from=banana'));

    expect(response.status).toBe(400);
  });

  it('forwards the body, so the caller learns which field was wrong', async () => {
    const body = { from: ["'banana' is not a valid date."] };
    apiRequest.mockRejectedValue(upstreamFailure(400, body));

    const response = await GET(event('frt', '?from=banana'));

    expect(await response.json()).toEqual(body);
  });

  it('forwards a 403 as a 403, not as a 500', async () => {
    apiRequest.mockRejectedValue(upstreamFailure(403, { error: 'Admin access required' }));

    const response = await GET(event('agents'));

    expect(response.status).toBe(403);
  });

  it('forwards a real 500 as a 500', async () => {
    apiRequest.mockRejectedValue(upstreamFailure(500, {}));

    const response = await GET(event('frt'));

    expect(response.status).toBe(500);
  });

  it('answers 502 when the failure carries no status at all', async () => {
    /* A transport error rather than a rejection: the proxy reached nobody, so
       blaming the caller with a 4xx would be a guess. */
    apiRequest.mockRejectedValue(new Error('fetch failed'));

    const response = await GET(event('frt'));

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ error: 'fetch failed' });
  });
});

describe('the success path is unchanged', () => {
  it('returns the upstream payload with a 200', async () => {
    apiRequest.mockResolvedValue({ series: [1, 2, 3] });

    const response = await GET(event('frt', '?from=2026-08-01'));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ series: [1, 2, 3] });
  });

  it('passes the query string through verbatim', async () => {
    apiRequest.mockResolvedValue({});

    await GET(event('backlog', '?from=2026-08-01&to=2026-08-07&team=t1'));

    expect(apiRequest.mock.lastCall?.[0]).toBe(
      '/cases/analytics/backlog/?from=2026-08-01&to=2026-08-07&team=t1'
    );
  });
});

describe('an unknown metric is refused before any call', () => {
  it('answers 404', async () => {
    const response = await GET(event('banana'));

    expect(response.status).toBe(404);
  });

  it('does not reach the API', async () => {
    const before = apiRequest.mock.calls.length;

    await GET(event('banana'));

    expect(apiRequest.mock.calls.length).toBe(before);
  });
});
