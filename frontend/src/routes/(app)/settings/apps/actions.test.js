import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const mod = /** @type {any} */ (await import('./+page.server.js'));
const { load, actions } = mod;

const cookies = /** @type {any} */ ({ get: () => undefined });

/** @param {string} key @param {string} group @param {Record<string, any>} [more] */
const row = (key, group, more = {}) => ({
  key,
  label: key,
  group,
  covers: '',
  stops: '',
  enabled: true,
  available: true,
  needs: null,
  ...more
});

const ROWS = [
  row('deals', 'sell'),
  row('leads', 'sell'),
  row('goals', 'sell', { needs: 'deals' }),
  row('tasks', 'serve'),
  row('tickets', 'serve', { enabled: false, available: false }),
  row('invoices', 'bill')
];

const APPS = [
  {
    id: 'real-estate',
    name: 'Real Estate',
    description: 'Listings and viewings',
    version: 2,
    status: 'installed',
    installed_version: 1,
    update_available: true,
    skipped_modules: ['tickets'],
    installed_at: '2026-10-01T10:00:00Z',
    installed_by_details: { id: 'p1', name: 'Asha' }
  },
  {
    id: 'events-weddings',
    name: 'Events and Weddings',
    description: '',
    version: 1,
    status: 'not_installed',
    installed_version: null,
    update_available: false,
    skipped_modules: [],
    installed_at: null,
    installed_by_details: null
  }
];

const PREVIEW = {
  action: 'install',
  items: [
    { type: 'tag', target: null, label: 'VIP', effect: 'keep' },
    { type: 'field', target: 'lead', label: 'Budget', effect: 'add' },
    { type: 'wording', target: null, label: 'Deals will be called Engagements', effect: 'add' },
    { type: 'field', target: 'lead', label: 'Venue', effect: 'skipped_module' },
    { type: 'stage', target: 'lead', label: 'Site visit', effect: 'add_by_hand' }
  ],
  sample_data: { offered: true, default_on: false, records: 58 }
};

const failure = (/** @type {number} */ status, body = {}) =>
  Object.assign(new Error('x'), { status, body });

/**
 * @param {Record<string, string>} fields
 * @param {string} [query]
 */
function event(fields, query = '') {
  const body = new FormData();
  for (const [key, value] of Object.entries(fields)) body.set(key, value);
  return /** @type {any} */ ({
    request: new Request('http://test/settings/apps', { method: 'POST', body }),
    url: new URL(`http://test/settings/apps${query}`),
    cookies
  });
}

/**
 * @param {{ canEdit?: boolean, apps?: 'ok' | 404 | 500, preview?: any }} [opts]
 */
function serve({ canEdit = true, apps = 'ok', preview = PREVIEW } = {}) {
  apiRequest.mockImplementation(async (path, options) => {
    if (path === '/org/modules/') {
      return options?.method === 'PUT'
        ? { modules: ROWS, can_edit: true }
        : { modules: ROWS, can_edit: canEdit };
    }
    if (path === '/apps/') {
      if (apps !== 'ok') throw failure(apps);
      return { apps: APPS };
    }
    if (path.includes('/preview/')) {
      if (preview instanceof Error) throw preview;
      return preview;
    }
    if (options?.method === 'POST') return { app: APPS[0] };
    if (options?.method === 'DELETE') return { deleted: 3, retained_by_type: { account: 1 } };
    throw failure(404);
  });
}

const puts = () => apiRequest.mock.calls.filter((c) => c[1]?.method === 'PUT');
const posts = () => apiRequest.mock.calls.filter((c) => c[1]?.method === 'POST');

/** @param {() => Promise<any>} run */
async function redirectOf(run) {
  try {
    await run();
  } catch (/** @type {any} */ thrown) {
    return thrown;
  }
  throw new Error('expected a redirect');
}

beforeEach(() => {
  apiRequest.mockReset();
});

