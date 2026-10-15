import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { actions } = await import('./+page.server.js');

/** @param {Record<string, string>} fields */
function saveEvent(fields) {
  const body = new FormData();
  for (const [key, value] of Object.entries(fields)) body.set(key, value);
  return /** @type {any} */ ({
    request: new Request('http://test/settings/organization/edit?/save', { method: 'POST', body }),
    cookies: { get: () => 'token' }
  });
}

describe('organization save action', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('sends the numbering settings (#802), trimmed', async () => {
    apiRequest.mockResolvedValue({});
    await expect(
      actions.save(
        saveEvent({
          invoice_number_prefix: ' INVNSD- ',
          estimate_number_prefix: 'ESTNSD-',
          number_date_part: 'NONE',
          number_padding: '5',
          invoice_number_start: '1042'
        })
      )
    ).rejects.toMatchObject({ status: 303, location: '/settings/organization' });

    expect(apiRequest.mock.calls[0][0]).toBe('/org/settings/');
    expect(apiRequest.mock.calls[0][1]).toMatchObject({ method: 'PATCH' });
    expect(apiRequest.mock.calls[0][1].body).toEqual({
      invoice_number_prefix: 'INVNSD-',
      estimate_number_prefix: 'ESTNSD-',
      number_date_part: 'NONE',
      number_padding: '5',
      invoice_number_start: '1042'
    });
  });

  it('sends nothing the form does not offer', async () => {
    apiRequest.mockResolvedValue({});
    await expect(
      actions.save(saveEvent({ name: 'Acme', api_key: 'x', is_active: 'false' }))
    ).rejects.toMatchObject({ status: 303 });
    expect(apiRequest.mock.calls[0][1].body).toEqual({ name: 'Acme' });
  });

  it("keeps the server's reason when it refuses", async () => {
    apiRequest.mockRejectedValue(
      Object.assign(new Error('A starting number only applies to numbers without a date.'), {
        status: 400
      })
    );
    const result = /** @type {any} */ (
      await actions.save(saveEvent({ number_date_part: 'YEAR', invoice_number_start: '1042' }))
    );
    expect(result.status).toBe(400);
    expect(result.data.error).toContain('only applies to numbers without a date');
  });
});
