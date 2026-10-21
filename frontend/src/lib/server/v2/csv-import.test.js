import { inspect } from 'node:util';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { forwardCsvImport } = await import('#lib/server/v2/csv-import.js');
/** @type {typeof import('#lib/api-helpers.js')} */
const actual = await vi.importActual('#lib/api-helpers.js');

/** @param {Record<string, string | File>} fields */
function event(fields) {
  const form = new FormData();
  for (const [k, v] of Object.entries(fields)) form.set(k, v);
  return /** @type {any} */ ({
    request: new Request('http://x/contacts?/importPreview', { method: 'POST', body: form }),
    cookies: { get: () => 'token' }
  });
}

const sheet = () => new File(['Name,Email\nAda,ada@x.test\n'], 'people.csv');

/** @param {number} status @param {any} body */
function httpError(status, body) {
  return Object.assign(new Error('x'), { status, body });
}

describe('forwardCsvImport', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('forwards the mapping field with the file', async () => {
    apiRequest.mockResolvedValue({ columns: [] });
    const out = await forwardCsvImport(
      event({ file: sheet(), mapping: '{"0":"full_name","1":null}' }),
      '/contacts/import/preview/',
      'importPreview'
    );
    expect(out).toEqual({ importPreview: { columns: [] } });
    const body = apiRequest.mock.calls[0][1].body;
    expect(body.get('mapping')).toBe('{"0":"full_name","1":null}');
    expect(body.get('file').name).toBe('people.csv');
  });

  it('sends no mapping when the form has none, keeping the template path', async () => {
    apiRequest.mockResolvedValue({});
    await forwardCsvImport(event({ file: sheet() }), '/leads/import/preview/', 'importPreview');
    expect(apiRequest.mock.calls[0][1].body.has('mapping')).toBe(false);
  });

  it('asks for a file when none was chosen', async () => {
    const out = await forwardCsvImport(
      event({ mapping: 'auto' }),
      '/contacts/import/preview/',
      'importPreview'
    );
    expect(out.status).toBe(400);
    expect(out.data.importError).toBe('Choose a file.');
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('passes the skipped rows through when nothing can be imported', async () => {
    const skipped = [
      { row: 1, field: 'email', message: 'A lead with this email already exists', cells: ['Ada'] }
    ];
    apiRequest.mockRejectedValue(
      httpError(400, {
        error: true,
        message: 'Nothing in this file can be imported.',
        skipped,
        created: 0
      })
    );
    const out = await forwardCsvImport(
      event({ file: sheet(), mapping: 'auto' }),
      '/leads/import/commit/',
      'importCommit'
    );
    expect(out.status).toBe(400);
    expect(out.data.importError).toBe('Nothing in this file can be imported.');
    expect(out.data.importSkipped).toEqual(skipped);
  });

  it('turns the throttle into a sentence', async () => {
    apiRequest.mockRejectedValue(
      httpError(429, { detail: 'Request was throttled. Expected available in 20 seconds.' })
    );
    const out = await forwardCsvImport(
      event({ file: sheet(), mapping: 'auto' }),
      '/contacts/import/preview/',
      'importPreview'
    );
    expect(out.status).toBe(429);
    expect(out.data.importError).toBe('Too many tries in a minute. Wait a moment, then try again.');
  });

  it('keeps the permission sentence for a refused role', async () => {
    apiRequest.mockRejectedValue(httpError(403, { error: true, message: 'Permission denied' }));
    const out = await forwardCsvImport(
      event({ file: sheet(), mapping: 'auto' }),
      '/contacts/import/preview/',
      'importPreview'
    );
    expect(out.status).toBe(403);
    expect(out.data.importError).toBe('Importing needs an admin, or a member with sales access.');
    expect(out.data.importSkipped).toEqual([]);
  });
});

describe('import error logging', () => {
  const CELL = 'ada.private@cell.test';
  const reply = {
    error: true,
    message: 'Nothing in this file can be imported.',
    created: 0,
    skipped: [
      {
        row: 1,
        field: 'email',
        message: 'A lead with this email already exists',
        cells: ['Ada', CELL],
        kind: 'duplicate'
      }
    ]
  };
  /** @type {string[]} */
  let logged;

  beforeEach(() => {
    logged = [];
    for (const level of /** @type {const} */ (['error', 'warn', 'log', 'info', 'debug'])) {
      vi.spyOn(console, level).mockImplementation((...args) => {
        logged.push(
          args.map((a) => (typeof a === 'string' ? a : inspect(a, { depth: Infinity }))).join(' ')
        );
      });
    }
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify(reply), { status: 400 }))
    );
    apiRequest.mockReset();
    apiRequest.mockImplementation(actual.apiRequest);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("never logs a skipped row's cells, and still hands them to the client", async () => {
    const out = await forwardCsvImport(
      event({ file: sheet(), mapping: 'auto' }),
      '/leads/import/commit/',
      'importCommit'
    );
    expect(out.data.importSkipped[0].cells).toEqual(['Ada', CELL]);
    const log = logged.join('\n');
    expect(log).toContain('400');
    expect(log).toContain('Nothing in this file can be imported.');
    expect(log).not.toContain(CELL);
  });

  it('would see the leak: without quietErrors the body is logged', async () => {
    await expect(
      actual.apiRequest(
        '/leads/import/commit/',
        { method: 'POST', body: new FormData() },
        { cookies: /** @type {any} */ ({ get: () => 'token' }) }
      )
    ).rejects.toThrow();
    expect(logged.join('\n')).toContain(CELL);
  });
});
