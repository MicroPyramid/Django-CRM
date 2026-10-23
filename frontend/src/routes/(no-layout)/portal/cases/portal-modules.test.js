import { describe, it, expect, vi } from 'vitest';

const portal = vi.hoisted(() => {
  class PortalError extends Error {
    constructor(status, data) {
      super('portal request failed');
      this.status = status;
      this.data = data;
    }
  }
  return { PortalError, failWith: /** @type {number} */ (404) };
});

vi.mock('#lib/server/portal.js', () => ({
  ACCESS_COOKIE: 'access',
  ORG_COOKIE: 'org',
  PortalError: portal.PortalError,
  clearSession: () => {},
  loginPath: () => '/portal/login',
  createCase: async () => ({}),
  listCases: async () => {
    throw new portal.PortalError(portal.failWith, { error: 'x' });
  }
}));

const { load } = await import('./+page.server.js');

/** @param {number} status */
async function run(status) {
  portal.failWith = status;
  const cookies = { get: () => 'token' };
  const url = new URL('http://localhost/portal/cases');
  try {
    await load(/** @type {any} */ ({ cookies, url }));
  } catch (err) {
    return err;
  }
  return undefined;
}

describe('cases list when its module is off', () => {
  it('sends a customer from the ticket list to articles when the list answers 404', async () => {
    const err = await run(404);
    expect(err).toMatchObject({ status: 303, location: '/portal/articles' });
  });

  it('still rethrows other portal errors as before', async () => {
    const err = await run(500);
    expect(err).toBeInstanceOf(portal.PortalError);
    expect(err.status).toBe(500);
  });
});