describe('load', () => {
  it('answers the apps and the module rows for an admin', async () => {
    serve();
    const data = await load(event({}));
    expect(data.modules).toEqual(ROWS);
    expect(data.modulesFailed).toBe(false);
    expect(data.apps.state).toBe('ok');
    expect(data.apps.apps.map((/** @type {any} */ a) => a.id)).toEqual([
      'real-estate',
      'events-weddings'
    ]);
    expect(data.apps.apps[0]).toMatchObject({
      status: 'installed',
      installedVersion: 1,
      updateAvailable: true,
      skippedModules: ['tickets'],
      installedBy: 'Asha'
    });
    expect(data.confirm).toBeNull();
  });

  it('hides the apps section on an API without apps and keeps Modules working', async () => {
    serve({ apps: 404 });
    const data = await load(event({}));
    expect(data.apps).toEqual({ state: 'absent', apps: [] });
    expect(data.modules).toEqual(ROWS);

    const result = await actions.switch(event({ key: 'leads', on: 'false' }));
    expect(result).toEqual({ saved: true });
    expect(puts()).toHaveLength(1);
  });

  it('says the apps failed on any other error', async () => {
    serve({ apps: 500 });
    expect((await load(event({}))).apps.state).toBe('failed');
  });

  it('shows a member the admins-only notice and does not write for one', async () => {
    serve({ canEdit: false });
    expect(await load(event({}))).toEqual({ forbidden: true });
    const result = await actions.switch(event({ key: 'tasks', on: 'false' }));
    expect(result.status).toBe(403);
    expect(puts()).toHaveLength(0);
  });

  it('marks the modules failed when the list cannot be read', async () => {
    apiRequest.mockImplementation(async (path) => {
      if (path === '/apps/') return { apps: APPS };
      throw new Error('down');
    });
    // No modules answer and no admin claim on the token: the page refuses.
    expect(await load(event({}))).toEqual({ forbidden: true });
  });

  it('opens the confirmation with the preview grouped by type', async () => {
    serve();
    const data = await load(event({}, '?app=events-weddings&do=install'));
    expect(apiRequest.mock.calls.map((c) => c[0])).toContain(
      '/apps/events-weddings/preview/?action=install'
    );
    expect(data.confirm.error).toBe('');
    const groups = data.confirm.preview.groups;
    expect(groups.map((/** @type {any} */ g) => g.label)).toEqual([
      'Wording',
      'Fields',
      'Stages',
      'Tags'
    ]);
    expect(groups[1].items).toEqual([
      { label: 'Budget', target: 'leads', effect: 'add', effectLabel: 'Will add' },
      {
        label: 'Venue',
        target: 'leads',
        effect: 'skipped_module',
        effectLabel: 'Skipped while its module is off'
      }
    ]);
    expect(groups[2].items[0].effectLabel).toBe('Not added: add this stage by hand');
    expect(data.confirm.preview.sampleData).toEqual({
      offered: true,
      defaultOn: false,
      records: 58
    });
  });

  it('asks for no preview for an app or action it does not know', async () => {
    serve();
    expect((await load(event({}, '?app=crm&do=install'))).confirm).toBeNull();
    expect((await load(event({}, '?app=real-estate&do=wipe'))).confirm).toBeNull();
    expect(apiRequest.mock.calls.some((c) => String(c[0]).includes('/preview/'))).toBe(false);
  });

  it('puts a refused preview on the confirmation', async () => {
    serve({ preview: failure(403) });
    const data = await load(event({}, '?app=real-estate&do=remove'));
    expect(data.confirm).toMatchObject({
      app: 'real-estate',
      action: 'remove',
      preview: null,
      error: 'Only an organization admin can remove an app.'
    });
  });

  it('names what was done after an action lands', async () => {
    serve();
    const data = await load(event({}, '?done=install&app=real-estate'));
    expect(data.done).toEqual({ action: 'install', app: 'real-estate' });
    expect((await load(event({}, '?done=wipe&app=real-estate'))).done).toBeNull();
  });
});

