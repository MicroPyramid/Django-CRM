import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...args) => apiRequest(...args) }));

const {
  createSupportTicket,
  getSupportTicket,
  listSupportTickets,
  loadHelpPage,
  replyToSupportTicket
} = await import('./support.js');

const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });

function apiTicket(overrides = {}) {
  return {
    id: '4d60686d-bd3d-4e33-b114-ab36f194a6cd',
    reference: 'SUP-4D60686D',
    subject: 'Export failed',
    category: 'technical',
    category_label: 'Technical issue',
    status: 'open',
    status_label: 'Open',
    priority: 'normal',
    priority_label: 'Normal',
    message_count: 1,
    last_activity_at: '2026-08-08T00:00:00Z',
    created_at: '2026-08-08T00:00:00Z',
    messages: [],
    ...overrides
  };
}

describe('support API adapter', () => {
  // Block body on purpose. An expression body returns the mock, and vitest
  // treats a function returned from beforeEach as a teardown callback, so it
  // calls apiRequest() after every test. That is invisible while the mock
  // resolves and becomes an unhandled rejection the moment one rejects.
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('maps the customer list envelope', async () => {
    apiRequest.mockResolvedValue({ count: 1, tickets: [apiTicket()] });
    const result = await listSupportTickets(event);
    expect(result.count).toBe(1);
    expect(result.tickets[0].statusLabel).toBe('Open');
    expect(apiRequest.mock.calls[0][0]).toBe('/support/?limit=100');
  });

  it('allow-lists create fields and does not forward server-owned values', async () => {
    apiRequest.mockResolvedValue(apiTicket());
    await createSupportTicket(
      event,
      /** @type {any} */ ({
        subject: '  Export failed  ',
        category: 'technical',
        body: '  It returns 500.  ',
        org: 'attacker-org',
        status: 'closed',
        priority: 'urgent'
      })
    );
    const form = apiRequest.mock.calls[0][1].body;
    expect([...form.keys()].sort()).toEqual(['body', 'category', 'subject']);
    expect(form.get('subject')).toBe('Export failed');
    expect(form.get('body')).toBe('It returns 500.');
  });

  it('builds local authenticated attachment links', async () => {
    const id = apiTicket().id;
    apiRequest.mockResolvedValue(
      apiTicket({
        messages: [
          {
            id: 'm1',
            author_label: 'BottleCRM Support',
            author_type: 'staff',
            body: 'Please check this file.',
            attachment_name: 'steps.pdf',
            attachment_download_url: '/api/support/messages/m1/attachment/',
            created_at: '2026-08-08T01:00:00Z'
          }
        ]
      })
    );
    const ticket = await getSupportTicket(event, id);
    expect(ticket.messages[0].attachmentUrl).toBe(`/help/${id}/attachments/m1`);
  });

  it('turns a missing ticket into a 404 rather than a 500', async () => {
    // Somebody else's ticket answers 404 too, deliberately: a 403 would
    // confirm the id is real.
    const failure = /** @type {any} */ (new Error('Not found'));
    failure.status = 404;
    apiRequest.mockRejectedValue(failure);

    await expect(getSupportTicket(event, apiTicket().id)).rejects.toMatchObject({ status: 404 });
  });

  it('lets any other failure through untouched', async () => {
    const failure = /** @type {any} */ (new Error('Bad gateway'));
    failure.status = 502;
    apiRequest.mockRejectedValue(failure);

    await expect(getSupportTicket(event, apiTicket().id)).rejects.toMatchObject({ status: 502 });
  });

  describe('the help page picks its tier from the support queue', () => {
    /** @param {number} status */
    function apiFailure(status) {
      const failure = /** @type {any} */ (new Error(`HTTP ${status}`));
      failure.status = status;
      return failure;
    }

    it('serves the queue when the enterprise API answers', async () => {
      apiRequest.mockResolvedValue({ count: 1, tickets: [apiTicket()] });

      const data = await loadHelpPage(event);

      expect(data.available).toBe(true);
      expect(data.tickets).toHaveLength(1);
    });

    it('falls back to self-serve when the API is absent, which is a 404', async () => {
      // A community deployment has no platform_support app, so the route
      // itself does not exist. That is a deployment fact, not a failure.
      apiRequest.mockRejectedValue(apiFailure(404));

      const data = await loadHelpPage(event);

      expect(data.available).toBe(false);
      expect(data.tickets).toEqual([]);
      expect(data.count).toBe(0);
    });

    it.each([500, 502, 401, 403])(
      'still fails on %i, so an outage is not disguised as the community edition',
      async (status) => {
        apiRequest.mockRejectedValue(apiFailure(status));

        await expect(loadHelpPage(event)).rejects.toThrow(`HTTP ${status}`);
      }
    );

    it('still fails when the error carries no status at all', async () => {
      apiRequest.mockRejectedValue(new Error('socket hang up'));

      await expect(loadHelpPage(event)).rejects.toThrow('socket hang up');
    });
  });

  it('posts replies only to the selected ticket endpoint', async () => {
    apiRequest.mockResolvedValue(apiTicket());
    await replyToSupportTicket(event, apiTicket().id, { body: ' Still broken ' });
    const [url, options] = apiRequest.mock.calls[0];
    expect(url).toContain(`/support/${apiTicket().id}/replies/`);
    expect([...options.body.keys()]).toEqual(['body']);
    expect(options.body.get('body')).toBe('Still broken');
  });
});
