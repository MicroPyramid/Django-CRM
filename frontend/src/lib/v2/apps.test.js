import { describe, it, expect } from 'vitest';
import { updateLine } from './apps.js';

describe('updateLine', () => {
  it('names the version when it is newer', () => {
    expect(updateLine({ version: 2, installedVersion: 1 })).toBe('Version 2 adds more.');
  });

  it('explains a same-version update, numbers or strings', () => {
    const copy = 'An update adds the parts skipped while a module was off.';
    expect(updateLine({ version: 2, installedVersion: '2' })).toBe(copy);
    expect(updateLine({ version: '1.1', installedVersion: '1.1' })).toBe(copy);
  });

  it('falls back when the version is unknown', () => {
    expect(updateLine({ version: null, installedVersion: 1 })).toBe('An update adds more.');
  });
});
