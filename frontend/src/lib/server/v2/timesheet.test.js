import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { stopTimer } = await import('$lib/server/v2/timesheet.js');
// Cast rather than shaping a full Cookies mock, matching leads.test.js and
// tags.test.js: stopTimer only ever calls `cookies.get`, and `apiRequest`
// itself is mocked above, so nothing here touches
// `getAll`/`set`/`delete`/`serialize`. Without the cast svelte-check flags
// this object against SvelteKit's full `Cookies` type on every call site
// below, which is noise for a shape the test deliberately keeps minimal.
const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });

describe('stopTimer', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('POSTs to the stop endpoint for the given entry', async () => {
    apiRequest.mockResolvedValue({ id: 'e1', ended_at: '2026-08-04T10:00:00Z' });
    const result = await stopTimer(event, 'e1');

    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/time-entries/e1/stop/');
    expect(options.method).toBe('POST');
    expect(result.ended_at).toBeTruthy();
  });

  it('refuses a missing entry id rather than posting to a malformed path', async () => {
    await expect(stopTimer(event, '')).rejects.toThrow(/entry/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
