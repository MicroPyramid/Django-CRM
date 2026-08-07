import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { shortDate, longDate, daysSince, relativeDays, relativeTime } from '$lib/v2/format.js';

/**
 * A date and an instant are not the same kind of value, and the API sends both.
 *
 * `created_at` is an instant: an ISO timestamp with an offset, and rendering it
 * in the reader's timezone is exactly right. `due_date`, `close_date`, and
 * every analytics bucket label are calendar dates with no time and no zone.
 * `new Date('2026-08-07')` reads those as UTC midnight, so a browser west of
 * UTC prints the day before: a ticket-volume bar the API labelled the 7th sits
 * under the 6th, and a task due Friday reads as due Thursday.
 *
 * These run pinned to New York, because in a UTC or an Indian test process the
 * bug is invisible: the shift only shows up in zones behind UTC.
 */
const REAL_TZ = process.env.TZ;

beforeAll(() => {
  process.env.TZ = 'America/New_York';
});

afterAll(() => {
  process.env.TZ = REAL_TZ;
});

describe('the test timezone', () => {
  it('is behind UTC, or none of the rest of this file discriminates', () => {
    expect(new Date('2026-08-07T00:00:00Z').getDate()).toBe(6);
  });
});

describe('a date with no time is a calendar day', () => {
  it('shortDate prints the day it was given', () => {
    expect(shortDate('2026-08-07', new Date('2026-08-07T12:00:00'))).toBe('7 Aug');
  });

  it('longDate prints the day it was given', () => {
    expect(longDate('2026-08-07')).toBe('7 August 2026');
  });

  it('a date earlier in the year still carries the year', () => {
    expect(shortDate('2023-01-01', new Date('2026-08-07T12:00:00'))).toBe('1 Jan 2023');
  });

  it('today is today, not yesterday', () => {
    expect(relativeDays('2026-08-07', new Date('2026-08-07T12:00:00'))).toBe('today');
  });

  it('and the day before is yesterday', () => {
    expect(relativeDays('2026-08-06', new Date('2026-08-07T12:00:00'))).toBe('yesterday');
  });

  it('daysSince counts from local midnight', () => {
    expect(daysSince('2026-08-07', new Date('2026-08-07T23:00:00'))).toBe(0);
  });
});

describe('a timestamp is an instant and keeps its zone', () => {
  it('an offset in the string is honoured, not overridden', () => {
    // 02:00 UTC on the 7th is 22:00 on the 6th in New York, and a reader in
    // New York should see the 6th. This is the half a naive "always treat it
    // as local" fix would break.
    expect(shortDate('2026-08-07T02:00:00Z', new Date('2026-08-07T12:00:00'))).toBe('6 Aug');
  });

  it('relativeTime still measures hours, not days', () => {
    expect(relativeTime('2026-08-07T09:00:00Z', new Date('2026-08-07T12:00:00Z'))).toBe(
      '3 hours ago'
    );
  });
});

describe('nothing to render', () => {
  it('null and an unparseable string both give the placeholder', () => {
    expect(shortDate(null)).toBe('—');
    expect(shortDate('not a date')).toBe('—');
    expect(longDate(undefined)).toBe('—');
    expect(daysSince('')).toBe(null);
  });
});
