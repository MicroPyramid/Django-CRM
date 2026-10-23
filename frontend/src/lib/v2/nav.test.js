import { describe, it, expect } from 'vitest';
import {
  sidebarGroups,
  tabBar,
  fabAction,
  paletteActions,
  searchPlaceholder,
  noHitsText
} from '#lib/v2/nav.js';

/** @param {string} key @param {boolean} [available] */
const row = (key, available = true) => ({
  key,
  label: key,
  group: /** @type {const} */ ('sell'),
  covers: '',
  stops: '',
  enabled: available,
  available,
  needs: null
});
/** @param {string[]} keys @param {string[]} [off] */
const rows = (keys, off = []) => keys.map((k) => row(k, !off.includes(k)));
const ALL = [
  'deals',
  'leads',
  'goals',
  'tasks',
  'tickets',
  'knowledge_base',
  'documents',
  'invoices',
  'timesheet'
];
/** @param {any[]} groups @param {string} label */
const hrefs = (groups, label) => groups.find((g) => g.label === label)?.items.map((i) => i.href);

describe('sidebarGroups', () => {
  it('drops the items of off modules and keeps core ones', () => {
    const g = sidebarGroups(rows(ALL, ['tickets']), { isAdmin: false });
    expect(hrefs(g, 'Serve')).not.toContain('/tickets');
    expect(hrefs(g, 'Sell')).toEqual(expect.arrayContaining(['/', '/accounts', '/contacts']));
  });

  it('drops a group left empty', () => {
    const g = sidebarGroups(rows(ALL, ['invoices', 'timesheet']), {});
    expect(g.map((x) => x.label)).toEqual(['Sell', 'Serve', 'Run']);
  });

  it('orders each group by the served order, core items at the edges of Sell', () => {
    const g = sidebarGroups(rows(['goals', 'leads', 'deals', 'tickets', 'tasks']), {});
    expect(hrefs(g, 'Sell')).toEqual([
      '/',
      '/goals',
      '/leads',
      '/pipeline',
      '/accounts',
      '/contacts'
    ]);
    expect(hrefs(g, 'Serve').slice(0, 2)).toEqual(['/tickets', '/tasks']);
  });

  it('uses the default order for a null list', () => {
    const g = sidebarGroups(null, {});
    expect(hrefs(g, 'Sell')).toEqual([
      '/',
      '/pipeline',
      '/leads',
      '/goals',
      '/accounts',
      '/contacts'
    ]);
    expect(hrefs(g, 'Bill')).toEqual(['/invoices', '/timesheet']);
  });

  it('labels by terminology and keeps admin items for admins', () => {
    const term = { 'opportunity.plural': 'Cases', 'account.plural': 'Clients' };
    const g = sidebarGroups(null, { isAdmin: true, terminology: term });
    const sell = g.find((x) => x.label === 'Sell');
    expect(sell?.items.map((i) => i.label)).toContain('Cases');
    expect(sell?.items.map((i) => i.label)).toContain('Clients');
    expect(hrefs(g, 'Run')).toContain('/team');
    expect(hrefs(sidebarGroups(null, { isAdmin: false }), 'Run')).toEqual(['/settings']);
  });
});

describe('tabBar and fabAction', () => {
  it('fills the tab bar from the candidates in order', () => {
    expect(tabBar(null).map((i) => i.label)).toEqual(['Today', 'Pipeline', 'Tickets', 'Invoices']);
    expect(tabBar(rows(ALL, ['deals'])).map((i) => i.label)).toEqual([
      'Today',
      'Tickets',
      'Invoices',
      'Leads'
    ]);
  });

  it('picks the first button whose module is on, or none', () => {
    expect(fabAction(null)?.label).toBe('New deal');
    expect(fabAction(rows(ALL, ['deals']))).toEqual({
      href: '/tickets/new',
      label: 'New ticket',
      icon: 'Plus'
    });
    expect(fabAction(rows(ALL, ['deals', 'tickets', 'leads']))?.href).toBe('/tasks/new');
    expect(fabAction(rows(ALL, ['deals', 'tickets', 'leads', 'tasks']))).toBeNull();
  });
});

describe('palette copy', () => {
  it('filters the actions', () => {
    expect(paletteActions(null).map((a) => a.title)).toEqual([
      'New deal',
      'Go to Today',
      'Go to Tasks',
      'Go to Invoices'
    ]);
    expect(paletteActions(rows(ALL, ['deals', 'tasks', 'invoices'])).map((a) => a.title)).toEqual([
      'Go to Today'
    ]);
  });

  it('builds the placeholder and the no-hit sentence from what is on', () => {
    expect(searchPlaceholder(null)).toBe('Search deals, accounts, people, tickets, invoices…');
    expect(noHitsText('x', null)).toBe(
      'Nothing matches “x”. Try an account name, a deal, or an invoice number.'
    );
    const off = rows(ALL, ['deals', 'invoices']);
    expect(searchPlaceholder(off)).toBe('Search accounts, people, tickets…');
    expect(noHitsText('x', off)).toBe('Nothing matches “x”. Try an account name.');
    expect(noHitsText('x', rows(ALL, ['invoices']))).toBe(
      'Nothing matches “x”. Try an account name or a deal.'
    );
  });
});
