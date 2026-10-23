import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const {
  getModules,
  putModules,
  switchBody,
  moveBody,
  moduleErrors,
  moduleGuard,
  moduleOffError,
  rethrowModuleOff,
  moduleOffDetail
} = await import('#lib/server/v2/modules.js');
const { forwardCsvExport } = await import('#lib/server/v2/csv-export.js');
const { streamDownload } = await import('#lib/server/v2/files.js');
const { forwardStatementPdf } = await import('#lib/server/v2/statements.js');
const timeExport = await import('../../../routes/api/time-entries/report/export/+server.js');
const invoicePdf = await import('../../../routes/(app)/invoices/[id]/pdf/+server.js');

const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });

/** @type {[string, string][]} */
const LAYOUT = [
  ['deals', 'sell'],
  ['leads', 'sell'],
  ['goals', 'sell'],
  ['tasks', 'serve'],
  ['tickets', 'serve'],
  ['knowledge_base', 'serve'],
  ['documents', 'serve'],
  ['invoices', 'bill'],
  ['timesheet', 'bill']
];
const rows = (/** @type {string[]} */ off = []) =>
  /** @type {any[]} */ (
    LAYOUT.map(([key, group]) => ({
      key,
      group,
      label: key,
      enabled: !off.includes(key),
      available: !off.includes(key)
    }))
  );
const ALL = LAYOUT.map(([k]) => k);

const failure = (/** @type {number} */ status, body = {}) =>
  Object.assign(new Error('x'), { status, body });

describe('modules API', () => {
  beforeEach(() => apiRequest.mockReset());

  it('reads the list quietly and keeps rows and can_edit', async () => {
    apiRequest.mockResolvedValue({ modules: rows(), can_edit: true });
    const answer = await getModules(event);
    expect(apiRequest).toHaveBeenCalledWith(
      '/org/modules/',
      { quietErrors: true, expectedStatuses: [404] },
      event
    );
    expect(answer?.canEdit).toBe(true);
    expect(answer?.modules).toHaveLength(9);
  });

  it('answers null for the module list on 404, 500 and a network error', async () => {
    for (const err of [failure(404), failure(500), new Error('offline')]) {
      apiRequest.mockRejectedValueOnce(err);
      expect(await getModules(event)).toBeNull();
    }
  });

  it('reads once per request, shared by every load that passes the same locals', async () => {
    apiRequest.mockResolvedValue({ modules: rows(), can_edit: true });
    const locals = {};
    const shell = { cookies: event.cookies, locals };
    const guard = { cookies: event.cookies, locals, route: { id: '/(app)/tickets' } };
    const [a, b] = await Promise.all([getModules(shell), getModules(guard)]);
    expect(a).toBe(b);
    expect(apiRequest).toHaveBeenCalledTimes(1);
    await getModules({ cookies: event.cookies, locals: {} });
    expect(apiRequest).toHaveBeenCalledTimes(2);
  });

  it('shares a failed read as null within the request', async () => {
    apiRequest.mockRejectedValueOnce(failure(500));
    const req = { cookies: event.cookies, locals: {} };
    expect(await getModules(req)).toBeNull();
    expect(await getModules(req)).toBeNull();
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });

  it('reads again after a save in the same request', async () => {
    const req = { cookies: event.cookies, locals: {} };
    apiRequest.mockResolvedValueOnce({ modules: rows(), can_edit: true });
    await getModules(req);
    apiRequest.mockResolvedValueOnce({ modules: rows(['goals']), can_edit: true });
    await putModules(req, { off: ['goals'], order: ALL });
    apiRequest.mockResolvedValueOnce({ modules: rows(['goals']), can_edit: true });
    const after = await getModules(req);
    expect(after?.modules.find((m) => m.key === 'goals')?.enabled).toBe(false);
    expect(apiRequest).toHaveBeenCalledTimes(3);
  });

  it('sends exactly off and order on save, and throws what the API throws', async () => {
    apiRequest.mockResolvedValue({ modules: rows(), can_edit: true });
    await putModules(event, { off: ['goals'], order: ALL });
    expect(apiRequest).toHaveBeenCalledWith(
      '/org/modules/',
      { method: 'PUT', body: { off: ['goals'], order: ALL } },
      event
    );
    apiRequest.mockRejectedValueOnce(failure(400));
    let thrown;
    try {
      await putModules(event, { off: [], order: [] });
    } catch (e) {
      thrown = e;
    }
    expect(thrown.status).toBe(400);
  });

  it('switches one module and sends the served order', () => {
    expect(switchBody(rows(['goals']), 'tickets', false)).toEqual({
      off: ['goals', 'tickets'],
      order: ALL
    });
    expect(switchBody(rows(['goals', 'tickets']), 'goals', true)).toEqual({
      off: ['tickets'],
      order: ALL
    });
    expect(switchBody(rows(), 'crm', false)).toBeNull();
  });

  it('moves a module within its group and stops at the ends', () => {
    expect(moveBody(rows(['goals']), 'leads', 'up')).toEqual({
      off: ['goals'],
      order: ['leads', 'deals', 'goals', ...ALL.slice(3)]
    });
    expect(moveBody(rows(), 'deals', 'up')).toBeNull();
    expect(moveBody(rows(), 'goals', 'down')).toBeNull();
    expect(moveBody(rows(), 'tasks', 'up')).toBeNull();
    expect(moveBody(rows(), 'invoices', 'down')?.order.slice(7)).toEqual(['timesheet', 'invoices']);
    expect(moveBody(rows(), 'crm', 'up')).toBeNull();
    expect(moveBody(rows(), 'leads', 'sideways')).toBeNull();
  });

  it('lists every refusal message, off first then order', () => {
    expect(
      moduleErrors(failure(400, { order: ['Name each module once.'], off: ['A', 'B'] }))
    ).toEqual(['A', 'B', 'Name each module once.']);
    expect(moduleErrors(failure(403, { error: true, errors: 'Only admins can.' }))).toEqual([
      'Only admins can.'
    ]);
    expect(moduleErrors(failure(403, { detail: 'No org.' }))).toEqual(['No org.']);
    expect(moduleErrors(new Error('offline'))).toEqual(['offline']);
    expect(moduleErrors(failure(500, {}))).toHaveLength(1);
  });
});

