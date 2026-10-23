import { describe, it, expect } from 'vitest';
import { visibleTabs } from '#lib/v2/tabs.js';

/** @param {string} key @param {boolean} available */
const row = (key, available) => ({
  key,
  label: key,
  group: /** @type {const} */ ('bill'),
  covers: '',
  stops: '',
  enabled: available,
  available,
  needs: null
});
/** @param {string[]} off */
const modules = (off) =>
  ['deals', 'tasks', 'tickets', 'invoices'].map((k) => row(k, !off.includes(k)));
/** @param {any[]} tabs */
const labels = (tabs) => tabs.map((t) => t.label);

describe('visibleTabs', () => {
  it('keeps Products while invoices or deals is on, and hides admin tabs from members', () => {
    const only = (/** @type {string[]} */ off) =>
      labels(visibleTabs('invoices', { isAdmin: false, modules: modules(off) }));
    expect(only(['invoices'])).toEqual(['Products']);
    expect(only(['deals'])).toContain('Products');
    expect(only(['invoices', 'deals'])).toEqual([]);
    expect(only([])).not.toContain('Reports');
    expect(labels(visibleTabs('invoices', { isAdmin: true, modules: null }))).toContain('Reports');
  });

  it('drops a set whose module is off and keeps everything for a null list', () => {
    expect(visibleTabs('tickets', { isAdmin: true, modules: modules(['tickets']) })).toEqual([]);
    expect(visibleTabs('tasks', { modules: null })).toHaveLength(3);
  });
});
