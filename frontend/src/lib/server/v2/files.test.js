/**
 * The download proxy. What it forwards, what it refuses, and what it does not
 * leak.
 *
 * The rule this pins is the one the old code broke: a client never receives a
 * storage path. `attachmentHref`/`documentHref` return a route on this origin,
 * and `streamDownload` is the only thing that ever speaks to the file endpoint,
 * with the caller's own token.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest';

vi.mock('$env/dynamic/public', () => ({
  env: { PUBLIC_DJANGO_API_URL: 'http://api.test' }
}));

const { attachmentHref, documentHref, streamDownload } = await import('./files.js');

/** A Cookies-alike carrying just what the helper reads. */
function cookies(/** @type {Record<string, string>} */ jar) {
  return /** @type {any} */ ({ get: (/** @type {string} */ k) => jar[k] });
}

function upstream(status, { body = 'bytes', headers = {} } = {}) {
  return new Response(status === 200 ? body : null, { status, headers });
}

describe('href builders', () => {
  it('point at this origin, never at the storage path', () => {
    expect(attachmentHref('abc')).toBe('/api/attachments/abc/download');
    expect(documentHref('abc')).toBe('/api/documents/abc/download');
  });

  it('return null for a missing id so a page renders text, not a dead link', () => {
    expect(attachmentHref(null)).toBeNull();
    expect(attachmentHref(undefined)).toBeNull();
    expect(attachmentHref('')).toBeNull();
    expect(documentHref(null)).toBeNull();
  });
});

describe('streamDownload', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('refuses without a token instead of asking the API anonymously', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    const response = await streamDownload(
      { cookies: cookies({}), request: new Request('http://x/') },
      '/attachments/1/download/'
    );
    expect(response.status).toBe(401);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('sends the caller their own bearer token', async () => {
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(upstream(200, { headers: { 'Content-Type': 'text/plain' } }));

    await streamDownload(
      { cookies: cookies({ jwt_access: 'tok' }), request: new Request('http://x/') },
      '/attachments/1/download/'
    );

    const [url, init] = fetchSpy.mock.calls[0];
    expect(url).toBe('http://api.test/api/attachments/1/download/');
    const headers = /** @type {Record<string, string>} */ (init?.headers ?? {});
    expect(headers.Authorization).toBe('Bearer tok');
  });

  it('passes the upstream filename through rather than inventing one', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      upstream(200, {
        headers: { 'Content-Disposition': 'attachment; filename="Q3 pricing.pdf"' }
      })
    );

    const response = await streamDownload(
      { cookies: cookies({ jwt_access: 'tok' }), request: new Request('http://x/') },
      '/documents/1/download/'
    );

    expect(response.headers.get('Content-Disposition')).toBe(
      'attachment; filename="Q3 pricing.pdf"'
    );
  });

  it("tells caches not to keep one tenant's private file", async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(upstream(200));
    const response = await streamDownload(
      { cookies: cookies({ jwt_access: 'tok' }), request: new Request('http://x/') },
      '/documents/1/download/'
    );
    expect(response.headers.get('Cache-Control')).toBe('private, no-store');
  });

  it.each([403, 404])('passes a %d through as itself, not as a 500', async (status) => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(upstream(status));
    const response = await streamDownload(
      { cookies: cookies({ jwt_access: 'tok' }), request: new Request('http://x/') },
      '/attachments/1/download/'
    );
    expect(response.status).toBe(status);
  });

  it('streams the body it was given', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(upstream(200, { body: 'the file' }));
    const response = await streamDownload(
      { cookies: cookies({ jwt_access: 'tok' }), request: new Request('http://x/') },
      '/documents/1/download/'
    );
    expect(await response.text()).toBe('the file');
  });
});
