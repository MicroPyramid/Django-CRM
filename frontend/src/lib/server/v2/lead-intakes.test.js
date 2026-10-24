import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const {
  listIntakes,
  getIntake,
  createIntake,
  updateIntake,
  deleteIntake,
  replaceIntakeKey,
  testIntake,
  intakeBody,
  intakesSummary
} = await import('./lead-intakes.js');

const jwt = (/** @type {Record<string, unknown>} */ claims) =>
  `x.${Buffer.from(JSON.stringify(claims)).toString('base64url')}.y`;
const asAdmin = /** @type {any} */ ({
  cookies: { get: () => jwt({ is_organization_admin: true }) }
});
const asMember = /** @type {any} */ ({ cookies: { get: () => jwt({}) } });

const ID = '0b9f4c6e-3f0a-4a5b-9a77-1c2d3e4f5a6b';
const KEY = 'lk_9f8e7d6c5b4a39281706f5e4d3c2b1a0';
const status = (/** @type {number} */ n, /** @type {any} */ body = {}) =>
  Object.assign(new Error('failed'), { status: n, body });

const INTAKE = {
  id: ID,
  name: 'Google Ads',
  preset: 'google_ads',
  url: `https://api.example.test/api/public/leads/${ID}/`,
  key_hint: 'b1a0',
  mapping: [{ from: 'user_column_data.EMAIL', to: 'email' }],
  default_source: 'google ads',
  source_detail: 'Spring campaign',
  tags: [{ id: 't1', name: 'Ads' }],
  assignee: 'p1',
  is_active: true,
  last_received_at: null,
  last_error: '',
  created_at: '2026-10-24T10:00:00Z'
};

beforeEach(() => {
  apiRequest.mockReset();
});

describe('the key', () => {
  it('comes back from a create once, with the URL to post to', async () => {
    apiRequest.mockResolvedValueOnce({ ...INTAKE, key: KEY });
    const created = await createIntake(asAdmin, { name: 'Google Ads', preset: 'google_ads' });
    expect(created).toEqual({ id: ID, name: 'Google Ads', url: INTAKE.url, key: KEY });
  });

  it('never reaches the detail page, even when a read carries it', async () => {
    apiRequest.mockImplementation(async (/** @type {string} */ path) =>
      path.endsWith('/deliveries/') ? { deliveries: [] } : { ...INTAKE, key: KEY }
    );
    const detail = /** @type {any} */ (await getIntake(asAdmin, ID));
    expect(detail.intake.key_hint).toBe('b1a0');
    expect('key' in detail.intake).toBe(false);
    expect(JSON.stringify(detail)).not.toContain(KEY);
  });

  it('never reaches the list either', async () => {
    apiRequest.mockResolvedValueOnce({ intakes: [{ ...INTAKE, key: KEY }] });
    const list = await listIntakes(asAdmin);
    expect(JSON.stringify(list)).not.toContain(KEY);
  });

  it('comes back from a replace once', async () => {
    apiRequest.mockResolvedValueOnce({ key: KEY, key_hint: 'b1a0' });
    expect(await replaceIntakeKey(asAdmin, ID)).toEqual({ key: KEY });
    expect(apiRequest).toHaveBeenCalledWith(
      `/leads/intakes/${ID}/key/`,
      { method: 'POST' },
      { cookies: asAdmin.cookies }
    );
  });

  it('is never sent up, whatever the values hold', () => {
    const body = intakeBody({
      name: 'X',
      key: 'chosen',
      url: 'https://evil.test',
      id: 'other',
      org: 'other-org'
    });
    expect(body).toEqual({ name: 'X' });
  });
});

describe('listIntakes', () => {
  it('reads the list from any list shape', async () => {
    apiRequest.mockResolvedValueOnce({ intakes: [INTAKE] });
    expect((await listIntakes(asAdmin)).intakes[0].tags).toEqual(['t1']);
    apiRequest.mockResolvedValueOnce([INTAKE]);
    expect((await listIntakes(asAdmin)).intakes).toHaveLength(1);
    apiRequest.mockResolvedValueOnce({ results: [INTAKE] });
    expect((await listIntakes(asAdmin)).state).toBe('ok');
  });

  it('folds a member’s 403, an older API’s 404 and a failure into states', async () => {
    apiRequest.mockRejectedValueOnce(status(403));
    expect(await listIntakes(asMember)).toEqual({ state: 'forbidden', intakes: [] });
    apiRequest.mockRejectedValueOnce(status(404));
    expect(await listIntakes(asAdmin)).toEqual({ state: 'absent', intakes: [] });
    apiRequest.mockRejectedValueOnce(status(500));
    expect(await listIntakes(asAdmin)).toEqual({ state: 'failed', intakes: [] });
  });
});

