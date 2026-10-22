import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { loadRelated, relatedActions } = await import('#lib/server/v2/related-records.js');

const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });
const ID = '0b9f4c6e-3f0a-4a5b-9a77-1c2d3e4f5a6b';
const REC = '1c9f4c6e-3f0a-4a5b-9a77-1c2d3e4f5a6c';
const status = (n, body) => Object.assign(new Error('failed'), { status: n, body });

/** @param {Record<string, string>} values */
function post(values) {
  const form = new FormData();
  for (const [k, v] of Object.entries(values)) form.set(k, v);
  return { cookies: event.cookies, params: { id: ID }, request: { formData: async () => form } };
}

beforeEach(() => {
  apiRequest.mockReset();
});

describe('loadRelated', () => {
  it('loads nothing, quietly, where the server has no custom objects', async () => {
    apiRequest.mockRejectedValueOnce(status(404));
    expect(await loadRelated(event, 'lead', ID)).toBeNull();
    expect(apiRequest.mock.calls[0][1]).toMatchObject({ quietErrors: true });
  });

  it('answers the related payload', async () => {
    const answer = { groups: [], can_edit: false, link_fields: [] };
    apiRequest.mockResolvedValueOnce(answer);
    expect(await loadRelated(event, 'lead', ID)).toBe(answer);
  });
});

describe('relatedActions', () => {
  it('asks to choose a record when Add arrives empty, without calling the API', async () => {
    const out = await relatedActions('lead').relatedAdd(
      /** @type {any} */ (post({ record: '', field: 'property:enquiries' }))
    );
    expect(out).toMatchObject({
      status: 400,
      data: { related: { error: 'Choose a record to add.' } }
    });
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('adds through the API with the page record as the target', async () => {
    apiRequest.mockResolvedValueOnce({ added: true });
    const out = await relatedActions('lead').relatedAdd(
      /** @type {any} */ (post({ record: REC, field: 'property:enquiries' }))
    );
    expect(out).toEqual({ related: { done: true } });
    expect(apiRequest).toHaveBeenCalledWith(
      '/objects/related/',
      { method: 'POST', body: { to: 'lead', id: ID, record: REC, field: 'enquiries' } },
      expect.anything()
    );
  });

  it('removes through the API', async () => {
    apiRequest.mockResolvedValueOnce(null);
    const out = await relatedActions('deal').relatedRemove(
      /** @type {any} */ (post({ record: REC, field: 'enquiries' }))
    );
    expect(out).toEqual({ related: { done: true } });
    expect(apiRequest.mock.calls[0][0]).toContain('to=deal');
    expect(apiRequest.mock.calls[0][1]).toEqual({ method: 'DELETE' });
  });

  it('refuses a malformed record id before calling the API', async () => {
    const out = /** @type {any} */ (
      await relatedActions('lead').relatedAdd(
        /** @type {any} */ (post({ record: 'nope', field: 'property:enquiries' }))
      )
    );
    expect(out.status).toBe(400);
    expect(out.data.related.error).toBe('No such record, or you cannot open it.');
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('refuses a malformed object or field key before calling the API', async () => {
    for (const field of ['Bad:enquiries', 'property:Bad Key', '', 'a:b:c']) {
      const out = /** @type {any} */ (
        await relatedActions('lead').relatedAdd(/** @type {any} */ (post({ record: REC, field })))
      );
      expect(out.status).toBe(400);
    }
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('passes the API status through', async () => {
    apiRequest.mockRejectedValueOnce(status(403, { detail: 'You cannot edit this.' }));
    const out = /** @type {any} */ (
      await relatedActions('lead').relatedAdd(
        /** @type {any} */ (post({ record: REC, field: 'property:enquiries' }))
      )
    );
    expect(out.status).toBe(403);
    expect(typeof out.data.related.error).toBe('string');
  });
});
