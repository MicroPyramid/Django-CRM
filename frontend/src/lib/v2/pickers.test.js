import { describe, it, expect } from 'vitest';

import { missingOption, missingOptions, inactiveOptionLabel } from './pickers.js';

const people = [
  { id: 'p1', name: 'Ada Lovelace' },
  { id: 'p2', name: 'Grace Hopper' }
];

describe('missingOptions', () => {
  it('returns the stored entries the options list cannot offer', () => {
    const stored = [{ id: 'p1' }, { id: 'gone', email: 'left@x.io' }];
    expect(missingOptions(people, stored)).toEqual([{ id: 'gone', email: 'left@x.io' }]);
  });

  it('returns nothing when every stored entry is in the list', () => {
    expect(missingOptions(people, [{ id: 'p1' }, { id: 'p2' }])).toEqual([]);
  });

  it('keeps the stored order', () => {
    const stored = [{ id: 'a' }, { id: 'p1' }, { id: 'b' }];
    expect(missingOptions(people, stored).map((s) => s.id)).toEqual(['a', 'b']);
  });

  it('treats an empty options list as offering nothing', () => {
    // What a failed `getOrgPeopleAndTeams` fetch looks like. Keeping the
    // stored value is still the right outcome: the form cannot offer an
    // alternative, so discarding it would be pure loss.
    expect(missingOptions([], [{ id: 'p1' }])).toEqual([{ id: 'p1' }]);
  });

  it('survives null and undefined on either side', () => {
    expect(missingOptions(null, null)).toEqual([]);
    expect(missingOptions(undefined, undefined)).toEqual([]);
    expect(missingOptions(people, undefined)).toEqual([]);
  });

  it('ignores stored entries with no id', () => {
    expect(missingOptions(people, [null, {}, { id: '' }])).toEqual([]);
  });
});

describe('missingOption', () => {
  it('returns the stored target when the list cannot offer it', () => {
    expect(missingOption(people, { id: 'gone', name: 'Departed' })).toEqual({
      id: 'gone',
      name: 'Departed'
    });
  });

  it('returns null when the list can offer it', () => {
    expect(missingOption(people, { id: 'p1', name: 'Ada Lovelace' })).toBeNull();
  });

  it('returns null when nothing is stored', () => {
    expect(missingOption(people, null)).toBeNull();
    expect(missingOption(people, undefined)).toBeNull();
  });
});

describe('inactiveOptionLabel', () => {
  it('says the target is no longer active', () => {
    expect(inactiveOptionLabel('Ada Lovelace')).toBe('Ada Lovelace (no longer active)');
  });

  it('falls back to Unnamed rather than rendering null', () => {
    // Both `shapeTarget` and `shapeAssignee` resolve a missing
    // `user_details.name` to null, so a bare interpolation would read
    // "null (no longer active)".
    expect(inactiveOptionLabel(null)).toBe('Unnamed (no longer active)');
    expect(inactiveOptionLabel('')).toBe('Unnamed (no longer active)');
  });
});
