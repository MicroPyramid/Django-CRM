import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { createLead, convertLead } = await import('$lib/server/v2/leads.js');
// Cast rather than shaping a full Cookies mock: createLead only ever calls
// `cookies.get`, and `apiRequest` itself is mocked above, so nothing here
// touches `getAll`/`set`/`delete`/`serialize`. Without the cast svelte-check
// flags this object against SvelteKit's full `Cookies` type on every call site
// below, which is noise for a shape the test deliberately keeps minimal.
const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });

describe('createLead', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('POSTs to /leads/ and returns the created lead', async () => {
    apiRequest.mockResolvedValue({ id: 'abc', first_name: 'Ada' });
    const result = await createLead(event, { first_name: 'Ada', last_name: 'Lovelace' });

    expect(apiRequest).toHaveBeenCalledOnce();
    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/leads/');
    expect(options.method).toBe('POST');
    expect(options.body.first_name).toBe('Ada');
    expect(result.id).toBe('abc');
  });

  it('sends an empty field as null rather than an empty string', async () => {
    apiRequest.mockResolvedValue({ id: 'abc' });
    await createLead(event, { first_name: 'Ada', job_title: '' });
    expect(apiRequest.mock.calls[0][1].body.job_title).toBeNull();
  });

  it('coerces opportunity_amount to a number', async () => {
    apiRequest.mockResolvedValue({ id: 'abc' });
    await createLead(event, { first_name: 'Ada', opportunity_amount: '4200.50' });
    expect(apiRequest.mock.calls[0][1].body.opportunity_amount).toBe(4200.5);
  });

  it('wraps a single owner id in a list, matching the API contract', async () => {
    apiRequest.mockResolvedValue({ id: 'abc' });
    await createLead(event, { first_name: 'Ada', assigned_to: 'profile-1' });
    expect(apiRequest.mock.calls[0][1].body.assigned_to).toEqual(['profile-1']);
  });

  it('never forwards a client-supplied org, which the backend derives from the JWT', async () => {
    apiRequest.mockResolvedValue({ id: 'abc' });
    await createLead(event, { first_name: 'Ada', org: 'attacker-org', created_by: 'someone' });
    const body = apiRequest.mock.calls[0][1].body;
    expect(body.org).toBeUndefined();
    expect(body.created_by).toBeUndefined();
  });
});

describe('convertLead', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('PATCHes the lead detail URL with status: converted, and nothing else', async () => {
    apiRequest.mockResolvedValue({
      error: false,
      account_id: 'acc-1',
      contact_id: 'con-1',
      opportunity_id: 'opp-1'
    });
    const result = await convertLead(event, 'lead-1');

    expect(apiRequest).toHaveBeenCalledOnce();
    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/leads/lead-1/');
    expect(options.method).toBe('PATCH');
    expect(options.body).toEqual({ status: 'converted' });
    expect(result.account_id).toBe('acc-1');
  });

  it('refuses to call the API without a lead id', async () => {
    await expect(convertLead(event, '')).rejects.toThrow(/id is required/);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('lets a rejected conversion (e.g. the email guard) propagate to the caller', async () => {
    const rejection = Object.assign(new Error('{"error":true,"errors":{"email":["required"]}}'), {
      status: 400
    });
    apiRequest.mockRejectedValue(rejection);
    await expect(convertLead(event, 'lead-1')).rejects.toBe(rejection);
  });
});
