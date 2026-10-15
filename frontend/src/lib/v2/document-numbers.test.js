import { describe, it, expect } from 'vitest';
import {
  exampleNumber,
  numberPattern,
  numberSeries,
  NUMBER_PREFIX_PATTERN
} from '$lib/v2/document-numbers.js';

describe('numberSeries', () => {
  const today = '2026-10-15';

  it('is the format every org had before numbering was a setting', () => {
    expect(numberSeries('INV-', 'DAY', today)).toBe('INV-20261015-');
  });

  it('carries the year, or the year and month, then a hyphen', () => {
    expect(numberSeries('INV-', 'YEAR', today)).toBe('INV-2026-');
    expect(numberSeries('EST-', 'MONTH', today)).toBe('EST-202610-');
  });

  it('is the prefix alone when numbers are undated', () => {
    expect(numberSeries('INV-', 'NONE', today)).toBe('INV-');
    expect(numberSeries('INV', 'NONE', today)).toBe('INV');
    expect(numberSeries('', 'NONE', today)).toBe('');
  });
});

describe('NUMBER_PREFIX_PATTERN', () => {
  it('takes letters, digits, hyphens and underscores, or nothing', () => {
    for (const prefix of ['', 'INV', 'INVNSD-', 'A_1']) {
      expect(NUMBER_PREFIX_PATTERN.test(prefix)).toBe(true);
    }
  });

  it('refuses what the server refuses', () => {
    for (const prefix of ['INV/', 'INV 1', 'INV"', 'FACTÜRA-', 'INV\n']) {
      expect(NUMBER_PREFIX_PATTERN.test(prefix)).toBe(false);
    }
  });
});

describe('exampleNumber', () => {
  const today = '2026-10-15';
  const defaults = {
    invoice_number_prefix: 'INV-',
    estimate_number_prefix: 'EST-',
    number_date_part: 'DAY',
    number_padding: 4,
    invoice_number_start: 1
  };

  it('is the first number of a series in the org’s format', () => {
    expect(exampleNumber(defaults, 'invoice', today)).toBe('INV-20261015-0001');
    expect(exampleNumber(defaults, 'estimate', today)).toBe('EST-20261015-0001');
  });

  it('starts an undated invoice count where the org asked', () => {
    const carried = { ...defaults, number_date_part: 'NONE', invoice_number_start: 1042 };
    expect(exampleNumber(carried, 'invoice', today)).toBe('INV-1042');
    // The start is for invoices only.
    expect(exampleNumber(carried, 'estimate', today)).toBe('EST-0001');
  });

  it('starts a dated count at 1, whatever start the form still holds', () => {
    const dated = { ...defaults, number_date_part: 'YEAR', invoice_number_start: 1042 };
    expect(exampleNumber(dated, 'invoice', today)).toBe('INV-2026-0001');
  });

  it('pads to the width, and survives a width still being typed', () => {
    expect(exampleNumber({ ...defaults, number_padding: 6 }, 'invoice', today)).toBe(
      'INV-20261015-000001'
    );
    expect(exampleNumber({ ...defaults, number_padding: '' }, 'invoice', today)).toBe(
      'INV-20261015-1'
    );
    expect(exampleNumber({ ...defaults, number_padding: 1e9 }, 'invoice', today)).toBe(
      'INV-20261015-0000000001'
    );
  });
});

describe('numberPattern', () => {
  const settings = {
    invoice_number_prefix: 'INVNSD-',
    estimate_number_prefix: 'ESTNSD-',
    number_date_part: 'YEAR',
    number_padding: 5,
    invoice_number_start: 1
  };

  it('shows the series and the counter width, not a number nobody holds yet', () => {
    expect(numberPattern(settings, 'invoice', '2026-10-15')).toBe('INVNSD-2026-nnnnn');
    expect(numberPattern(settings, 'estimate', '2026-10-15')).toBe('ESTNSD-2026-nnnnn');
  });
});
