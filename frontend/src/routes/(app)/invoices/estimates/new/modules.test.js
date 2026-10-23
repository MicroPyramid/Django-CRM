import { describe, it, expect, vi, beforeEach } from 'vitest';

const off = { value: /** @type {string[]} */ ([]), unreadable: false };
const calls = vi.hoisted(() => /** @type {string[]} */ ([]));

vi.mock('#lib/server/v2/modules.js', () => ({
  getModules: async () =>
    off.unreadable
      ? null
      : {
          canEdit: false,
          modules: [{ key: 'deals', label: 'Pipeline', available: !off.value.includes('deals') }]
        }
}));
vi.mock('#lib/server/v2/accounts.js', () => ({ listAccounts: async () => ({ results: [] }) }));
vi.mock('#lib/server/v2/contacts.js', () => ({ listContacts: async () => ({ results: [] }) }));
vi.mock('#lib/server/v2/products.js', () => ({ listProducts: async () => ({ results: [] }) }));
vi.mock('#lib/server/v2/deals.js', () => ({
  listDeals: async () => (calls.push('deals'), { results: [] })
}));
vi.mock('#lib/server/v2/estimates.js', () => ({
  createEstimate: async () => ({}),
  estimateFromDeal: async () => (calls.push('prefill'), null)
}));
vi.mock('#lib/server/v2/organization.js', () => ({ getNumbering: async () => null }));

const { load } = await import('./+page.server.js');

const event = () =>
  /** @type {any} */ ({
    cookies: {},
    url: new URL('http://x/invoices/estimates/new?opportunity=d1')
  });

beforeEach(() => {
  calls.length = 0;
  off.value = [];
  off.unreadable = false;
});

describe('new estimate load', () => {
  it('asks for deals and the prefill while Pipeline is on', async () => {
    const data = /** @type {any} */ (await load(event()));
    expect(calls.sort()).toEqual(['deals', 'prefill']);
    expect(data.modules).toEqual([{ key: 'deals', label: 'Pipeline', available: true }]);
  });

  it('treats an unreadable module list as Pipeline on, and returns null', async () => {
    off.unreadable = true;
    const data = /** @type {any} */ (await load(event()));
    expect(calls.sort()).toEqual(['deals', 'prefill']);
    expect(data.modules).toBeNull();
  });

  it('does not ask for deals on a new estimate while Pipeline is off', async () => {
    off.value = ['deals'];
    const data = /** @type {any} */ (await load(event()));
    expect(calls).toEqual([]);
    expect(data.deals).toEqual([]);
    expect(data.prefill).toBeNull();
    expect(data.modules[0].available).toBe(false);
  });
});
