import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));
vi.mock('./org-people.js', () => ({
  getOrgPeopleAndTeams: async () => ({ people: [], teams: [] })
}));

const { listGoals } = await import('./goals.js');

/** A JWT whose payload carries just the role claim `viewerRole` reads. */
function tokenFor(role) {
  const payload = Buffer.from(JSON.stringify({ role })).toString('base64url');
  return `header.${payload}.signature`;
}

const cookies = /** @type {any} */ ({ get: () => tokenFor('ADMIN') });

/** One `SalesGoalSerializer` row, with only the fields under test spelled out. */
function goal(over = {}) {
  return {
    id: 'g1',
    name: 'Goal',
    goal_type: 'REVENUE',
    target_value: '100',
    period_type: 'MONTHLY',
    period_start: '2026-01-01',
    period_end: '2026-12-31',
    is_active: true,
    progress_value: 10,
    progress_percent: 10,
    status: 'on_track',
    ...over
  };
}

function respond({ goals = [], leaderboard = [] }) {
  apiRequest.mockImplementation(async (url) =>
    url.includes('leaderboard') ? { leaderboard } : { goals }
  );
}

describe('listGoals totals', () => {
  beforeEach(() => {
    apiRequest.mockReset();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('sums targets and attainment over the active goals only', async () => {
    vi.setSystemTime(new Date(2026, 5, 1, 12));
    respond({
      goals: [
        goal({ id: 'a', target_value: '100', progress_value: 50 }),
        goal({ id: 'b', target_value: '200', progress_value: 20 }),
        goal({ id: 'c', target_value: '999', progress_value: 999, is_active: false })
      ]
    });

    const { totals } = await listGoals({ cookies });
    expect(totals.count).toBe(3);
    expect(totals.active).toBe(2);
    expect(totals.target).toBe(300);
    expect(totals.achieved).toBe(70);
  });

  it('still counts a goal whose period ends today as behind pace', async () => {
    // The boundary this fixes. `new Date('2026-06-01')` is midnight UTC, so
    // measuring it against `Date.now()` dropped the goal out of this count
    // part-way through its own final day, for every timezone east of
    // Greenwich and for most of the day. Noon local is chosen deliberately:
    // it is past midnight UTC, which is exactly when the old code broke.
    vi.setSystemTime(new Date(2026, 5, 1, 12));
    respond({ goals: [goal({ status: 'behind', period_end: '2026-06-01' })] });

    const { totals } = await listGoals({ cookies });
    expect(totals.behind).toBe(1);
  });

  it('leaves out a goal whose period has already ended', async () => {
    vi.setSystemTime(new Date(2026, 5, 1, 12));
    respond({ goals: [goal({ status: 'behind', period_end: '2026-05-31' })] });

    const { totals } = await listGoals({ cookies });
    expect(totals.behind).toBe(0);
  });

  it('leaves out a retired goal even when it is behind and still open', async () => {
    vi.setSystemTime(new Date(2026, 5, 1, 12));
    respond({
      goals: [goal({ status: 'behind', period_end: '2026-12-31', is_active: false })]
    });

    const { totals } = await listGoals({ cookies });
    expect(totals.behind).toBe(0);
  });
});

describe('listGoals leaderboard', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('reads the name the endpoint sends, which is no longer an email', async () => {
    // The row used to carry the address twice, as `name` and as `email`, so
    // this list printed raw addresses. There is nothing to fall back to now.
    respond({
      leaderboard: [
        {
          rank: 1,
          goal_id: 'g1',
          user: { id: 'p1', name: 'Ada Lovelace' },
          target: 100,
          achieved: 104,
          percent: 104
        }
      ]
    });

    const { leaderboard } = await listGoals({ cookies });
    expect(leaderboard[0].user).toBe('Ada Lovelace');
    // Uncapped, unlike `progress_percent`, which the model caps at 100.
    expect(leaderboard[0].percent).toBe(104);
  });

  it('says Unknown rather than blank when the user block is missing', async () => {
    respond({ leaderboard: [{ rank: 1, goal_id: 'g1' }] });
    const { leaderboard } = await listGoals({ cookies });
    expect(leaderboard[0].user).toBe('Unknown');
  });

  it('is empty rather than throwing when the endpoint narrows a member to nothing', async () => {
    // An ordinary outcome now that the board is scoped like the list: somebody
    // with no current monthly goal of their own ranks against nobody.
    respond({ leaderboard: [] });
    const { leaderboard } = await listGoals({ cookies });
    expect(leaderboard).toEqual([]);
  });
});

describe('listGoals can_edit', () => {
  beforeEach(() => {
    apiRequest.mockReset();
    respond({});
  });

  it('is true for an admin and false for a member', async () => {
    const asAdmin = await listGoals({ cookies });
    expect(asAdmin.can_edit).toBe(true);

    const asMember = await listGoals({
      cookies: /** @type {any} */ ({ get: () => tokenFor('USER') })
    });
    expect(asMember.can_edit).toBe(false);
  });

  it('is false when there is no token, rather than throwing', async () => {
    const signedOut = await listGoals({
      cookies: /** @type {any} */ ({ get: () => undefined })
    });
    expect(signedOut.can_edit).toBe(false);
  });
});
