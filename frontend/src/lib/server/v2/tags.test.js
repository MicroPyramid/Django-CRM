import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { createTag, archiveTag, restoreTag } = await import('$lib/server/v2/tags.js');
// Cast rather than shaping a full Cookies mock, matching leads.test.js:
// createTag only ever calls `cookies.get`, and `apiRequest` itself is mocked
// above, so nothing here touches `getAll`/`set`/`delete`/`serialize`. Without
// the cast svelte-check flags this object against SvelteKit's full `Cookies`
// type on every call site below, which is noise for a shape the test
// deliberately keeps minimal.
const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });

describe('createTag', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('POSTs the trimmed name to /tags/ and unwraps the tag from the response envelope', async () => {
    // The real backend, `TagsListView.post`, never returns a bare tag: it
    // wraps its result as `{ error, message, tag }` on both the create
    // branch and the reactivation branch. A mock that returned a bare object
    // here would let `resp.tag ?? resp`'s fallback mask a broken unwrap.
    apiRequest.mockResolvedValue({
      error: false,
      message: 'Tag Created Successfully',
      tag: { id: 't1', name: 'urgent' }
    });
    const result = await createTag(event, { name: '  urgent  ' });

    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/tags/');
    expect(options.method).toBe('POST');
    expect(options.body.name).toBe('urgent');
    expect(result.id).toBe('t1');
    expect(result.name).toBe('urgent');
  });

  it('falls back to the raw response when it is not wrapped in a tag envelope', async () => {
    apiRequest.mockResolvedValue({ id: 't1', name: 'urgent' });
    const result = await createTag(event, { name: 'urgent' });
    expect(result.id).toBe('t1');
  });

  it('rejects an empty name before making a request', async () => {
    await expect(createTag(event, { name: '   ' })).rejects.toThrow(/name/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('never forwards a client-supplied org', async () => {
    apiRequest.mockResolvedValue({ tag: { id: 't1' } });
    await createTag(event, { name: 'urgent', org: 'attacker-org' });
    expect(apiRequest.mock.calls[0][1].body.org).toBeUndefined();
  });
});

describe('archiveTag', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('sends DELETE to the tag detail url', async () => {
    // The backend soft-archives on DELETE: it sets is_active = False and
    // returns 200 with this envelope. It never removes the row.
    apiRequest.mockResolvedValue({ error: false, message: 'Tag archived successfully' });
    await archiveTag(event, 'tag-1');
    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/tags/tag-1/');
    expect(options.method).toBe('DELETE');
  });

  it('refuses an empty id rather than calling the collection url', async () => {
    // Without this guard the url collapses to `/tags//`, and a caller that
    // lost the id would be aiming an unscoped request at the collection.
    await expect(archiveTag(event, '')).rejects.toThrow(/id/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('sends no request body, because the backend derives everything', async () => {
    apiRequest.mockResolvedValue({ error: false });
    await archiveTag(event, 'tag-1');
    expect(apiRequest.mock.calls[0][1].body).toBeUndefined();
  });
});

describe('restoreTag', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('posts to the restore url', async () => {
    apiRequest.mockResolvedValue({ error: false });
    await restoreTag(event, 'tag-1');
    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/tags/tag-1/restore/');
    expect(options.method).toBe('POST');
  });

  it('refuses an empty id', async () => {
    await expect(restoreTag(event, '')).rejects.toThrow(/id/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