describe('app actions', () => {
  it('installs with the sample data choice, sending false when unticked', async () => {
    serve();
    const ticked = await redirectOf(() =>
      actions.install(event({ app: 'events-weddings', sample_data: 'on' }))
    );
    expect(ticked).toMatchObject({
      status: 303,
      location: '/settings/apps?done=install&app=events-weddings'
    });
    await redirectOf(() => actions.install(event({ app: 'events-weddings' })));
    expect(posts().map((c) => [c[0], c[1].body])).toEqual([
      ['/apps/events-weddings/install/', { sample_data: true }],
      ['/apps/events-weddings/install/', { sample_data: false }]
    ]);
  });

  it('updates and removes through their own endpoints', async () => {
    serve();
    await redirectOf(() => actions.upgrade(event({ app: 'real-estate' })));
    await redirectOf(() => actions.remove(event({ app: 'real-estate' })));
    expect(posts().map((c) => c[0])).toEqual([
      '/apps/real-estate/upgrade/',
      '/apps/real-estate/remove/'
    ]);
  });

  it("returns the server's reason for a refused action and keeps the confirmation", async () => {
    apiRequest.mockRejectedValueOnce(
      failure(409, { error: true, errors: 'Nothing new to add in this version.' })
    );
    const result = await actions.upgrade(event({ app: 'real-estate' }));
    expect(result.status).toBe(409);
    expect(result.data).toEqual({
      appError: 'Nothing new to add in this version.',
      app: 'real-estate'
    });
  });

  it('tells a member only an admin can act', async () => {
    apiRequest.mockRejectedValueOnce(failure(403));
    const result = await actions.remove(event({ app: 'real-estate' }));
    expect(result.status).toBe(403);
    expect(result.data.appError).toBe('Only an organization admin can remove an app.');
  });

  it('never sends a malformed app id', async () => {
    serve();
    const result = await actions.install(event({ app: '../org' }));
    expect(result.status).toBe(400);
    expect(posts()).toHaveLength(0);
  });
});

describe('clear sample data', () => {
  it('reports what was deleted and what was kept', async () => {
    serve();
    expect(await actions.clearSampleData(event({}))).toEqual({ cleared: 3, retained: 1 });
    expect(apiRequest.mock.calls.at(-1)?.[0]).toBe('/packs/sample-data/');
  });

  it('tells a member only an admin can clear it', async () => {
    apiRequest.mockRejectedValueOnce(failure(403));
    const result = await actions.clearSampleData(event({}));
    expect(result.status).toBe(403);
  });
});

describe('switch', () => {
  it('switches a module off with the off list and the served order', async () => {
    serve();
    const result = await actions.switch(event({ key: 'leads', on: 'false' }));
    expect(result).toEqual({ saved: true });
    expect(puts()[0][1].body).toEqual({
      off: ['leads', 'tickets'],
      order: ROWS.map((r) => r.key)
    });
  });

  it('switches a module on by taking it out of the off list', async () => {
    serve();
    await actions.switch(event({ key: 'tickets', on: 'true' }));
    expect(puts()[0][1].body.off).toEqual([]);
  });

  it('returns every refusal and writes nothing else', async () => {
    apiRequest.mockImplementation(async (_path, options) => {
      if (options?.method === 'PUT') {
        throw Object.assign(new Error('bad'), { status: 400, body: { off: ['a', 'b'] } });
      }
      return { modules: ROWS, can_edit: true };
    });
    const result = await actions.switch(event({ key: 'leads', on: 'false' }));
    expect(result.status).toBe(400);
    expect(result.data).toEqual({ errors: ['a', 'b'], key: 'leads' });
    expect(puts()).toHaveLength(1);
  });

  it('refuses an unknown key or flag without a write', async () => {
    serve();
    expect((await actions.switch(event({ key: 'crm', on: 'false' }))).status).toBe(400);
    expect((await actions.switch(event({ key: 'leads', on: 'maybe' }))).status).toBe(400);
    expect(puts()).toHaveLength(0);
  });
});

describe('move', () => {
  it('moves a module and keeps the off list', async () => {
    serve();
    const result = await actions.move(event({ key: 'leads', direction: 'up' }));
    expect(result).toEqual({ saved: true });
    expect(puts()[0][1].body).toEqual({
      off: ['tickets'],
      order: ['leads', 'deals', 'goals', 'tasks', 'tickets', 'invoices']
    });
  });

  it('refuses a move past a group end or an unknown key without a write', async () => {
    serve();
    expect((await actions.move(event({ key: 'deals', direction: 'up' }))).status).toBe(400);
    expect((await actions.move(event({ key: 'tickets', direction: 'down' }))).status).toBe(400);
    expect((await actions.move(event({ key: 'crm', direction: 'up' }))).status).toBe(400);
    expect(puts()).toHaveLength(0);
  });
});

describe('/settings/modules', () => {
  it('redirects to the Apps page', async () => {
    const { GET } = /** @type {any} */ (await import('../modules/+server.js'));
    const thrown = await redirectOf(async () => GET());
    expect(thrown).toMatchObject({ status: 308, location: '/settings/apps' });
  });
});
