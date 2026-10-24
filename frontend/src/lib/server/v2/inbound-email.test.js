import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const {
  createMailbox,
  updateMailbox,
  deleteMailbox,
  getMailboxes,
  topicArnEdit,
  webhookSecretEdit
} = await import('./inbound-email.js');

const ARN = 'arn:aws:sns:us-east-1:123456789012:inbound';

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

  it('sends a typed webhook_secret, trimmed, and nothing when it is blank', async () => {
    apiRequest.mockResolvedValue({});
    await createMailbox(event, { ...base, provider: 'postmark', webhook_secret: ' s3cret ' });
    expect(apiRequest.mock.calls[0][1].body.webhook_secret).toBe('s3cret');
    await createMailbox(event, { ...base, provider: 'postmark', webhook_secret: '  ' });
    expect('webhook_secret' in apiRequest.mock.calls[1][1].body).toBe(false);
  });

  it('drops a webhook_secret when the server generates the address', async () => {
    apiRequest.mockResolvedValue({});
    await createMailbox(event, { generate_address: true, webhook_secret: 'x' });
    expect('webhook_secret' in apiRequest.mock.calls[0][1].body).toBe(false);
  });

  it('sends an admin-entered topic_arn, trimmed', async () => {
    apiRequest.mockResolvedValue({});
    await createMailbox(event, { ...base, topic_arn: `  ${ARN} ` });
    const [, opts] = apiRequest.mock.calls[0];
    expect(opts.body.topic_arn).toBe(ARN);
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

  it('sends a typed webhook_secret and leaves it out when none was given', async () => {
    apiRequest.mockResolvedValue({});
    await updateMailbox(event, 'm1', { ...base, webhook_secret: 'abc' });
    expect(apiRequest.mock.calls[0][1].body.webhook_secret).toBe('abc');
    await updateMailbox(event, 'm1', { ...base });
    expect('webhook_secret' in apiRequest.mock.calls[1][1].body).toBe(false);
  });

  it('sends a changed topic_arn, and an empty one clears it', async () => {
    apiRequest.mockResolvedValue({});
    await updateMailbox(event, 'm1', { topic_arn: ARN });
    await updateMailbox(event, 'm1', { topic_arn: '' });
    expect(apiRequest.mock.calls[0][1].body).toEqual({ topic_arn: ARN });
    expect(apiRequest.mock.calls[1][1].body).toEqual({ topic_arn: '' });
  });

  it('leaves topic_arn out when the form did not change it', async () => {
    apiRequest.mockResolvedValue({});
    await updateMailbox(event, 'm1', { ...base, topic_arn: undefined });
    expect('topic_arn' in apiRequest.mock.calls[0][1].body).toBe(false);
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

describe('topicArnEdit', () => {
  it('is undefined when the field was not on the form', () => {
    expect(topicArnEdit(null, '')).toBeUndefined();
    expect(topicArnEdit(undefined, ARN)).toBeUndefined();
  });

  it('is undefined when the value is what the form was prefilled with', () => {
    // A stale form must not undo a pin the webhook set after the page loaded.
    expect(topicArnEdit('', '')).toBeUndefined();
    expect(topicArnEdit(` ${ARN} `, ARN)).toBeUndefined();
  });

  it('is the new value, trimmed, when the admin changed it', () => {
    expect(topicArnEdit(` ${ARN}`, '')).toBe(ARN);
    expect(topicArnEdit('arn:aws:sns:eu-west-1:123456789012:other', ARN)).toBe(
      'arn:aws:sns:eu-west-1:123456789012:other'
    );
  });

  it('is the empty string when the admin cleared it', () => {
    expect(topicArnEdit('  ', ARN)).toBe('');
  });
});

describe('getMailboxes', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  const row = { id: 'm1', address: 'a@b.io', provider: 'ses', is_active: true };

  it('carries the ARN the backend sent an admin', async () => {
    apiRequest.mockResolvedValue({
      mailboxes: [{ ...row, has_topic_arn: true, topic_arn: ARN, webhook_secret: 'x' }]
    });
    const { mailboxes } = await getMailboxes(event);
    expect(mailboxes[0].topic_arn).toBe(ARN);
    expect(mailboxes[0].has_topic_arn).toBe(true);
    expect('webhook_secret' in mailboxes[0]).toBe(false);
  });

  it('has a null ARN for a member, who is sent only has_topic_arn', async () => {
    apiRequest.mockResolvedValue({ mailboxes: [{ ...row, has_topic_arn: true }] });
    const { mailboxes } = await getMailboxes(event);
    expect(mailboxes[0].topic_arn).toBeNull();
    expect(mailboxes[0].has_topic_arn).toBe(true);
  });
});

describe('lead addresses', () => {
  beforeEach(() => {
    apiRequest.mockReset();
    apiRequest.mockResolvedValue({});
  });

  it('sends creates, the lead source and the sub-source on create', async () => {
    await createMailbox(event, {
      ...base,
      creates: 'leads',
      lead_source: ' email ',
      lead_source_detail: ' Zillow '
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.creates).toBe('leads');
    expect(body.lead_source).toBe('email');
    expect(body.lead_source_detail).toBe('Zillow');
  });

  it('sends creates on an edit, and reads anything but leads as tickets', async () => {
    await updateMailbox(event, 'm1', { creates: 'leads' });
    expect(apiRequest.mock.calls[0][1]).toEqual({ method: 'PUT', body: { creates: 'leads' } });
    await updateMailbox(event, 'm1', { creates: 'cases' });
    expect(apiRequest.mock.calls[1][1].body).toEqual({ creates: 'tickets' });
  });

  it('asks the server to generate the address, sending nothing typed for it', async () => {
    await createMailbox(event, {
      ...base,
      address: '',
      topic_arn: ARN,
      provider: 'mailgun',
      creates: 'leads',
      generate_address: true
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.generate_address).toBe(true);
    expect(body.provider).toBe('ses');
    expect('address' in body).toBe(false);
    expect('topic_arn' in body).toBe(false);
  });

  it('still needs an address when not generating one, and never generates on an edit', async () => {
    await expect(createMailbox(event, { ...base, address: '' })).rejects.toThrow(
      'A mailbox needs an address.'
    );
    await updateMailbox(event, 'm1', { generate_address: true, is_active: true });
    expect(apiRequest.mock.calls[0][1].body).toEqual({ is_active: true });
  });

  it('reads the new fields, the generated domain and whether leads are on offer', async () => {
    apiRequest.mockResolvedValueOnce({
      generated_domain: 'in.example.io',
      mailboxes: [
        { id: 'm1', address: 'acme-x1y2z3@in.example.io', creates: 'leads', lead_source: 'email' },
        { id: 'm2', address: 'help@acme.io', creates: 'tickets', is_generated: false }
      ]
    });
    const answer = await getMailboxes(event);
    expect(answer.generated_domain).toBe('in.example.io');
    expect(answer.can_create_leads).toBe(true);
    expect(answer.mailboxes[0]).toMatchObject({
      creates: 'leads',
      lead_source: 'email',
      lead_source_detail: '',
      is_generated: true
    });
    expect(answer.mailboxes[1].is_generated).toBe(false);
  });

  it('offers tickets only on an older API', async () => {
    apiRequest.mockResolvedValueOnce({ mailboxes: [{ id: 'm1', address: 'a@b.io' }] });
    const answer = await getMailboxes(event);
    expect(answer.can_create_leads).toBe(false);
    expect(answer.generated_domain).toBeNull();
    expect(answer.mailboxes[0].creates).toBe('tickets');
  });
});

describe('webhookSecretEdit', () => {
  it('is undefined when nothing was typed, so a stored secret is kept', () => {
    expect(webhookSecretEdit(null)).toBeUndefined();
    expect(webhookSecretEdit('')).toBeUndefined();
    expect(webhookSecretEdit('   ')).toBeUndefined();
  });

  it('is the typed value, trimmed', () => {
    expect(webhookSecretEdit(' abc ')).toBe('abc');
  });
});

describe('getMailboxes secrets', () => {
  it('carries has_webhook_secret and never a secret', async () => {
    apiRequest.mockResolvedValue({
      mailboxes: [
        { id: 'm1', provider: 'postmark', has_webhook_secret: true, webhook_secret: 'leak' }
      ],
      totals: {}
    });
    const { mailboxes } = await getMailboxes(event);
    expect(mailboxes[0].has_webhook_secret).toBe(true);
    expect('webhook_secret' in mailboxes[0]).toBe(false);
  });

  it('reads a row with no flag as having no secret', async () => {
    apiRequest.mockResolvedValue({ mailboxes: [{ id: 'm1', provider: 'mailgun' }], totals: {} });
    const { mailboxes } = await getMailboxes(event);
    expect(mailboxes[0].has_webhook_secret).toBe(false);
  });
});
