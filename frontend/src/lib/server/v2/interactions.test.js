import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const {
  listInteractions,
  interactionEvents,
  withInteractions,
  interactionBody,
  logInteraction,
  deleteInteraction,
  interactionActions,
  toInteraction
} = await import('./interactions.js');

const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });
const LEAD = '0b9f4c6e-3f0a-4a5b-9a77-1c2d3e4f5a6b';
const IX = '5d1e2f3a-4b5c-4d6e-8f70-819a2b3c4d5e';
const status = (/** @type {number} */ n, /** @type {any} */ body = {}) =>
  Object.assign(new Error('failed'), { status: n, body });

const CALL = {
  id: IX,
  kind: 'call',
  direction: 'outbound',
  occurred_at: '2026-10-24T09:12:00Z',
  duration_seconds: 240,
  duration_estimated: false,
  outcome: 'connected',
  subject: '',
  body: 'Wants a viewing on Saturday.',
  logged_by: 'p1',
  logged_by_details: { id: 'p1', name: 'Maria Lopez', email: 'maria@example.com' },
  participants: [],
  lead: LEAD,
  contact: null,
  account: null,
  opportunity: null,
  case: null,
  home: 'lead',
  origin: 'manual',
  external_id: '',
  created_at: '2026-10-24T09:13:00Z',
  can_edit: true
};
const ENQUIRY = {
  ...CALL,
  id: '6e2f3a4b-5c6d-4e7f-8a91-92ab3c4d5e6f',
  kind: 'enquiry',
  direction: 'inbound',
  occurred_at: '2026-10-24T09:00:00Z',
  duration_seconds: null,
  outcome: '',
  body: 'Is the flat still available?',
  logged_by: null,
  logged_by_details: null,
  origin: 'webform',
  can_edit: true
};

beforeEach(() => {
  apiRequest.mockReset();
});

