/**
 * The ticket page asks only for what its modules serve, and the estimate and
 * task form loads skip pickers of a switched-off module.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

const off = { value: /** @type {string[]} */ ([]), unreadable: false };
const calls = vi.hoisted(() => /** @type {string[]} */ ([]));

vi.mock('#lib/server/v2/modules.js', () => ({
  getModules: async () =>
    off.unreadable
      ? null
      : {
          canEdit: false,
          modules: ['timesheet', 'knowledge_base', 'deals'].map((key) => ({
            key,
            label: key,
            available: !off.value.includes(key)
          }))
        }
}));
vi.mock('#lib/server/v2/tickets.js', () => ({
  getTicket: async () => ({ ticket: { id: 't1' }, articles: [], canReply: true }),
  listTicketTime: async () => (calls.push('time'), []),
  suggestTicketArticles: async () => (calls.push('articles'), []),
  getTicketWatchers: async () => null,
  getTicketTree: async () => null,
  listTickets: async () => ({ results: [] })
}));
vi.mock('#lib/server/v2/timesheet.js', () => ({
  listTicketTime: async () => (calls.push('time'), [])
}));
vi.mock('#lib/server/v2/approvals.js', () => ({ listTicketApprovals: async () => [] }));
vi.mock('#lib/server/v2/macros.js', () => ({ listUsableMacros: async () => [] }));
vi.mock('#lib/server/v2/organization.js', () => ({ getOrgSettings: async () => null }));
vi.mock('#lib/server/v2/org-people.js', () => ({
  getOrgPeopleAndTeams: async () => ({ people: [] })
}));
vi.mock('#lib/server/v2/related-records.js', () => ({
  loadRelated: async () => null,
  relatedActions: () => ({})
}));

const { load } = await import('./+page.server.js');

const event = () =>
  /** @type {any} */ ({
    cookies: {},
    params: { id: 't1' },
    locals: { user: { id: 'u1' } },
    url: new URL('http://x/tickets/t1')
  });

beforeEach(() => {
  calls.length = 0;
  off.value = [];
  off.unreadable = false;
});

describe('ticket load', () => {
  it('asks for both while the modules are on', async () => {
    const data = /** @type {any} */ (await load(event()));
    expect(calls.sort()).toEqual(['articles', 'time']);
    expect(data.modules).toHaveLength(3);
  });

  it('treats an unreadable module list as every module on, and returns null', async () => {
    off.unreadable = true;
    const data = /** @type {any} */ (await load(event()));
    expect(calls.sort()).toEqual(['articles', 'time']);
    expect(data.modules).toBeNull();
  });

  it('does not ask for time entries while Timesheet is off, nor articles while the knowledge base is off', async () => {
    off.value = ['timesheet', 'knowledge_base'];
    const data = /** @type {any} */ (await load(event()));
    expect(calls).toEqual([]);
    expect(data.time.entries).toBeNull();
    expect(data.articlePicker.candidates).toBeNull();
    expect(data.modules.filter((/** @type {any} */ m) => !m.available)).toHaveLength(2);
  });
});
