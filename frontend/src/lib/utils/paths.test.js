import { describe, expect, it } from 'vitest';
import { asInternalPath } from '#lib/utils/paths.js';

describe('asInternalPath', () => {
  it('drops the leading slash so resolve() reads a pathname, not a route ID', () => {
    expect(asInternalPath('/leads/board?pipeline=p1')).toBe('leads/board?pipeline=p1');
  });

  it('turns the root into the empty pathname', () => {
    expect(asInternalPath('/')).toBe('');
  });

  it('leaves a path without a leading slash alone', () => {
    expect(asInternalPath('leads')).toBe('leads');
  });
});