describe('listInteractions', () => {
  it('reads one record’s interactions by its own filter', async () => {
    apiRequest.mockResolvedValueOnce({ interactions: [CALL, ENQUIRY], count: 2 });
    const { state, interactions, count } = await listInteractions(event, 'lead', LEAD);
    expect(state).toBe('ok');
    expect(count).toBe(2);
    expect(interactions.map((i) => i.kind)).toEqual(['call', 'enquiry']);
    expect(interactions[0].logged_by).toBe('Maria Lopez');
    const [url, options] = apiRequest.mock.calls[0];
    expect(url).toBe(`/interactions/?lead=${LEAD}&limit=50`);
    expect(options.expectedStatuses).toEqual([404]);
  });

  it('asks a deal by `opportunity`', async () => {
    apiRequest.mockResolvedValueOnce({ interactions: [], count: 0 });
    await listInteractions(event, 'opportunity', LEAD);
    expect(apiRequest.mock.calls[0][0]).toBe(`/interactions/?opportunity=${LEAD}&limit=50`);
  });

  it('hides the feature on an API without interactions', async () => {
    apiRequest.mockRejectedValueOnce(status(404));
    expect(await listInteractions(event, 'contact', LEAD)).toEqual({
      state: 'absent',
      interactions: [],
      count: 0
    });
  });

  it('says the read failed on any other error', async () => {
    apiRequest.mockRejectedValueOnce(status(500));
    expect((await listInteractions(event, 'lead', LEAD)).state).toBe('failed');
  });

  it('never asks with a malformed id or an unknown record kind', async () => {
    expect((await listInteractions(event, 'lead', 'x')).state).toBe('failed');
    expect((await listInteractions(event, 'org', LEAD)).state).toBe('failed');
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('toInteraction', () => {
  it('offers delete only on a person’s own log the API lets this caller edit', () => {
    expect(toInteraction(CALL).can_delete).toBe(true);
    expect(toInteraction({ ...CALL, can_edit: false }).can_delete).toBe(false);
    expect(toInteraction(ENQUIRY).can_delete).toBe(false);
    expect(toInteraction({ ...CALL, origin: 'zapier' }).can_delete).toBe(false);
    expect(toInteraction({ ...CALL, origin: 'phone_tap' }).can_delete).toBe(true);
  });

  it('keeps only the fields the pages read', () => {
    const shaped = toInteraction({ ...CALL, org: 'other', participants: [{ email: 'x' }] });
    expect(shaped).not.toHaveProperty('org');
    expect(shaped).not.toHaveProperty('participants');
  });
});

describe('interactionEvents and withInteractions', () => {
  it('turns a call into a headline with its outcome and length, and the note beneath', () => {
    const [e] = interactionEvents([toInteraction(CALL)]);
    expect(e).toMatchObject({
      id: `ix-${IX}`,
      type: 'interaction',
      kind: 'call',
      at: CALL.occurred_at,
      by: 'Maria Lopez',
      body: 'Outgoing call · Connected · 4 min',
      detail: 'Wants a viewing on Saturday.',
      interaction: IX,
      canDelete: true
    });
  });

  it('marks an estimated length and leaves an outcome off anything but a call', () => {
    const [e] = interactionEvents([
      toInteraction({ ...CALL, kind: 'meeting', outcome: 'connected', duration_estimated: true })
    ]);
    expect(e.body).toBe('Meeting · about 4 min');
  });

  it('merges into the page’s activity, newest first', () => {
    const activity = [
      { id: 'note-1', type: 'note', at: '2026-10-24T09:05:00Z', body: 'Note' },
      { id: 'created-1', type: 'status', at: '2026-10-24T08:59:00Z', body: 'Lead created' }
    ];
    const merged = withInteractions(activity, [toInteraction(ENQUIRY), toInteraction(CALL)]);
    expect(merged.map((e) => e.id)).toEqual([
      `ix-${IX}`,
      'note-1',
      `ix-${ENQUIRY.id}`,
      'created-1'
    ]);
    expect(merged[2].body).toBe('Enquiry via web form');
    expect(merged[2].by).toBeNull();
  });
});

describe('interactionBody', () => {
  const now = new Date('2026-10-24T12:00:00Z');

  it('builds a call log against the route’s record', () => {
    const body = interactionBody(
      'lead',
      LEAD,
      {
        kind: 'call',
        direction: 'outbound',
        outcome: 'no_answer',
        duration_minutes: '3',
        subject: 'ignored on a call',
        body: '  Left a message.  ',
        occurred_at: ''
      },
      { now }
    );
    expect(body).toEqual({
      kind: 'call',
      direction: 'outbound',
      origin: 'manual',
      lead: LEAD,
      outcome: 'no_answer',
      duration_seconds: 180,
      duration_estimated: false,
      body: 'Left a message.'
    });
  });

  it('reads the time in the org’s zone', () => {
    const body = interactionBody(
      'contact',
      LEAD,
      { kind: 'email', direction: 'inbound', occurred_at: '2026-10-24T14:30', subject: 'Re: flat' },
      { timeZone: 'Asia/Kolkata', now }
    );
    expect(body.occurred_at).toBe('2026-10-24T09:00:00.000Z');
    expect(body.direction).toBe('inbound');
    expect(body.subject).toBe('Re: flat');
    expect(body.contact).toBe(LEAD);
  });

  it('allows a few minutes of clock drift and refuses a time further ahead', () => {
    expect(() =>
      interactionBody('lead', LEAD, { kind: 'sms', occurred_at: '2026-10-24T12:04' }, { now })
    ).not.toThrow();
    expect(() =>
      interactionBody('lead', LEAD, { kind: 'sms', occurred_at: '2026-10-24T12:10' }, { now })
    ).toThrow('That time is in the future.');
  });

  it('logs a meeting as outbound whatever the form says', () => {
    expect(interactionBody('lead', LEAD, { kind: 'meeting', direction: 'inbound' }).direction).toBe(
      'outbound'
    );
  });

  it('refuses an enquiry, an unknown kind or outcome, and a bad duration', () => {
    expect(() => interactionBody('lead', LEAD, { kind: 'enquiry' })).toThrow(
      'Choose what you are logging.'
    );
    expect(() => interactionBody('lead', LEAD, { kind: '' })).toThrow();
    expect(() => interactionBody('lead', LEAD, { kind: 'call', outcome: 'hung_up' })).toThrow(
      'Choose how the call went.'
    );
    expect(() => interactionBody('lead', LEAD, { kind: 'call', duration_minutes: '2.5' })).toThrow(
      'Duration is a whole number of minutes.'
    );
    expect(() => interactionBody('lead', LEAD, { kind: 'call', duration_minutes: '-1' })).toThrow();
    expect(() => interactionBody('lead', LEAD, { kind: 'call', occurred_at: 'tomorrow' })).toThrow(
      'That date and time could not be read.'
    );
  });

  it('refuses text past the API’s limits', () => {
    expect(() =>
      interactionBody('lead', LEAD, { kind: 'email', subject: 'x'.repeat(201) })
    ).toThrow();
    expect(() =>
      interactionBody('lead', LEAD, { kind: 'call', body: 'x'.repeat(10001) })
    ).toThrow();
  });

  it('never takes the record from anywhere but the route', () => {
    const body = interactionBody('lead', LEAD, {
      kind: 'call',
      contact: 'someone-else',
      origin: 'intake',
      logged_by: 'p9'
    });
    expect(body.contact).toBeUndefined();
    expect(body.logged_by).toBeUndefined();
    expect(body.origin).toBe('manual');
    expect(() => interactionBody('lead', 'not-an-id', { kind: 'call' })).toThrow();
    expect(() => interactionBody('org', LEAD, { kind: 'call' })).toThrow();
  });
});

describe('writes', () => {
  it('POSTs a log and DELETEs by id', async () => {
    apiRequest.mockResolvedValue(CALL);
    await logInteraction(event, { kind: 'call', lead: LEAD });
    expect(apiRequest.mock.calls[0][0]).toBe('/interactions/');
    expect(apiRequest.mock.calls[0][1]).toEqual({
      method: 'POST',
      body: { kind: 'call', lead: LEAD }
    });
    await deleteInteraction(event, IX);
    expect(apiRequest.mock.calls[1][0]).toBe(`/interactions/${IX}/`);
    expect(apiRequest.mock.calls[1][1]).toEqual({ method: 'DELETE' });
  });

  it('never sends a delete for a malformed id', async () => {
    await expect(deleteInteraction(event, '../leads')).rejects.toMatchObject({ status: 404 });
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('interactionActions', () => {
  /** @param {Record<string, string>} fields */
  const actionEvent = (fields, timezone = 'UTC') => {
    const form = new FormData();
    for (const [k, v] of Object.entries(fields)) form.set(k, v);
    return /** @type {any} */ ({
      cookies: event.cookies,
      params: { id: LEAD },
      locals: { org_settings: { timezone } },
      request: { formData: async () => form }
    });
  };
  const { logActivity, deleteActivity } = interactionActions('lead');

  it('logs against the page’s record and says so', async () => {
    apiRequest.mockResolvedValueOnce(CALL);
    const result = await logActivity(actionEvent({ kind: 'call', outcome: 'connected' }));
    expect(result).toEqual({ activity: { logged: true } });
    expect(apiRequest.mock.calls[0][1].body).toMatchObject({ kind: 'call', lead: LEAD });
  });

  it('turns a refused form into a message without calling the API', async () => {
    const result = /** @type {any} */ (await logActivity(actionEvent({ kind: 'enquiry' })));
    expect(result.status).toBe(400);
    expect(result.data.activity.error).toBe('Choose what you are logging.');
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('passes the API’s refusal on with its status', async () => {
    apiRequest.mockRejectedValueOnce(status(404, { detail: 'Not found.' }));
    const result = /** @type {any} */ (await logActivity(actionEvent({ kind: 'call' })));
    expect(result.status).toBe(404);
    expect(result.data.activity.error).toBeTruthy();
  });

  it('deletes by the id the form names, and reports a refusal', async () => {
    apiRequest.mockResolvedValueOnce(null);
    expect(await deleteActivity(actionEvent({ interaction: IX }))).toEqual({
      activity: { deleted: true }
    });
    apiRequest.mockRejectedValueOnce(
      status(403, { error: true, errors: 'Only the person who logged it can change it.' })
    );
    const refused = /** @type {any} */ (await deleteActivity(actionEvent({ interaction: IX })));
    expect(refused.status).toBe(403);
    expect(refused.data.activity.deleteError).toBe('Only the person who logged it can change it.');
  });
});
