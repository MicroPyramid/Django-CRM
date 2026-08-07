import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { getToday } = await import('$lib/server/v2/today.js');
// Cast rather than shaping a full Cookies mock: getToday only passes `cookies`
// through to `apiRequest`, which is mocked above. Same reason as
// timesheet.test.js.
const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });

describe('getToday', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('passes the count, the rows shown and the overflow sources through', async () => {
    apiRequest.mockResolvedValue({
      queue: [{ id: 'invoice-1' }],
      summary: {
        count: 42,
        shown: 8,
        sources: [{ label: 'overdue invoices', count: 23, href: '/invoices' }],
        quiet_deals: 7,
        quiet_value: 5291148,
        cleared_yesterday: 0
      },
      later: []
    });

    const { summary } = await getToday(event);

    expect(summary.count).toBe(42);
    expect(summary.shown).toBe(8);
    expect(summary.sources[0].href).toBe('/invoices');
  });

  it('defaults shown to the rows it actually has, never to zero', async () => {
    // The page decides whether to print "that's everything" by comparing shown
    // against count. A 0 default would make a full page claim it had truncated.
    apiRequest.mockResolvedValue({
      queue: [{ id: 'task-1' }, { id: 'task-2' }],
      summary: { count: 2, quiet_deals: 0, quiet_value: 0, cleared_yesterday: 0 },
      later: []
    });

    const { summary } = await getToday(event);

    expect(summary.shown).toBe(2);
    expect(summary.count).toBe(2);
  });

  it('gives the page an empty source list rather than undefined', async () => {
    apiRequest.mockResolvedValue({});

    const { summary, queue, later } = await getToday(event);

    expect(summary.sources).toEqual([]);
    expect(queue).toEqual([]);
    expect(later).toEqual([]);
    expect(summary.count).toBe(0);
  });
});