const OFF_DETAIL = 'Tickets is switched off for this organization.';
const OFF_BODY = { detail: OFF_DETAIL, code: 'module_off', module: 'tickets' };

/** What a call threw, or undefined when it returned. */
function caught(/** @type {() => unknown} */ fn) {
  try {
    fn();
  } catch (e) {
    return e;
  }
  return undefined;
}

describe('the module guard', () => {
  /** The guard asks for the list itself; `parent()` would rerun the whole shell. */
  const parent = vi.fn(() => {
    throw new Error('parent() was called');
  });
  const guardEvent = (/** @type {string} */ id) =>
    /** @type {any} */ ({ route: { id }, cookies: event.cookies, parent });
  /** @param {any[]} modules */
  const serve = (modules) => apiRequest.mockResolvedValue({ modules, can_edit: false });

  beforeEach(() => {
    apiRequest.mockReset();
    parent.mockClear();
  });

  it('throws the module error for a route of an off module, with its label', async () => {
    serve(
      rows(['tickets', 'invoices']).map((r) => (r.key === 'tickets' ? { ...r, label: 'Cases' } : r))
    );
    const guarded = guardEvent('/(app)/tickets/[id]');
    await expect(moduleGuard(guarded)).rejects.toMatchObject({
      status: 404,
      body: {
        message: 'Cases is switched off for this organization.',
        code: 'module_off',
        module: 'tickets',
        label: 'Cases'
      }
    });
    expect(apiRequest).toHaveBeenCalledTimes(1);
    expect(apiRequest).toHaveBeenCalledWith(
      '/org/modules/',
      { quietErrors: true, expectedStatuses: [404] },
      guarded
    );
    for (const id of ['/(app)/settings/routing', '/(app)/accounts/[id]/statement']) {
      await expect(moduleGuard(guardEvent(id))).rejects.toMatchObject({
        status: 404,
        body: { code: 'module_off' }
      });
    }
    serve(rows(['deals', 'invoices']));
    await expect(moduleGuard(guardEvent('/(app)/invoices/products'))).rejects.toMatchObject({
      body: { module: 'invoices', label: 'invoices' }
    });
  });

  it('passes core routes and routes of modules that are on', async () => {
    serve(rows(['tickets', 'invoices']));
    for (const id of [
      '/(app)',
      '/(app)/accounts/[id]',
      '/(app)/profile',
      '/(app)/settings',
      '/(app)/settings/tags',
      '/(app)/leads/[id]',
      '/(app)/invoices/products/new'
    ]) {
      expect(await moduleGuard(guardEvent(id))).toEqual({});
    }
  });

  it('makes no request for a core route', async () => {
    serve(rows(ALL));
    for (const id of [
      '/(app)',
      '/(app)/accounts/[id]',
      '/(app)/profile/tokens',
      '/(app)/settings'
    ]) {
      expect(await moduleGuard(guardEvent(id))).toEqual({});
    }
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('never reads the parent layout', async () => {
    serve(rows(['tickets']));
    await expect(moduleGuard(guardEvent('/(app)/tickets'))).rejects.toMatchObject({
      body: { code: 'module_off' }
    });
    expect(await moduleGuard(guardEvent('/(app)/leads'))).toEqual({});
    expect(await moduleGuard(guardEvent('/(app)/accounts'))).toEqual({});
    expect(parent).not.toHaveBeenCalled();
  });

  it('passes everything when the module list is null', async () => {
    for (const err of [failure(404), failure(500), new Error('offline')]) {
      apiRequest.mockRejectedValue(err);
      for (const id of ['/(app)/tickets', '/(app)/settings/routing', '/(app)/invoices/products']) {
        expect(await moduleGuard(guardEvent(id))).toEqual({});
      }
    }
    apiRequest.mockResolvedValue({ detail: 'not a module list' });
    expect(await moduleGuard(guardEvent('/(app)/tickets'))).toEqual({});
  });
});

describe('a module_off from the API', () => {
  it('turns an API module_off into an error the page can show, and leaves other errors alone', () => {
    const off = failure(404, OFF_BODY);
    expect(moduleOffError(off)).toEqual({
      status: 404,
      message: OFF_DETAIL,
      code: 'module_off',
      module: 'tickets'
    });
    expect(caught(() => rethrowModuleOff(off))).toMatchObject({
      status: 404,
      body: { message: OFF_DETAIL, code: 'module_off', module: 'tickets' }
    });

    const others = [
      failure(404, { detail: 'Not found.' }),
      // A delete refusal is a form's message, not a page.
      failure(409, { error: true, errors: 'This account has 3 tickets.', code: 'module_off' }),
      failure(500),
      new Error('offline'),
      undefined,
      // The guard's own error, as `handleError` receives it, keeps its label.
      { status: 404, message: OFF_DETAIL, code: 'module_off', module: 'tickets', label: 'Tickets' }
    ];
    for (const err of others) {
      expect(moduleOffError(err)).toBeUndefined();
      expect(caught(() => rethrowModuleOff(err))).toBeUndefined();
    }
  });

  it('reads the detail of an upstream module_off and nothing else', async () => {
    const json = (/** @type {number} */ status, /** @type {any} */ body) =>
      new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json' }
      });
    expect(await moduleOffDetail(json(404, OFF_BODY))).toBe(OFF_DETAIL);
    expect(await moduleOffDetail(json(404, { detail: 'Not found.' }))).toBeNull();
    expect(await moduleOffDetail(json(403, OFF_BODY))).toBeNull();
    expect(await moduleOffDetail(json(200, OFF_BODY))).toBeNull();
    expect(await moduleOffDetail(new Response('<h1>Not Found</h1>', { status: 404 }))).toBeNull();
    expect(await moduleOffDetail(new Response(null, { status: 404 }))).toBeNull();
  });
});

