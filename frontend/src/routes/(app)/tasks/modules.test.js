import { describe, it, expect, vi, beforeEach } from 'vitest';

const off = { value: /** @type {string[]} */ ([]), unreadable: false };
const sent = vi.hoisted(() => ({ values: /** @type {any} */ (undefined) }));
const task = vi.hoisted(() => ({ related: /** @type {any} */ (null) }));
const calls = vi.hoisted(() => /** @type {string[]} */ ([]));

vi.mock('#lib/server/v2/modules.js', () => ({
  getModules: async () =>
    off.unreadable
      ? null
      : {
          canEdit: false,
          modules: ['deals', 'tickets', 'leads'].map((key) => ({
            key,
            label: key,
            available: !off.value.includes(key)
          }))
        }
}));
vi.mock('#lib/server/v2/tasks.js', () => ({
  getTaskFormOptions: async () => ({ owners: [], accounts: [] }),
  getTask: async () => ({ task: { id: 'k1', title: 'x', related: task.related } }),
  createTask: async () => ({}),
  updateTask: async (
    /** @type {any} */ _e,
    /** @type {string} */ _id,
    /** @type {any} */ values
  ) => {
    sent.values = values;
    return {};
  }
}));
vi.mock('#lib/server/v2/tickets.js', () => ({
  listTickets: async () => (calls.push('tickets'), { results: [] })
}));
vi.mock('#lib/server/v2/deals.js', () => ({
  listDeals: async () => (calls.push('deals'), { results: [] })
}));
vi.mock('#lib/server/v2/leads.js', () => ({
  listLeads: async () => (calls.push('leads'), { results: [] })
}));

const { actions } = await import('./[id]/edit/+page.server.js');
const saveEdit = /** @type {any} */ (actions).save;
const forms = {
  new: (await import('./new/+page.server.js')).load,
  edit: (await import('./[id]/edit/+page.server.js')).load
};
const event = () => /** @type {any} */ ({ cookies: {}, params: { id: 'k1' }, locals: {} });

beforeEach(() => {
  calls.length = 0;
  off.value = [];
  off.unreadable = false;
  task.related = null;
});

describe.each(['new', 'edit'])('task form load (%s)', (which) => {
  it('asks for every picker while the modules are on', async () => {
    const data = await /** @type {any} */ (forms)[which](event());
    expect(calls.sort()).toEqual(['deals', 'leads', 'tickets']);
    expect(data.modules).toHaveLength(3);
  });

  it('treats an unreadable module list as every module on, and returns null', async () => {
    off.unreadable = true;
    const data = await /** @type {any} */ (forms)[which](event());
    expect(calls.sort()).toEqual(['deals', 'leads', 'tickets']);
    expect(data.modules).toBeNull();
  });

  it('does not load deals, tickets or leads while their modules are off', async () => {
    off.value = ['deals', 'tickets', 'leads'];
    const data = await /** @type {any} */ (forms)[which](event());
    expect(calls).toEqual([]);
    expect(data.parents.opportunity).toEqual([]);
    expect(data.parents.case).toEqual([]);
    expect(data.parents.lead).toEqual([]);
    expect(data.modules.every((/** @type {any} */ m) => !m.available)).toBe(true);
  });
});

describe('task edit with the deal link hidden', () => {
  it('loads with no deal kind, and saving sends no parent change', async () => {
    off.value = ['deals'];
    // The API answers null for the hidden deal, so no related record arrives.
    task.related = null;
    const data = await /** @type {any} */ (forms).edit(event());
    expect(data.form.parent_kind).toBe('');
    expect(data.form.parent_id).toBe('');

    const body = new FormData();
    body.set('title', 'x');
    body.set('parent_kind', '');
    body.set('parent_kind_original', data.form.parent_kind);
    body.set('parent_id_original', data.form.parent_id);
    const result = await saveEdit(
      /** @type {any} */ ({
        cookies: {},
        params: { id: 'k1' },
        request: { formData: async () => body }
      })
    ).catch((/** @type {any} */ e) => e);
    expect(sent.values).toBeDefined();
    expect(Object.keys(sent.values)).not.toEqual(expect.arrayContaining(['opportunity']));
    expect('case' in sent.values || 'lead' in sent.values || 'account' in sent.values).toBe(false);
    expect(result.status).toBe(303);
  });
});
