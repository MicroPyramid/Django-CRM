import { describe, it, expect } from 'vitest';
import {
  LEGACY_LEAD_SOURCES,
  moveKeys,
  sourceFilterOptions,
  sourceLabel,
  sourceOptions
} from './lead-sources.js';

const S = [
  { id: 'a', key: 'call', label: 'Call', is_active: true, order: 0 },
  { id: 'b', key: 'fax', label: 'Fax', is_active: false, order: 1 },
  { id: 'c', key: 'walk-in', label: 'Walk-in', is_active: true, order: 2 }
];

describe('sourceOptions', () => {
  it('offers the active sources only, for a new record', () => {
    expect(sourceOptions(S, '')).toEqual([
      { key: 'call', label: 'Call', retired: false },
      { key: 'walk-in', label: 'Walk-in', retired: false }
    ]);
  });

  it('keeps a retired current value first, labelled', () => {
    expect(sourceOptions(S, 'fax')[0]).toEqual({
      key: 'fax',
      label: 'Fax (retired)',
      retired: true
    });
  });

  it('keeps a value the list has never had, so a save does not drop it', () => {
    expect(sourceOptions(S, 'WEBSITE')[0]).toEqual({
      key: 'WEBSITE',
      label: 'WEBSITE (retired)',
      retired: true
    });
    expect(sourceOptions([], 'google ads').map((o) => o.key)).toEqual(['google ads']);
  });
});

describe('sourceLabel', () => {
  it('reads the label, falling back to the key, and empty for none', () => {
    expect(sourceLabel(S, 'walk-in')).toBe('Walk-in');
    expect(sourceLabel(S, 'zillow')).toBe('zillow');
    expect(sourceLabel(S, '')).toBe('');
    expect(sourceLabel(null, 'call')).toBe('call');
  });
});

describe('sourceFilterOptions', () => {
  it('lists every source, retired ones marked', () => {
    expect(sourceFilterOptions(S)).toEqual([
      { id: 'call', name: 'Call' },
      { id: 'fax', name: 'Fax (retired)' },
      { id: 'walk-in', name: 'Walk-in' }
    ]);
  });
});

describe('moveKeys', () => {
  it('swaps with the neighbour', () => {
    expect(moveKeys(S, 'fax', 'up')).toEqual(['fax', 'call', 'walk-in']);
    expect(moveKeys(S, 'fax', 'down')).toEqual(['call', 'walk-in', 'fax']);
  });

  it('refuses a move off either end, an unknown key or direction', () => {
    expect(moveKeys(S, 'call', 'up')).toBeNull();
    expect(moveKeys(S, 'walk-in', 'down')).toBeNull();
    expect(moveKeys(S, 'nope', 'up')).toBeNull();
    expect(moveKeys(S, 'fax', 'sideways')).toBeNull();
  });
});

describe('LEGACY_LEAD_SOURCES', () => {
  it('is the seven keys an API without the list validates against', () => {
    expect(LEGACY_LEAD_SOURCES.map((s) => s.key)).toEqual([
      'call',
      'email',
      'existing customer',
      'partner',
      'public relations',
      'compaign',
      'other'
    ]);
    expect(sourceLabel(LEGACY_LEAD_SOURCES, 'compaign')).toBe('Campaign');
  });
});
