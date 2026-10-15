/**
 * Account statements (#810): the page asks for the period in its own URL, a
 * member's 403 becomes the "admins only" state, a refused period shows the
 * API's sentence, and the PDF streams through with the caller's own token.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('$app/env/public', () => ({ PUBLIC_DJANGO_API_URL: 'http://api.test' }));
const apiRequest = vi.fn();
vi.mock('#lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { statementQuery, previousMonth, getStatement, forwardStatementPdf } =
  await import('./statements.js');

const ACCOUNT = '11111111-2222-3333-4444-555555555555';
const OCTOBER = 'start_date=2026-10-01&end_date=2026-10-31';
const cookies = /** @type {any} */ ({ get: () => 'tok' });

/** What `apiRequest` throws: the status and the parsed body travel with it. */
const refusal = (/** @type {number} */ status, /** @type {any} */ body = {}) =>
  Object.assign(new Error(`HTTP ${status}`), { status, body });

describe('statementQuery', () => {
  it('keeps the two dates and nothing else', () => {
    const params = new URLSearchParams(`${OCTOBER}&limit=5&org=x`);
    expect(statementQuery(params)).toBe(`?${OCTOBER}`);
  });

  it('leaves blank dates out, so the API default applies', () => {
    expect(statementQuery(new URLSearchParams('start_date=&end_date=2026-10-31'))).toBe(
      '?end_date=2026-10-31'
    );
    expect(statementQuery(new URLSearchParams())).toBe('');
  });
});

describe('previousMonth', () => {
  it('is the whole calendar month before the one a date falls in', () => {
    expect(previousMonth('2026-10-15')).toEqual({
      start_date: '2026-09-01',
      end_date: '2026-09-30'
    });
  });

  it('crosses a year and knows a leap February', () => {
    expect(previousMonth('2026-01-05')).toEqual({
      start_date: '2025-12-01',
      end_date: '2025-12-31'
    });
    expect(previousMonth('2024-03-31')).toEqual({
      start_date: '2024-02-01',
      end_date: '2024-02-29'
    });
  });
});

describe('getStatement', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('asks for the account and period, and reads money as numbers', async () => {
    apiRequest.mockResolvedValue({
      account: { id: ACCOUNT, name: 'Acme' },
      start_date: '2026-10-01',
      end_date: '2026-10-31',
      currencies: [
        {
          currency: 'USD',
          opening_balance: '60.00',
          invoiced: '250.00',
          paid: '160.00',
          cancelled: '0.00',
          closing_balance: '150.00',
          entries: [
            {
              date: '2026-10-05',
              kind: 'invoice',
              invoice_id: 'inv-1',
              invoice_number: 'INV-1',
              description: 'Build',
              amount: '250.00',
              balance: '310.00'
            },
            {
              date: '2026-10-12',
              kind: 'payment',
              invoice_id: 'inv-1',
              invoice_number: 'INV-1',
              description: 'Payment (Bank Transfer)',
              amount: '-100.00',
              balance: '210.00'
            }
          ]
        }
      ]
    });

    const result = await getStatement({ cookies }, ACCOUNT, new URLSearchParams(OCTOBER));

    expect(apiRequest.mock.calls[0][0]).toBe(`/invoices/statements/${ACCOUNT}/?${OCTOBER}`);
    expect(result.can_view).toBe(true);
    expect(result.error).toBeNull();
    const usd = result.statement.currencies[0];
    expect(usd).toMatchObject({
      currency: 'USD',
      opening_balance: 60,
      invoiced: 250,
      paid: 160,
      cancelled: 0,
      closing_balance: 150
    });
    expect(usd.entries.map((/** @type {any} */ e) => [e.kind, e.amount, e.balance])).toEqual([
      ['invoice', 250, 310],
      ['payment', -100, 210]
    ]);
  });

  it('tells a member it is for admins rather than failing', async () => {
    apiRequest.mockRejectedValue(refusal(403, { error: true, message: 'Only an administrator' }));
    const result = await getStatement({ cookies }, ACCOUNT, new URLSearchParams());
    expect(result).toEqual({ can_view: false, statement: null, error: null });
  });

  it("shows the API's reason for refusing a period", async () => {
    apiRequest.mockRejectedValue(
      refusal(400, { end_date: ['A statement can cover at most 366 days.'] })
    );
    const result = await getStatement({ cookies }, ACCOUNT, new URLSearchParams(OCTOBER));
    expect(result).toEqual({
      can_view: true,
      statement: null,
      error: 'A statement can cover at most 366 days.'
    });
  });

  it('answers a missing account with a 404', async () => {
    apiRequest.mockRejectedValue(refusal(404, { error: true, message: 'Account not found' }));
    await expect(getStatement({ cookies }, ACCOUNT, new URLSearchParams())).rejects.toMatchObject({
      status: 404
    });
  });

  it('lets any other failure through', async () => {
    const boom = refusal(500);
    apiRequest.mockRejectedValue(boom);
    await expect(getStatement({ cookies }, ACCOUNT, new URLSearchParams())).rejects.toBe(boom);
  });
});

describe('forwardStatementPdf', () => {
  /** @type {import('vitest').Mock} */
  let fetchMock;

  beforeEach(() => {
    fetchMock = vi.fn(
      async () =>
        new Response('%PDF-1.7', {
          status: 200,
          headers: {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="Statement_2026-10-01_2026-10-31.pdf"'
          }
        })
    );
    vi.stubGlobal('fetch', fetchMock);
  });

  const event = (/** @type {Record<string, string>} */ jar) =>
    /** @type {any} */ ({
      cookies: { get: (/** @type {string} */ k) => jar[k] },
      params: { id: ACCOUNT },
      url: new URL(`http://app.test/accounts/${ACCOUNT}/statement/pdf?${OCTOBER}&limit=9`),
      request: new Request('http://app.test/')
    });

  it('refuses without a session and never calls the API', async () => {
    const res = await forwardStatementPdf(event({}));
    expect(res.status).toBe(401);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("sends the caller's token and the period, and passes the PDF through", async () => {
    const res = await forwardStatementPdf(event({ jwt_access: 'tok' }));
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`http://api.test/api/invoices/statements/${ACCOUNT}/pdf/?${OCTOBER}`);
    expect(init.headers).toEqual({ Authorization: 'Bearer tok' });
    expect(res.status).toBe(200);
    expect(res.headers.get('Content-Type')).toBe('application/pdf');
    expect(res.headers.get('Content-Disposition')).toBe(
      'attachment; filename="Statement_2026-10-01_2026-10-31.pdf"'
    );
    expect(await res.text()).toBe('%PDF-1.7');
  });

  it('passes a refusal through as a refusal, never as a PDF', async () => {
    fetchMock.mockResolvedValueOnce(new Response('{}', { status: 403 }));
    const res = await forwardStatementPdf(event({ jwt_access: 'tok' }));
    expect(res.status).toBe(403);
    expect(res.headers.get('Content-Type')).not.toBe('application/pdf');
  });
});
