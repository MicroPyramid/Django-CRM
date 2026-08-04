import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { updateReopenPolicy } = await import('$lib/server/v2/reopen.js');

// Cast rather than shaping a full Cookies mock, matching tags.test.js: the
// function under test only reads `cookies.get`, and `apiRequest` is mocked.
const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });

describe('updateReopenPolicy', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('PUTs the four policy fields to the singleton endpoint', async () => {
    apiRequest.mockResolvedValue({ is_enabled: true, reopen_window_days: 14 });

    await updateReopenPolicy(event, {
      is_enabled: true,
      reopen_window_days: 14,
      reopen_to_status: 'Assigned',
      notify_assigned: false
    });

    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/cases/reopen-policy/');
    expect(options.method).toBe('PUT');
    expect(options.body).toEqual({
      is_enabled: true,
      reopen_window_days: 14,
      reopen_to_status: 'Assigned',
      notify_assigned: false
    });
  });

  it('never forwards a computed metric or a client-supplied org', async () => {
    apiRequest.mockResolvedValue({});

    await updateReopenPolicy(event, {
      is_enabled: true,
      reopen_window_days: 7,
      reopen_to_status: 'New',
      notify_assigned: true,
      reopened_last_30d: 999,
      org: 'attacker-org'
    });

    const body = apiRequest.mock.calls[0][1].body;
    expect(body.reopened_last_30d).toBeUndefined();
    expect(body.org).toBeUndefined();
  });

  it('rejects a window outside 1 to 365 before making a request', async () => {
    await expect(
      updateReopenPolicy(event, {
        is_enabled: true,
        reopen_window_days: 0,
        reopen_to_status: 'New',
        notify_assigned: true
      })
    ).rejects.toThrow(/between 1 and 365/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('rejects a terminal reopen_to_status before making a request', async () => {
    await expect(
      updateReopenPolicy(event, {
        is_enabled: true,
        reopen_window_days: 7,
        reopen_to_status: 'Closed',
        notify_assigned: true
      })
    ).rejects.toThrow(/New, Assigned or Pending/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
