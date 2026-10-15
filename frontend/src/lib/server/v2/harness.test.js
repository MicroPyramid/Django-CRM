import { describe, it, expect } from 'vitest';
import { EDITABLE_FIELDS } from '#lib/server/v2/leads.js';

describe('vitest harness', () => {
  it('resolves #lib subpath imports into server modules', () => {
    expect(Array.isArray(EDITABLE_FIELDS)).toBe(true);
    expect(EDITABLE_FIELDS).toContain('first_name');
  });
});
