import { describe, it, expect } from 'vitest';
import { isBilled } from '#lib/v2/time-entry.js';

describe('isBilled', () => {
  it('reads an entry billed while Invoices is off as billed', () => {
    expect(isBilled({ invoiced: true, invoice: null })).toBe(true);
    expect(isBilled({ invoiced: false, invoice: null })).toBe(false);
    expect(isBilled({ invoice: 'id' })).toBe(true);
    expect(isBilled({ invoiced: false, invoice: { id: 'x' } })).toBe(true);
    expect(isBilled({})).toBe(false);
  });
});
