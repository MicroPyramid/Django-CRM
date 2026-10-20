import { describe, it, expect } from 'vitest';
import { todayLayout } from './today-layout.js';

const empty = { empty_workspace: true, can_import: true };

describe('todayLayout', () => {
  it('shows the import card above a queue of starter sample tasks', () => {
    expect(todayLayout({ ...empty, count: 3, shown: 3 }, 3)).toEqual({
      importCard: true,
      hidden: 0,
      tail: 'everything'
    });
    expect(todayLayout({ ...empty, count: 12, shown: 8 }, 8)).toEqual({
      importCard: true,
      hidden: 4,
      tail: 'more'
    });
  });

  it('shows the import card alone when the queue is empty', () => {
    expect(todayLayout({ ...empty, count: 0, shown: 0 }, 0)).toEqual({
      importCard: true,
      hidden: 0,
      tail: null
    });
  });

  it('offers no import to someone who cannot import, or once records exist', () => {
    for (const flags of [
      { empty_workspace: true, can_import: false },
      { empty_workspace: false, can_import: true },
      {}
    ]) {
      expect(todayLayout({ ...flags, count: 0, shown: 0 }, 0)).toEqual({
        importCard: false,
        hidden: 0,
        tail: 'clear'
      });
      expect(todayLayout({ ...flags, count: 2, shown: 2 }, 2).importCard).toBe(false);
    }
  });
});