describe('getIntake', () => {
  it('answers the deliveries beside the intake, and survives their failure', async () => {
    apiRequest.mockImplementation(async (/** @type {string} */ path) => {
      if (path.endsWith('/deliveries/')) {
        return [{ id: 'd1', received_at: 'x', result: 'created', lead: { id: 'l1' } }];
      }
      return INTAKE;
    });
    const detail = /** @type {any} */ (await getIntake(asAdmin, ID));
    expect(detail.deliveries).toEqual([
      { id: 'd1', received_at: 'x', result: 'created', lead: 'l1', external_id: '', error: '' }
    ]);

    apiRequest.mockImplementation(async (/** @type {string} */ path) => {
      if (path.endsWith('/deliveries/')) throw status(500);
      return INTAKE;
    });
    const without = /** @type {any} */ (await getIntake(asAdmin, ID));
    expect(without.deliveries).toEqual([]);
    expect(without.deliveriesFailed).toBe(true);
  });

  it('answers a page 404 for another org’s or a missing id, and forbidden for a member', async () => {
    apiRequest.mockImplementation(async (/** @type {string} */ path) => {
      if (path.endsWith('/deliveries/')) return [];
      throw status(404);
    });
    await expect(getIntake(asAdmin, ID)).rejects.toMatchObject({
      status: 404,
      body: { message: 'That webhook does not exist.' }
    });

    apiRequest.mockImplementation(async () => {
      throw status(403);
    });
    expect(await getIntake(asMember, ID)).toEqual({ forbidden: true });
  });

  it('refuses a malformed id without asking', async () => {
    await expect(getIntake(asAdmin, 'nope')).rejects.toMatchObject({ status: 404 });
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('names the owner from assignee_details, so a deactivated one keeps their name', async () => {
    /** @param {any} details */
    const read = async (details) => {
      apiRequest.mockImplementation(async (/** @type {string} */ path) =>
        path.endsWith('/deliveries/')
          ? { deliveries: [] }
          : { ...INTAKE, assignee_details: details }
      );
      return /** @type {any} */ (await getIntake(asAdmin, ID)).intake;
    };
    const gone = { id: 'p1', email: 'sam@acme.test', name: 'Sam Lee', is_active: false };

    expect(await read(gone)).toMatchObject({ assignee: 'p1', assignee_name: 'Sam Lee' });
    expect((await read({ ...gone, name: '' })).assignee_name).toBe('sam@acme.test');
    expect((await read(null)).assignee_name).toBeNull();
  });
});

describe('writes', () => {
  it('cleans the mapping and the pickers before sending', async () => {
    apiRequest.mockResolvedValueOnce({});
    await updateIntake(asAdmin, ID, {
      mapping: [
        { from: ' data.email ', to: 'email', extra: 1 },
        { from: '', to: 'phone' },
        { from: 'data.x', to: '' }
      ],
      tags: ['t1', ''],
      assignee: '',
      is_active: 'true',
      default_source: ' web form ',
      source_detail: ' Spring '
    });
    expect(apiRequest).toHaveBeenCalledWith(
      `/leads/intakes/${ID}/`,
      {
        method: 'PATCH',
        body: {
          mapping: [{ from: 'data.email', to: 'email' }],
          tags: ['t1'],
          assignee: null,
          is_active: false,
          default_source: 'web form',
          source_detail: 'Spring'
        }
      },
      { cookies: asAdmin.cookies }
    );
  });

  it('refuses a blank name before asking', async () => {
    await expect(createIntake(asAdmin, { name: '  ' })).rejects.toThrow('A webhook needs a name.');
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('deletes and tests by id', async () => {
    apiRequest.mockResolvedValue(null);
    await deleteIntake(asAdmin, ID);
    await testIntake(asAdmin, ID);
    expect(apiRequest.mock.calls.map((c) => [c[0], c[1].method])).toEqual([
      [`/leads/intakes/${ID}/`, 'DELETE'],
      [`/leads/intakes/${ID}/test/`, 'POST']
    ]);
  });
});

describe('intakesSummary', () => {
  it('asks only for an admin', async () => {
    expect(await intakesSummary(asMember)).toBeNull();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('counts, false without the API, null on failure', async () => {
    apiRequest.mockResolvedValueOnce({ intakes: [INTAKE, { ...INTAKE, is_active: false }] });
    expect(await intakesSummary(asAdmin)).toEqual({ count: 2, active: 1 });
    apiRequest.mockRejectedValueOnce(status(404));
    expect(await intakesSummary(asAdmin)).toBe(false);
    apiRequest.mockRejectedValueOnce(status(500));
    expect(await intakesSummary(asAdmin)).toBeNull();
  });
});
