import { describe, it, expect } from 'vitest';
import { todayIn, addDays, wallTimeToIso } from '#lib/v2/dates.js';

describe('todayIn', () => {
  // 23:30 UTC on 31 Dec is 05:00 on 1 Jan in Kolkata (UTC+5:30).
  const lateNewYearsEve = new Date('2025-12-31T23:30:00Z');

  it('is the org’s day across a UTC midnight boundary', () => {
    expect(todayIn('Asia/Kolkata', lateNewYearsEve)).toBe('2026-01-01');
  });

  it('is still the old day west of UTC', () => {
    expect(todayIn('America/New_York', lateNewYearsEve)).toBe('2025-12-31');
    expect(todayIn('UTC', lateNewYearsEve)).toBe('2025-12-31');
  });

  it('is the prior day in the Americas after UTC midnight', () => {
    expect(todayIn('America/Los_Angeles', new Date('2026-03-01T03:00:00Z'))).toBe('2026-02-28');
  });

  it('reads a legacy zone name as its IANA target', () => {
    expect(todayIn('US/Eastern', lateNewYearsEve)).toBe('2025-12-31');
  });

  it('falls back to UTC for a zone the runtime does not know', () => {
    expect(todayIn('Not/AZone', lateNewYearsEve)).toBe('2025-12-31');
  });
});

describe('addDays', () => {
  it('crosses a month and a year', () => {
    expect(addDays('2026-12-15', 30)).toBe('2027-01-14');
    expect(addDays('2026-01-31', 1)).toBe('2026-02-01');
  });

  it('is not moved by a DST change', () => {
    expect(addDays('2026-03-07', 2)).toBe('2026-03-09');
  });
});

describe('wallTimeToIso', () => {
  it('reads the wall clock in the org’s zone', () => {
    expect(wallTimeToIso('2026-10-24T14:30', 'Asia/Kolkata')).toBe('2026-10-24T09:00:00.000Z');
    expect(wallTimeToIso('2026-10-24T14:30', 'UTC')).toBe('2026-10-24T14:30:00.000Z');
    expect(wallTimeToIso('2026-01-15T09:05:30', 'America/New_York')).toBe(
      '2026-01-15T14:05:30.000Z'
    );
  });

  it('follows daylight saving on either side of the change', () => {
    // New York moved to EDT (UTC-4) at 02:00 on 8 March 2026.
    expect(wallTimeToIso('2026-03-07T12:00', 'America/New_York')).toBe('2026-03-07T17:00:00.000Z');
    expect(wallTimeToIso('2026-03-09T12:00', 'America/New_York')).toBe('2026-03-09T16:00:00.000Z');
  });

  it('refuses what is not a datetime-local value or not a real date', () => {
    expect(wallTimeToIso('', 'UTC')).toBeNull();
    expect(wallTimeToIso(null, 'UTC')).toBeNull();
    expect(wallTimeToIso('2026-10-24', 'UTC')).toBeNull();
    expect(wallTimeToIso('2026-02-31T10:00', 'UTC')).toBeNull();
    expect(wallTimeToIso('2026-10-24T25:00', 'UTC')).toBeNull();
    expect(wallTimeToIso('2026-10-24T10:00Z', 'UTC')).toBeNull();
  });

  it('reads an unknown zone as UTC', () => {
    expect(wallTimeToIso('2026-10-24T14:30', 'Not/AZone')).toBe('2026-10-24T14:30:00.000Z');
  });
});
