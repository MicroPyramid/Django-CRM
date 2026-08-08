import { describe, it, expect } from 'vitest';
import { dayHours, weeklyHours, isAlwaysOn } from './week.js';

/** @param {string | null} open @param {string | null} close */
const day = (open, close) => ({ open, close });

const WORKING_WEEK = [
  day('09:00', '17:00'),
  day('09:00', '17:00'),
  day('09:00', '17:00'),
  day('09:00', '17:00'),
  day('09:00', '17:00'),
  day(null, null),
  day(null, null)
];

describe('dayHours', () => {
  it('counts a normal span', () => {
    expect(dayHours(day('09:00', '17:00'))).toBe(8);
  });

  it('counts half hours', () => {
    expect(dayHours(day('09:30', '17:00'))).toBe(7.5);
  });

  it('is zero for a closed day', () => {
    expect(dayHours(day(null, null))).toBe(0);
  });

  it('is zero for a half-set day, which the serializer refuses on write', () => {
    expect(dayHours(day('09:00', null))).toBe(0);
    expect(dayHours(day(null, '17:00'))).toBe(0);
  });

  it('is zero when close is not after open', () => {
    // The walker reads `close_t <= open_t` as closed, so this cannot count.
    expect(dayHours(day('17:00', '09:00'))).toBe(0);
    expect(dayHours(day('09:00', '09:00'))).toBe(0);
  });

  it('is zero rather than NaN for an unparseable time', () => {
    expect(dayHours(day('nine', '17:00'))).toBe(0);
  });
});

describe('weeklyHours', () => {
  it('adds the open days', () => {
    expect(weeklyHours(WORKING_WEEK)).toBe(40);
  });

  it('is zero for a week with nothing open', () => {
    expect(weeklyHours([day(null, null), day(null, null)])).toBe(0);
  });
});

describe('isAlwaysOn', () => {
  it('is false for an ordinary week', () => {
    expect(isAlwaysOn(WORKING_WEEK)).toBe(false);
  });

  it('is true when every day is closed', () => {
    // The finding: `_has_any_open_window` false means the calendar is dropped
    // and the SLA runs on the wall clock, so this is 24/7 rather than never.
    expect(isAlwaysOn(WORKING_WEEK.map(() => day(null, null)))).toBe(true);
  });

  it('one open day is enough to make the calendar count', () => {
    const week = WORKING_WEEK.map(() => day(null, null));
    week[6] = day('10:00', '11:00');
    expect(isAlwaysOn(week)).toBe(false);
  });

  it('a backwards day does not count as open', () => {
    const week = WORKING_WEEK.map(() => day(null, null));
    week[0] = day('17:00', '09:00');
    expect(isAlwaysOn(week)).toBe(true);
  });
});
