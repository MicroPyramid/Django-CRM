/**
 * The shell asks once whether this install serves custom objects and hands the
 * answer to every page; any failure leaves it null and the shell intact.
 */
import { describe, it, expect, vi } from 'vitest';

/** @type {(endpoint: string) => Promise<any>} */
let respond = async () => {
  throw new Error('offline');
};

vi.mock('#lib/api-helpers.js', () => ({
  /** @param {string} endpoint */
  apiRequest: (endpoint) => respond(endpoint)
}));

const { load } = await import('./+layout.server.js');

const ANSWER = {
  has_custom_objects: true,
  objects: [{ key: 'property', label: 'Property', label_plural: 'Properties' }],
  link_targets: []
};

const event = () =>
  /** @type {any} */ ({
    locals: { org: { name: 'Acme' }, org_settings: {}, profile: {} },
    cookies: { get: () => 'token' }
  });

/** @param {() => Promise<any>} objects */
function route(objects) {
  respond = async (endpoint) => {
    if (endpoint.startsWith('/objects/')) return objects();
    throw new Error('offline');
  };
}

describe('the shell custom objects answer', () => {
  it('carries the objects answer', async () => {
    route(async () => ANSWER);
    const shell = /** @type {any} */ (await load(event()));
    expect(shell.customObjects.objects[0].key).toBe('property');
  });

  it('carries null when the server has no custom objects', async () => {
    route(async () => {
      throw Object.assign(new Error('Not found'), { status: 404 });
    });
    const shell = /** @type {any} */ (await load(event()));
    expect(shell.customObjects).toBeNull();
  });

  it('still loads the shell when the objects call fails', async () => {
    route(async () => {
      throw Object.assign(new Error('boom'), { status: 500 });
    });
    const shell = /** @type {any} */ (await load(event()));
    expect(shell.customObjects).toBeNull();
    expect(shell.org.name).toBe('Acme');
  });
});
