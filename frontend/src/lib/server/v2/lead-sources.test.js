import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const {
  getLeadSources,
  listSourcesForSettings,
  leadSourcesSummary,
  createLeadSource,
  updateLeadSource,
  orderLeadSources
} = await import('./lead-sources.js');
const { LEGACY_LEAD_SOURCES, sourceOptions } = await import('#lib/v2/lead-sources.js');

/** A JWT whose payload carries `claims`, for the admin display hint. */
const jwt = (/** @type {Record<string, unknown>} */ claims) =>
  `x.${Buffer.from(JSON.stringify(claims)).toString('base64url')}.y`;
const asAdmin = /** @type {any} */ ({
  cookies: { get: () => jwt({ is_organization_admin: true }) }
});
const asMember = /** @type {any} */ ({ cookies: { get: () => jwt({}) } });

const ID = '0b9f4c6e-3f0a-4a5b-9a77-1c2d3e4f5a6b';
const status = (/** @type {number} */ n, /** @type {any} */ body = {}) =>
  Object.assign(new Error('failed'), { status: n, body });

const SOURCES = {
  sources: [
    { id: 'b', key: 'google ads', label: 'Google ads', is_active: true, order: 2 },
    { id: 'a', key: 'call', label: 'Call', is_active: true, order: 1 },
    { id: 'c', key: 'fax', label: 'Fax', is_active: false, order: 3 }
  ]
};

beforeEach(() => {
  apiRequest.mockReset();
});

describe('getLeadSources', () => {
  it('answers the list in order, retired ones included', async () => {
    apiRequest.mockResolvedValueOnce(SOURCES);
    const { sources, live } = await getLeadSources(asMember);
    expect(live).toBe(true);
    expect(sources.map((s) => s.key)).toEqual(['call', 'google ads', 'fax']);
    expect(sources[2].is_active).toBe(false);
    expect(apiRequest).toHaveBeenCalledWith(
      '/leads/sources/',
      { quietErrors: true, expectedStatuses: [404] },
      { cookies: asMember.cookies }
    );
  });

  it('feeds a picker the active sources plus the record’s current retired one', async () => {
    apiRequest.mockResolvedValueOnce(SOURCES);
    const { sources } = await getLeadSources(asMember);
    const options = sourceOptions(sources, 'fax');
    expect(options.map((o) => o.key)).toEqual(['fax', 'call', 'google ads']);
    expect(options[0]).toEqual({ key: 'fax', label: 'Fax (retired)', retired: true });
    expect(sourceOptions(sources, 'call').map((o) => o.key)).toEqual(['call', 'google ads']);
  });

  it('falls back to the old fixed list where the API has none', async () => {
    apiRequest.mockRejectedValueOnce(status(404));
    const { sources, live } = await getLeadSources(asMember);
    expect(live).toBe(false);
    expect(sources).toBe(LEGACY_LEAD_SOURCES);
    expect(sources.map((s) => s.key)).toEqual([
      'call',
      'email',
      'existing customer',
      'partner',
      'public relations',
      'compaign',
      'other'
    ]);
  });

  it('answers an empty list, not the old one, when Leads is switched off or the read fails', async () => {
    apiRequest.mockRejectedValueOnce(status(404, { code: 'module_off' }));
    expect(await getLeadSources(asMember)).toEqual({ sources: [], live: false });
    apiRequest.mockRejectedValueOnce(status(500));
    expect(await getLeadSources(asMember)).toEqual({ sources: [], live: false });
  });
});

describe('listSourcesForSettings', () => {
  it('answers the list with the admin hint', async () => {
    apiRequest.mockResolvedValue(SOURCES);
    expect((await listSourcesForSettings(asAdmin)).canEdit).toBe(true);
    expect((await listSourcesForSettings(asMember)).canEdit).toBe(false);
  });

  it('turns a 404 into a page 404 saying the feature is not here', async () => {
    apiRequest.mockRejectedValueOnce(status(404));
    await expect(listSourcesForSettings(asAdmin)).rejects.toMatchObject({
      status: 404,
      body: { message: 'Lead sources are not available here.' }
    });
  });
});

describe('leadSourcesSummary', () => {
  it('counts active sources, false without the API, null on failure', async () => {
    apiRequest.mockResolvedValueOnce(SOURCES);
    expect(await leadSourcesSummary(asMember)).toEqual({ active: 2, count: 3 });
    apiRequest.mockRejectedValueOnce(status(404));
    expect(await leadSourcesSummary(asMember)).toBe(false);
    apiRequest.mockRejectedValueOnce(status(404, { code: 'module_off' }));
    expect(await leadSourcesSummary(asMember)).toBeNull();
    apiRequest.mockRejectedValueOnce(status(500));
    expect(await leadSourcesSummary(asMember)).toBeNull();
  });
});

describe('writes', () => {
  it('creates with the label alone, trimmed', async () => {
    apiRequest.mockResolvedValueOnce({});
    await createLeadSource(asAdmin, '  Spring fair ');
    expect(apiRequest).toHaveBeenCalledWith(
      '/leads/sources/',
      { method: 'POST', body: { label: 'Spring fair' } },
      { cookies: asAdmin.cookies }
    );
  });

  it('refuses a blank label before asking', async () => {
    await expect(createLeadSource(asAdmin, '   ')).rejects.toThrow('A source needs a name.');
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('sends only label and is_active on update, never the key', async () => {
    apiRequest.mockResolvedValue({});
    await updateLeadSource(asAdmin, ID, /** @type {any} */ ({ is_active: false, key: 'x' }));
    expect(apiRequest.mock.calls[0]).toEqual([
      `/leads/sources/${ID}/`,
      { method: 'PATCH', body: { is_active: false } },
      { cookies: asAdmin.cookies }
    ]);
    await updateLeadSource(asAdmin, ID, { label: ' Fairs ' });
    expect(apiRequest.mock.calls[1][1].body).toEqual({ label: 'Fairs' });
  });

  it('refuses a malformed id without asking', async () => {
    await expect(updateLeadSource(asAdmin, '../x', { is_active: true })).rejects.toMatchObject({
      status: 404
    });
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('posts the whole order as keys', async () => {
    apiRequest.mockResolvedValueOnce({});
    await orderLeadSources(asAdmin, ['call', 'fax']);
    expect(apiRequest).toHaveBeenCalledWith(
      '/leads/sources/order/',
      { method: 'POST', body: { keys: ['call', 'fax'] } },
      { cookies: asAdmin.cookies }
    );
  });
});
