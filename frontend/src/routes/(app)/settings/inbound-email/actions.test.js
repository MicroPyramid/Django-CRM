import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

vi.mock('$app/env/public', () => ({ PUBLIC_DJANGO_API_URL: 'http://api.test' }));

const { actions } = /** @type {any} */ (await import('./+page.server.js'));

const cookies = /** @type {any} */ ({ get: () => undefined });

/** @param {[string, string][]} entries */
function post(entries) {
  const body = new FormData();
  for (const [key, value] of entries) body.append(key, value);
  return /** @type {any} */ ({
    request: new Request('http://test/settings/inbound-email', { method: 'POST', body }),
    cookies
  });
}

const sent = () => apiRequest.mock.calls[0][1].body;

beforeEach(() => {
  apiRequest.mockReset();
  apiRequest.mockResolvedValue({});
});

describe('the mailbox form', () => {
  it('sends creates and the lead defaults on a lead address', async () => {
    await actions.create(
      post([
        ['address', 'Leads@Acme.io'],
        ['provider', 'ses'],
        ['creates', 'leads'],
        ['lead_source', 'email'],
        ['lead_source_detail', 'Zillow'],
        ['default_priority', 'Normal'],
        ['default_case_type', ''],
        ['default_assignee_id', 'p1'],
        ['is_active', 'true'],
        ['address_mode', 'own']
      ])
    );
    expect(sent()).toMatchObject({
      address: 'leads@acme.io',
      creates: 'leads',
      lead_source: 'email',
      lead_source_detail: 'Zillow',
      default_assignee_id: 'p1',
      is_active: true
    });
    expect('generate_address' in sent()).toBe(false);
  });

  it('asks the server for an address when generating one', async () => {
    await actions.create(
      post([
        ['creates', 'leads'],
        ['lead_source', 'email'],
        ['default_priority', 'Normal'],
        ['is_active', 'true'],
        ['address_mode', 'generate']
      ])
    );
    expect(sent()).toMatchObject({ generate_address: true, provider: 'ses', creates: 'leads' });
    expect('address' in sent()).toBe(false);
  });

  it('sends no lead fields when the form did not draw them', async () => {
    await actions.update(
      post([
        ['id', 'm1'],
        ['address', 'help@acme.io'],
        ['provider', 'ses'],
        ['default_priority', 'High'],
        ['default_case_type', 'Question'],
        ['default_assignee_id', '']
      ])
    );
    const body = sent();
    for (const key of ['creates', 'lead_source', 'lead_source_detail', 'generate_address']) {
      expect(key in body).toBe(false);
    }
    expect(body.default_priority).toBe('High');
  });

  it('leaves a generated address and its provider alone on an edit', async () => {
    await actions.update(
      post([
        ['id', 'm1'],
        ['creates', 'leads'],
        ['lead_source', 'walk-in'],
        ['default_priority', 'Normal'],
        ['default_assignee_id', '']
      ])
    );
    expect('address' in sent()).toBe(false);
    expect('provider' in sent()).toBe(false);
    expect(sent().lead_source).toBe('walk-in');
  });
});

describe('the webhook secret field', () => {
  const edit = (/** @type {[string, string][]} */ extra) =>
    post([
      ['id', 'm1'],
      ['address', 'help@acme.io'],
      ['provider', 'postmark'],
      ['default_priority', 'Normal'],
      ...extra
    ]);

  it('sends a typed secret', async () => {
    await actions.update(edit([['webhook_secret', ' s3cret ']]));
    expect(sent().webhook_secret).toBe('s3cret');
  });

  it('sends nothing when the field is blank, so the stored one is kept', async () => {
    await actions.update(edit([['webhook_secret', '']]));
    expect('webhook_secret' in sent()).toBe(false);
  });

  it('sends nothing when the form has no such field', async () => {
    await actions.update(edit([]));
    expect('webhook_secret' in sent()).toBe(false);
  });
});
