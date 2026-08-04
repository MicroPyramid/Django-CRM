import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { createMailbox, updateMailbox, deleteMailbox } = await import('./inbound-email.js');

const cookies = /** @type {any} */ ({ get: () => 'token' });
const event = /** @type {any} */ ({ cookies });

const base = {
  address: 'Support@Example.io',
  provider: 'ses',
  default_priority: 'Normal',
  default_case_type: 'Question',
  default_assignee_id: 'p1',
  is_active: true
};

describe('createMailbox', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('sends only allow-listed keys on create and drops a hostile org', async () => {
    apiRequest.mockResolvedValue({});
    await createMailbox(event, {
      ...base,
      org: 'ATTACKER-ORG',
      created_by: 'ATTACKER'
    });
    const [url, opts] = apiRequest.mock.calls[0];
    expect(url).toBe('/cases/mailboxes/');
    expect(opts.method).toBe('POST');
    expect(Object.keys(opts.body).sort()).toEqual([
      'address',
      'default_assignee_id',
      'default_case_type',
      'default_priority',
      'is_active',
      'provider'
    ]);
    expect(opts.body.org).toBeUndefined();
    expect(opts.body.created_by).toBeUndefined();
  });

  it('never sends a webhook_secret or topic_arn, even when handed one', async () => {
    apiRequest.mockResolvedValue({});
    await createMailbox(event, {
      ...base,
      webhook_secret: 'ATTACKER-CHOSEN',
      topic_arn: 'arn:aws:sns:us-east-1:999999999999:x'
    });
    const [, opts] = apiRequest.mock.calls[0];
    expect(opts.body.webhook_secret).toBeUndefined();
    expect(opts.body.topic_arn).toBeUndefined();
  });

  it('trims and lowercases the address before sending', async () => {
    apiRequest.mockResolvedValue({});
    await createMailbox(event, { ...base, address: '  Support@Example.IO  ' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.address).toBe('support@example.io');
  });

  it('sends null, not an empty string, for an unselected default_case_type', async () => {
    apiRequest.mockResolvedValue({});
    await createMailbox(event, { ...base, default_case_type: '' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.default_case_type).toBeNull();
  });

  it('sends null, not an empty string, for an unselected default_assignee_id', async () => {
    apiRequest.mockResolvedValue({});
    await createMailbox(event, { ...base, default_assignee_id: '' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.default_assignee_id).toBeNull();
  });

  it('coerces is_active to a boolean', async () => {
    apiRequest.mockResolvedValue({});
    await createMailbox(event, { ...base, is_active: 'true' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.is_active).toBe(true);
    expect(typeof body.is_active).toBe('boolean');
  });

  it('refuses a mailbox with no address before making a request', async () => {
    await expect(createMailbox(event, { ...base, address: '' })).rejects.toThrow(
      /needs an address/i
    );
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('refuses a mailbox whose address is only whitespace before making a request', async () => {
    await expect(createMailbox(event, { ...base, address: '   ' })).rejects.toThrow(
      /needs an address/i
    );
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('updateMailbox', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('PUTs to the detail endpoint', async () => {
    apiRequest.mockResolvedValue({});
    await updateMailbox(event, 'm1', base);
    const [url, opts] = apiRequest.mock.calls[0];
    expect(url).toBe('/cases/mailboxes/m1/');
    expect(opts.method).toBe('PUT');
  });

  it('sends only what it is given, with no org/created_by', async () => {
    apiRequest.mockResolvedValue({});
    await updateMailbox(event, 'm1', {
      ...base,
      org: 'ATTACKER-ORG',
      created_by: 'ATTACKER'
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(Object.keys(body).sort()).toEqual([
      'address',
      'default_assignee_id',
      'default_case_type',
      'default_priority',
      'is_active',
      'provider'
    ]);
    expect(body.org).toBeUndefined();
    expect(body.created_by).toBeUndefined();
  });

  it('never sends a webhook_secret or topic_arn, even when handed one', async () => {
    apiRequest.mockResolvedValue({});
    await updateMailbox(event, 'm1', {
      ...base,
      webhook_secret: 'ATTACKER-CHOSEN',
      topic_arn: 'arn:aws:sns:us-east-1:999999999999:x'
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.webhook_secret).toBeUndefined();
    expect(body.topic_arn).toBeUndefined();
  });

  it('sends exactly one key for a minimal { is_active: true } body (the turn-on path)', async () => {
    apiRequest.mockResolvedValue({});
    await updateMailbox(event, 'm1', { is_active: true });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body).toEqual({ is_active: true });
  });

  it('sends exactly one key for a minimal { is_active: false } body (the turn-off path)', async () => {
    apiRequest.mockResolvedValue({});
    await updateMailbox(event, 'm1', { is_active: false });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body).toEqual({ is_active: false });
  });

  it('does not require an address, since a turn-on/off submits none', async () => {
    apiRequest.mockResolvedValue({});
    await expect(updateMailbox(event, 'm1', { is_active: true })).resolves.toBeDefined();
  });

  it('trims and lowercases an address when one is submitted', async () => {
    apiRequest.mockResolvedValue({});
    await updateMailbox(event, 'm1', { address: '  New@Example.IO  ' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.address).toBe('new@example.io');
  });

  it('throws when the id is missing', async () => {
    await expect(updateMailbox(event, '', base)).rejects.toThrow(/which mailbox/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('deleteMailbox', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('DELETEs the detail endpoint', async () => {
    apiRequest.mockResolvedValue({});
    await deleteMailbox(event, 'm1');
    const [url, opts] = apiRequest.mock.calls[0];
    expect(url).toBe('/cases/mailboxes/m1/');
    expect(opts.method).toBe('DELETE');
  });

  it('throws when the id is missing', async () => {
    await expect(deleteMailbox(event, '')).rejects.toThrow(/which mailbox/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
