import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { updateBusinessHours, addHoliday, removeHoliday } =
  await import('$lib/server/v2/business-hours.js');

const event = /** @type {any} */ ({ cookies: { get: () => 'token' } });

const week = [
  { day: 'Monday', open: '09:00', close: '17:00' },
  { day: 'Tuesday', open: '09:00', close: '17:00' },
  { day: 'Wednesday', open: '09:00', close: '17:00' },
  { day: 'Thursday', open: '09:00', close: '17:00' },
  { day: 'Friday', open: '09:00', close: '17:00' },
  { day: 'Saturday', open: null, close: null },
  { day: 'Sunday', open: null, close: null }
];

describe('updateBusinessHours', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('unfolds the days array back into the fourteen flat fields', async () => {
    apiRequest.mockResolvedValue({});

    await updateBusinessHours(event, 'cal1', week, { name: 'Support', timezone: 'Asia/Kolkata' });

    const [endpoint, options] = apiRequest.mock.calls[0];
    // The detail URL, not the collection path the read uses.
    expect(endpoint).toBe('/business-hours/calendar/cal1/');
    expect(options.method).toBe('PUT');
    expect(options.body.monday_open).toBe('09:00');
    expect(options.body.friday_close).toBe('17:00');
    // A closed day is both fields null, never one of them.
    expect(options.body.saturday_open).toBeNull();
    expect(options.body.saturday_close).toBeNull();
    expect(options.body.name).toBe('Support');
    expect(options.body.timezone).toBe('Asia/Kolkata');
  });

  it('never sends is_default, which the serializer marks read-only', async () => {
    apiRequest.mockResolvedValue({});
    await updateBusinessHours(event, 'cal1', week, {
      name: 'Support',
      timezone: 'UTC',
      is_default: false
    });
    expect(apiRequest.mock.calls[0][1].body.is_default).toBeUndefined();
  });

  it('rejects a day with an open but no close, naming the day', async () => {
    const broken = week.map((d) => (d.day === 'Wednesday' ? { ...d, close: null } : d));
    await expect(
      updateBusinessHours(event, 'cal1', broken, { name: 'S', timezone: 'UTC' })
    ).rejects.toThrow(/Wednesday/);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('refuses an empty calendar id before making a request', async () => {
    await expect(
      updateBusinessHours(event, '', week, { name: 'S', timezone: 'UTC' })
    ).rejects.toThrow(/calendar/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('addHoliday', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('POSTs date and name to the calendar sub-resource', async () => {
    apiRequest.mockResolvedValue({ id: 'h1', date: '2026-12-25', name: 'Christmas' });

    await addHoliday(event, 'cal1', { date: '2026-12-25', name: 'Christmas' });

    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/business-hours/calendar/cal1/holidays/');
    expect(options.method).toBe('POST');
    expect(options.body).toEqual({ date: '2026-12-25', name: 'Christmas' });
  });

  it('rejects a missing date before making a request', async () => {
    await expect(addHoliday(event, 'cal1', { date: '', name: 'X' })).rejects.toThrow(/date/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('removeHoliday', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('DELETEs the holiday under its calendar', async () => {
    apiRequest.mockResolvedValue(null);
    await removeHoliday(event, 'cal1', 'h1');
    const [endpoint, options] = apiRequest.mock.calls[0];
    expect(endpoint).toBe('/business-hours/calendar/cal1/holidays/h1/');
    expect(options.method).toBe('DELETE');
  });
});
