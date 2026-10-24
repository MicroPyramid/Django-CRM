import { describe, it, expect, vi } from 'vitest';

const calls = /** @type {string[]} */ ([]);
/** @param {string} name @param {any} value */
const stub = (name, value) =>
  vi.fn(async () => {
    calls.push(name);
    return value;
  });

vi.mock('./automation.js', () => ({ automationSummary: stub('automation', null) }));
vi.mock('./business-hours.js', () => ({
  getBusinessHours: stub('hours', { calendar: { days: [] } })
}));
vi.mock('./custom-fields.js', () => ({ getCustomFields: stub('fields', { totals: {} }) }));
vi.mock('./escalation.js', () => ({
  getEscalationPolicies: stub('escalation', { policies: [] })
}));
vi.mock('./help-center-settings.js', () => ({ getHelpCenterSettings: stub('help', { x: 1 }) }));
vi.mock('./inbound-email.js', () => ({
  getMailboxes: stub('mailboxes', { totals: {}, mailboxes: [] })
}));
vi.mock('./macros.js', () => ({ getMacros: stub('macros', { totals: {} }) }));
vi.mock('./organization.js', () => ({ getOrgSettings: stub('org', { org: { name: 'Acme' } }) }));
vi.mock('./reopen.js', () => ({
  getReopenPolicy: stub('reopen', { policy: { is_enabled: true } })
}));
vi.mock('./routing.js', () => ({ getRoutingRules: stub('routing', { totals: {} }) }));
vi.mock('./tags.js', () => ({ getTags: stub('tags', { totals: {} }) }));
vi.mock('./team.js', () => ({ listTeam: stub('team', { totals: {} }) }));
vi.mock('./ticket-approvals.js', () => ({
  getApprovalRules: stub('approvals', { rules: [], totals: {} })
}));
vi.mock('./tokens.js', () => ({ listOrgTokens: stub('tokens', { totals: {} }) }));
vi.mock('./web-forms.js', () => ({ getWebForms: stub('forms', { totals: {} }) }));
vi.mock('./lead-sources.js', () => ({
  leadSourcesSummary: stub('sources', { active: 15, count: 15 })
}));
vi.mock('./lead-intakes.js', () => ({ intakesSummary: stub('intakes', false) }));

const { getSettingsHub } = await import('./settings.js');
const { getRoutingRules } = await import('./routing.js');
const event = /** @type {any} */ ({ cookies: { get: () => undefined } });

const UNGATED = ['org', 'tokens', 'team', 'tags', 'fields', 'forms', 'automation', 'sources'];
const GATED = [
  'hours',
  'routing',
  'escalation',
  'mailboxes',
  'reopen',
  'approvals',
  'macros',
  'help',
  'intakes'
];

/** A promise and the function that settles it. */
function deferred() {
  /** @type {(value: any) => void} */
  let settle = () => {};
  const promise = new Promise((r) => (settle = r));
  return { promise, settle };
}

/** @param {string} key */
const off = (key) => [{ key, available: false }];

describe('getSettingsHub', () => {
  it('asks for everything when the list is missing', async () => {
    calls.length = 0;
    const hub = await getSettingsHub(event, null);
    expect(calls).toEqual(expect.arrayContaining(['hours', 'routing', 'macros', 'help']));
    expect(hub.helpCenter).toEqual({ x: 1 });
    expect(hub.leadSources).toEqual({ active: 15, count: 15 });
    expect(hub.leadIntakes).toBe(false);
  });

  it('skips the webhooks while Leads is off, but still counts the sources deals use', async () => {
    calls.length = 0;
    const hub = await getSettingsHub(event, /** @type {any} */ (off('leads')));
    expect(calls).not.toContain('intakes');
    expect(hub.leadIntakes).toBeNull();
    expect(hub.leadSources).toEqual({ active: 15, count: 15 });
  });

  it('asks for the mailboxes while Tickets or Leads is on, and skips them when both are off', async () => {
    calls.length = 0;
    const leadsOnly = await getSettingsHub(event, /** @type {any} */ (off('tickets')));
    expect(calls).toContain('mailboxes');
    expect(leadsOnly.mailboxTotals).not.toBeNull();

    calls.length = 0;
    const neither = await getSettingsHub(
      event,
      /** @type {any} */ ([...off('tickets'), ...off('leads')])
    );
    expect(calls).not.toContain('mailboxes');
    expect(neither.mailboxTotals).toBeNull();
  });

  it('skips the settings calls of off modules and still answers', async () => {
    calls.length = 0;
    const hub = await getSettingsHub(
      event,
      /** @type {any} */ ([...off('tickets'), ...off('leads'), ...off('knowledge_base')])
    );
    for (const name of [
      'hours',
      'routing',
      'escalation',
      'mailboxes',
      'reopen',
      'approvals',
      'macros',
      'help'
    ]) {
      expect(calls).not.toContain(name);
    }
    expect(hub).toMatchObject({
      calendar: null,
      routingTotals: null,
      escalationTotals: null,
      mailboxTotals: null,
      reopen: null,
      approvalRules: null,
      approvalTotals: null,
      macroTotals: null,
      helpCenter: null
    });
    expect(hub.org).toEqual({ name: 'Acme' });
  });

  it('starts every call that needs no module before the list answers', async () => {
    calls.length = 0;
    const list = deferred();
    const hub = getSettingsHub(event, list.promise);
    await Promise.resolve();
    expect([...calls].sort()).toEqual([...UNGATED].sort());
    list.settle(null);
    await hub;
    expect(calls).toEqual(expect.arrayContaining(GATED));
  });

  it("reads a gated call's module_off answer as null, and still throws any other failure", async () => {
    const off = Object.assign(new Error('Tickets is switched off for this organization.'), {
      status: 404,
      body: { code: 'module_off', module: 'tickets', detail: 'Tickets is switched off.' }
    });
    vi.mocked(getRoutingRules).mockRejectedValueOnce(off);
    const hub = await getSettingsHub(event, null);
    expect(hub.routingTotals).toBeNull();
    expect(hub.org).toEqual({ name: 'Acme' });

    vi.mocked(getRoutingRules).mockRejectedValueOnce(
      Object.assign(new Error('x'), { status: 500 })
    );
    await expect(getSettingsHub(event, null)).rejects.toMatchObject({ status: 500 });
  });
});

describe('the hub page load', () => {
  it('returns the read that decided the skipped calls, without holding the others for it', async () => {
    vi.resetModules();
    const rows = [{ key: 'tickets', available: false, enabled: false }];
    const read = deferred();
    vi.doMock('./modules.js', async (importOriginal) => ({
      ...(await importOriginal()),
      getModules: () => read.promise
    }));
    calls.length = 0;
    const { load } = await import('../../../routes/(app)/settings/+page.server.js');
    const pending = load(event);
    await Promise.resolve();
    expect(calls).toContain('org');
    read.settle({ modules: rows, canEdit: true });
    const hub = /** @type {any} */ (await pending);
    expect(hub.modules).toBe(rows);
    expect(calls).not.toContain('routing');
    expect(hub.routingTotals).toBeNull();
  });
});
