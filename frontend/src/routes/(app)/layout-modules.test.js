/**
 * The shell asks which modules are on, then counts only those.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

/** @type {(endpoint: string) => Promise<any>} */
let respond = async () => {
  throw new Error('offline');
};

vi.mock('#lib/api-helpers.js', () => ({
  /** @param {string} endpoint */
  apiRequest: (endpoint) => respond(endpoint)
}));

const { load } = await import('./+layout.server.js');
const { resetObjectsAbsentMemo } = await import('#lib/server/v2/custom-objects.js');

const event = () =>
  /** @type {any} */ ({
    locals: { org: { name: 'Acme' }, org_settings: {}, profile: {} },
    cookies: { get: () => 'token' }
  });

const KEYS = [
  'deals',
  'leads',
  'goals',
  'tasks',
  'tickets',
  'knowledge_base',
  'documents',
  'invoices',
  'timesheet'
];

/** @param {string[]} off */
const modulesAnswer = (off) => ({
  can_edit: false,
  modules: KEYS.map((key) => ({
    key,
    label: key,
    group: 'sell',
    covers: '',
    stops: '',
    enabled: !off.includes(key),
    available: !off.includes(key),
    needs: null
  }))
});

/** @type {string[]} */
let asked = [];

/** @param {() => Promise<any>} modules */
function route(modules) {
  respond = async (endpoint) => {
    asked.push(endpoint);
    if (endpoint === '/org/modules/') return modules();
    if (endpoint.startsWith('/leads/')) return { totals: { count: 4 } };
    if (endpoint.startsWith('/notifications/')) return { unread_count: 2 };
    throw new Error('offline');
  };
}

describe('the shell modules answer', () => {
  beforeEach(() => {
    asked = [];
    resetObjectsAbsentMemo();
  });

  it('asks for the counts of available modules only', async () => {
    route(async () => modulesAnswer(['tickets']));
    const shell = /** @type {any} */ (await load(event()));
    expect(shell.modules).toHaveLength(9);
    expect(asked.some((e) => e.startsWith('/cases/'))).toBe(false);
    expect(asked.some((e) => e.startsWith('/leads/'))).toBe(true);
    expect(shell.counts.leads).toBe(4);
    expect(shell.counts.notifications).toBe(2);
    expect(shell.counts).not.toHaveProperty('tickets');
    expect(shell.counts).not.toHaveProperty('approvals');
  });

  it('asks for every count and returns modules null when the list answers 404', async () => {
    route(async () => {
      throw Object.assign(new Error('Not found'), { status: 404 });
    });
    const shell = /** @type {any} */ (await load(event()));
    expect(shell.modules).toBeNull();
    expect(asked.some((e) => e.startsWith('/cases/approvals/'))).toBe(true);
    expect(asked.some((e) => e.startsWith('/cases/'))).toBe(true);
    expect(asked.some((e) => e.startsWith('/opportunities/'))).toBe(true);
    expect(shell.org.name).toBe('Acme');
  });
});
