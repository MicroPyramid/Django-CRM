import { describe, it, expect, vi, beforeEach } from 'vitest';

// Local mock plus a thin wrapper, matching every other test in this
// directory (business-hours.test.js, tags.test.js, etc). Destructuring
// `apiRequest` straight off `await import('$lib/api-helpers.js')` types it
// against the real module's declared signature, which has no
// `mockReset`/`mockResolvedValue`, and fails `svelte-check`.
const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { getOrgPeopleAndTeams } = await import('./org-people.js');

const cookies = /** @type {any} */ ({});

describe('getOrgPeopleAndTeams', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('labels a person by name when there is one', async () => {
    apiRequest.mockResolvedValue({
      profiles: [{ id: 'p1', user_details: { name: 'Ada Lovelace', email: 'ada@x.io' } }],
      teams: []
    });
    const { people } = await getOrgPeopleAndTeams(cookies);
    expect(people).toEqual([{ id: 'p1', name: 'Ada Lovelace' }]);
  });

  it('falls back to the email, then to Unnamed', async () => {
    apiRequest.mockResolvedValue({
      profiles: [
        { id: 'p1', user_details: { email: 'ada@x.io' } },
        { id: 'p2', user_details: {} },
        { id: 'p3' }
      ],
      teams: []
    });
    const { people } = await getOrgPeopleAndTeams(cookies);
    expect(people.map((p) => p.name)).toEqual(['ada@x.io', 'Unnamed', 'Unnamed']);
  });

  it('flattens teams to id and name', async () => {
    apiRequest.mockResolvedValue({
      profiles: [],
      teams: [{ id: 't1', name: 'Support', description: 'ignored', users: [1, 2] }]
    });
    const { teams } = await getOrgPeopleAndTeams(cookies);
    expect(teams).toEqual([{ id: 't1', name: 'Support' }]);
  });

  it('returns empty lists rather than throwing when the fetch fails', async () => {
    apiRequest.mockImplementation(() => {
      throw new Error('boom');
    });
    await expect(getOrgPeopleAndTeams(cookies)).resolves.toEqual({ people: [], teams: [] });
  });

  it('survives a response missing both keys', async () => {
    apiRequest.mockResolvedValue({});
    await expect(getOrgPeopleAndTeams(cookies)).resolves.toEqual({ people: [], teams: [] });
  });
});
