import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

vi.mock('$app/env/public', () => ({ PUBLIC_DJANGO_API_URL: 'http://api.test' }));

const { apiRequest } = await import('#lib/api-helpers.js');
const cookies = /** @type {any} */ ({ get: () => 'token' });

/** @param {number} status @param {any} body */
function answer(status, body) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status,
      statusText: 'x',
      json: async () => body
    })
  );
}

describe('apiRequest expectedStatuses', () => {
  /** @type {import('vitest').MockInstance} */
  let logged;
  beforeEach(() => {
    logged = vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    logged.mockRestore();
  });

  it('throws an expected status with its status and body, and logs nothing', async () => {
    answer(404, { detail: 'Not found.' });
    await expect(
      apiRequest('/objects/', { quietErrors: true, expectedStatuses: [404] }, { cookies })
    ).rejects.toMatchObject({ status: 404, body: { detail: 'Not found.' } });
    expect(logged).not.toHaveBeenCalled();
  });

  it('logs nothing for an expected status without quietErrors either', async () => {
    answer(404, {});
    await expect(
      apiRequest('/objects/', { expectedStatuses: [404] }, { cookies })
    ).rejects.toMatchObject({ status: 404 });
    expect(logged).not.toHaveBeenCalled();
  });

  it('still logs a status that is not expected', async () => {
    answer(500, { detail: 'boom' });
    await expect(
      apiRequest('/objects/', { quietErrors: true, expectedStatuses: [404] }, { cookies })
    ).rejects.toMatchObject({ status: 500 });
    expect(logged).toHaveBeenCalled();
  });

  it('is unchanged without the option', async () => {
    answer(404, {});
    await expect(apiRequest('/objects/', { quietErrors: true }, { cookies })).rejects.toMatchObject(
      { status: 404 }
    );
    expect(logged).toHaveBeenCalled();
  });
});

describe('apiRequest and a switched-off module', () => {
  /** @type {import('vitest').MockInstance} */
  let logged;
  beforeEach(() => {
    logged = vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    logged.mockRestore();
  });

  const refusal = {
    detail: 'Tickets is switched off for this organization.',
    code: 'module_off',
    module: 'tickets'
  };

  it('throws a module_off refusal with its body and logs nothing', async () => {
    for (const options of [{}, { quietErrors: true }]) {
      answer(404, refusal);
      await expect(apiRequest('/cases/', options, { cookies })).rejects.toMatchObject({
        status: 404,
        body: refusal
      });
    }
    expect(logged).not.toHaveBeenCalled();
  });

  it('still logs any other 404', async () => {
    answer(404, { detail: 'Not found.', code: 'not_found' });
    await expect(apiRequest('/cases/x/', {}, { cookies })).rejects.toMatchObject({ status: 404 });
    expect(logged).toHaveBeenCalled();
  });
});
