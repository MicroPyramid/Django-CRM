import { describe, expect, it } from 'vitest';
import {
  SIGNUP_SOURCE_COOKIE,
  readSignupSource,
  rememberSignupSource,
  sourceOfVisit
} from './signup-source.js';

const APP = 'https://crm.example.com/login';

function fakeCookies(initial = {}) {
  /** @type {Record<string, string>} */
  const jar = { ...initial };
  /** @type {any[]} */
  const sets = [];
  return {
    jar,
    sets,
    get: (/** @type {string} */ name) => jar[name],
    set: (/** @type {string} */ name, /** @type {string} */ value, /** @type {any} */ opts) => {
      jar[name] = value;
      sets.push({ name, value, opts });
    }
  };
}

/** @param {string} url @param {string | null} referer */
function visit(url, referer = null) {
  const headers = new Headers();
  if (referer) headers.set('referer', referer);
  return { url: new URL(url), request: new Request(url, { headers }) };
}

describe('sourceOfVisit', () => {
  it('keeps the campaign tags and the referring host', () => {
    const url = new URL(`${APP}?utm_source=site&utm_medium=web&utm_campaign=pricing&x=1`);
    expect(sourceOfVisit(url, 'https://News.Example.org/some/path?token=abc')).toEqual({
      utm_source: 'site',
      utm_medium: 'web',
      utm_campaign: 'pricing',
      referrer: 'news.example.org'
    });
  });

  it("ignores the app's own pages as a referrer", () => {
    expect(sourceOfVisit(new URL(APP), 'https://crm.example.com/logout')).toEqual({});
  });

  it('ignores a malformed referrer and blank tags', () => {
    expect(sourceOfVisit(new URL(`${APP}?utm_source=%20`), 'not a url')).toEqual({});
  });

  it('cuts a long tag', () => {
    const url = new URL(`${APP}?utm_campaign=${'c'.repeat(300)}`);
    expect(sourceOfVisit(url, null).utm_campaign).toHaveLength(100);
  });
});

describe('rememberSignupSource', () => {
  it('stores the first visit in an httpOnly cookie', () => {
    const cookies = fakeCookies();
    rememberSignupSource(
      {
        ...visit(`${APP}?utm_source=site`, 'https://example.org/'),
        cookies: /** @type {any} */ (cookies)
      },
      true
    );
    expect(JSON.parse(cookies.jar[SIGNUP_SOURCE_COOKIE])).toEqual({
      utm_source: 'site',
      referrer: 'example.org'
    });
    expect(cookies.sets[0].opts).toMatchObject({
      httpOnly: true,
      sameSite: 'lax',
      secure: true,
      path: '/'
    });
  });

  it('records a direct visit too, so a later one does not replace it', () => {
    const cookies = fakeCookies();
    rememberSignupSource({ ...visit(APP), cookies: /** @type {any} */ (cookies) }, false);
    expect(cookies.jar[SIGNUP_SOURCE_COOKIE]).toBe('{}');
  });

  it('keeps an earlier visit', () => {
    const cookies = fakeCookies({ [SIGNUP_SOURCE_COOKIE]: '{"referrer":"first.example"}' });
    rememberSignupSource(
      { ...visit(`${APP}?utm_source=later`), cookies: /** @type {any} */ (cookies) },
      false
    );
    expect(cookies.sets).toHaveLength(0);
  });
});

describe('readSignupSource', () => {
  it('returns the stored object', () => {
    const cookies = fakeCookies({ [SIGNUP_SOURCE_COOKIE]: '{"utm_source":"site"}' });
    expect(readSignupSource(cookies)).toEqual({ utm_source: 'site' });
  });

  it.each([undefined, '', 'not json', '[1,2]', '"text"', 'null'])(
    'returns undefined for %j',
    (raw) => {
      const cookies = fakeCookies(raw === undefined ? {} : { [SIGNUP_SOURCE_COOKIE]: raw });
      expect(readSignupSource(cookies)).toBeUndefined();
    }
  );
});