describe('downloads and exports of an off module', () => {
  afterEach(() => vi.unstubAllGlobals());

  const download = () =>
    /** @type {any} */ ({
      cookies: { get: () => 'tok' },
      params: { id: 'id-1' },
      url: new URL('http://app.test/x'),
      request: new Request('http://app.test/x')
    });

  /** @type {[string, (event: any) => Response | Promise<Response>, string][]} */
  const ENDPOINTS = [
    [
      'a CSV export',
      (e) => forwardCsvExport(e, '/cases/export/', new URLSearchParams()),
      'Upstream error: 404'
    ],
    [
      'a file download',
      (e) => streamDownload(e, '/documents/1/download/'),
      'Could not download that file.'
    ],
    ['a statement PDF', (e) => forwardStatementPdf(e), 'Upstream error: 404'],
    ['the time report export', (e) => timeExport.GET(e), 'Upstream error: 404']
  ];

  it.each(ENDPOINTS)('%s answers the module message as its 404', async (_name, call, generic) => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => Response.json(OFF_BODY, { status: 404 }))
    );
    const off = await call(download());
    expect(off.status).toBe(404);
    expect(await off.text()).toBe(OFF_DETAIL);

    vi.stubGlobal(
      'fetch',
      vi.fn(async () => Response.json({ detail: 'Not found.' }, { status: 404 }))
    );
    const missing = await call(download());
    expect(missing.status).toBe(404);
    expect(await missing.text()).toBe(generic);
  });

  it('an invoice PDF answers the module message as its 404', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => Response.json(OFF_BODY, { status: 404 }))
    );
    const off = await invoicePdf.GET(download());
    expect(off.status).toBe(404);
    expect(await off.text()).toBe(OFF_DETAIL);

    vi.stubGlobal(
      'fetch',
      vi.fn(async () => Response.json({ detail: 'Not found.' }, { status: 404 }))
    );
    await expect(invoicePdf.GET(download())).rejects.toMatchObject({
      status: 404,
      body: { message: 'That invoice does not exist, or you do not have access to it.' }
    });
  });
});
