/**
 * The tickets list's bulk actions report a refused batch instead of throwing.
 *
 * The API refuses a batch outright for a few reasons, a batch over 200 ids
 * among them (issue #829). The actions let that throw, which surfaced as an
 * error page instead of a sentence in the bulk bar's banner.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { actions } = await import('../../../routes/(app)/tickets/+page.server.js');

/** @param {[string, string][]} entries */
function actionEvent(entries) {
  const body = new FormData();
  for (const [key, value] of entries) body.append(key, value);
  return /** @type {any} */ ({
    request: new Request('http://test/tickets', { method: 'POST', body }),
    cookies: { get: () => 'token' }
  });
}

const REFUSAL = 'Select at most 200 tickets at a time.';

/** What `apiRequest` throws for the `{error: true, errors: "<sentence>"}` envelope. */
function refused() {
  return Object.assign(new Error(`errors: ${REFUSAL}`), {
    status: 400,
    body: { error: true, errors: REFUSAL }
  });
}

const UPDATE = /** @type {[string, string][]} */ ([
  ['ids', 'a'],
  ['field', 'priority'],
  ['value', 'Urgent']
]);
const DELETE = /** @type {[string, string][]} */ ([['ids', 'a']]);

describe('ticket bulk actions', () => {
  beforeEach(() => apiRequest.mockReset());

  it.each([
    ['bulkUpdate', UPDATE],
    ['bulkDelete', DELETE]
  ])('%s returns the API sentence when the batch is refused', async (name, entries) => {
    apiRequest.mockRejectedValueOnce(refused());
    const result = /** @type {any} */ (await actions[name](actionEvent(entries)));
    expect(result.status).toBe(400);
    expect(result.data.message).toBe(REFUSAL);
  });

  it('a batch that runs still returns its summary', async () => {
    apiRequest.mockResolvedValueOnce({ results: [{ id: 'a', status: 'updated' }] });
    const result = /** @type {any} */ (await actions.bulkUpdate(actionEvent(UPDATE)));
    expect(result.ok).toBe(true);
    expect(result.summary.updated).toBe(1);
  });
});
