import { describe, it, expect } from 'vitest';
import {
  cleanMapping,
  deliveryResult,
  intakeState,
  mappingTargets,
  presetLabel,
  presetSource,
  targetsFor
} from './lead-intakes.js';

describe('presetSource', () => {
  const sources = [
    { key: 'web form', is_active: true },
    { key: 'google ads', is_active: false }
  ];

  it('starts a webhook on its preset’s usual source when the org has it on', () => {
    expect(presetSource('tally', sources)).toBe('web form');
    expect(presetSource('generic', sources)).toBe('web form');
  });

  it('leaves the choice empty when that source is retired or missing', () => {
    expect(presetSource('google_ads', sources)).toBe('');
    expect(presetSource('google_ads', [])).toBe('');
    expect(presetSource('unknown', sources)).toBe('');
  });
});

describe('mapping targets', () => {
  it('offers the web forms’ lead columns, then the custom fields', () => {
    const targets = mappingTargets([{ key: 'budget', label: 'Budget' }]);
    expect(targets[0]).toEqual({ value: 'salutation', label: 'Salutation' });
    expect(targets.some((t) => t.value === 'email')).toBe(true);
    expect(targets.at(-1)).toEqual({ value: 'custom_fields.budget', label: 'Budget' });
    expect(targets.some((t) => t.value === 'assigned_to')).toBe(false);
  });

  it('keeps a stored target the list cannot offer', () => {
    const targets = mappingTargets([]);
    const all = targetsFor(targets, [
      { from: 'lead_id', to: 'external_id' },
      { from: 'a', to: 'email' }
    ]);
    expect(all.length).toBe(targets.length + 1);
    expect(all.at(-1)).toEqual({ value: 'external_id', label: 'external_id' });
  });
});

describe('cleanMapping', () => {
  it('keeps complete rows, trimmed, and nothing else', () => {
    expect(
      cleanMapping([
        { from: ' a.b ', to: ' email ', id: 'x' },
        { from: '', to: 'phone' },
        { from: 'c', to: '' },
        null,
        { from: 3, to: 'x' }
      ])
    ).toEqual([{ from: 'a.b', to: 'email' }]);
    expect(cleanMapping('nope')).toEqual([]);
  });
});

describe('labels and states', () => {
  it('names presets and delivery results', () => {
    expect(presetLabel('tally')).toBe('Tally');
    expect(presetLabel('nope')).toBe('Any tool');
    expect(deliveryResult('rejected')).toEqual({ label: 'Rejected', tone: 'rust' });
    expect(deliveryResult('other')).toEqual({ label: 'other', tone: 'slate' });
  });

  it('reads a webhook as off, waiting for its first post, or receiving', () => {
    expect(intakeState({ is_active: false, last_received_at: 'x' }).label).toBe('Off');
    expect(intakeState({ is_active: true, last_received_at: null }).label).toBe('Waiting');
    expect(intakeState({ is_active: true, last_received_at: 'x' })).toEqual({
      label: 'Receiving',
      tone: 'moss'
    });
  });
});
