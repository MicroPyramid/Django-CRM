import { describe, it, expect } from 'vitest';
import {
  MODULE_KEYS,
  isOn,
  productsOn,
  labelOf,
  requirementFor,
  refusalFor,
  todayClearText,
  notificationsEmptyText,
  wordsOn
} from '#lib/v2/modules.js';

/**
 * @param {string} key
 * @param {Partial<import('#lib/v2/modules.js').ModuleRow>} [over]
 */
const row = (key, over = {}) => ({
  key,
  label: key,
  group: /** @type {const} */ ('sell'),
  covers: '',
  stops: '',
  enabled: true,
  available: true,
  needs: null,
  ...over
});

describe('module logic', () => {
  it('reads a module as on when its row is available, when the list is null, and when it has no row', () => {
    expect(isOn([row('leads')], 'leads')).toBe(true);
    expect(isOn([row('leads', { available: false })], 'leads')).toBe(false);
    expect(isOn(null, 'leads')).toBe(true);
    expect(isOn([row('deals')], 'leads')).toBe(true);
    expect(MODULE_KEYS).toHaveLength(9);
  });

  it('maps each module route and leaves core routes alone', () => {
    /** @type {[string, any][]} */
    const table = [
      ['/(app)/leads', { all: ['leads'] }],
      ['/(app)/settings/lead-pipelines', { all: ['leads'] }],
      ['/(app)/pipeline', { all: ['deals'] }],
      ['/(app)/settings/deal-pipelines', { all: ['deals'] }],
      ['/(app)/goals', { all: ['goals'] }],
      ['/(app)/tasks', { all: ['tasks'] }],
      ['/(app)/tickets/[id]', { all: ['tickets'] }],
      ['/(app)/settings/routing', { all: ['tickets'] }],
      ['/(app)/settings/macros', { all: ['tickets'] }],
      ['/(app)/solutions', { all: ['knowledge_base'] }],
      ['/(app)/settings/help-center', { all: ['knowledge_base'] }],
      ['/(app)/timesheet', { all: ['timesheet'] }],
      ['/(app)/documents', { all: ['documents'] }],
      ['/(app)/accounts/[id]/statement', { all: ['invoices'] }],
      ['/(app)/invoices/products', { any: ['invoices', 'deals'] }],
      ['/(app)/invoices/estimates', { all: ['invoices'] }],
      ['/(app)/profile/calendar-feed', { all: ['tasks'] }],
      ['/(app)/accounts/[id]', null],
      ['/(app)/profile', null],
      ['/(app)/settings/web-forms', null],
      ['/(app)/pipelinex', null]
    ];
    for (const [id, want] of table) expect(requirementFor(id), id).toEqual(want);
    expect(requirementFor('/accounts/[id]/statement')).toEqual({ all: ['invoices'] });
    expect(requirementFor(null)).toBeNull();
  });

  it('names invoices for products only when both are off', () => {
    const off = (/** @type {string} */ k) => row(k, { available: false });
    expect(refusalFor('/invoices/products', [off('invoices'), row('deals')])).toBeNull();
    expect(refusalFor('/invoices/products', [row('invoices'), off('deals')])).toBeNull();
    expect(refusalFor('/invoices/products', [off('invoices'), off('deals')])).toEqual({
      key: 'invoices',
      label: 'invoices'
    });
    expect(productsOn([off('invoices'), off('deals')])).toBe(false);
    expect(productsOn([off('invoices'), row('deals')])).toBe(true);
  });

  it('refuses the first off key of a route and nothing for an on module', () => {
    const rows = [row('tickets', { available: false, label: 'Tickets' })];
    expect(refusalFor('/tickets', rows)).toEqual({ key: 'tickets', label: 'Tickets' });
    expect(refusalFor('/tasks', rows)).toBeNull();
    expect(refusalFor('/tickets', null)).toBeNull();
  });

  it('labels a module by its row, else by default', () => {
    expect(labelOf([row('deals', { label: 'Jobs' })], 'deals')).toBe('Jobs');
    expect(labelOf(null, 'deals')).toBe('Pipeline');
    expect(labelOf([], 'knowledge_base')).toBe('Knowledge base');
  });

  it('says what Today is clear of, from what is on', () => {
    const off = (...keys) => MODULE_KEYS.map((k) => row(k, { available: !keys.includes(k) }));
    expect(todayClearText(null)).toBe('No overdue tickets, invoices, quiet deals or tasks.');
    expect(todayClearText(off('tickets'))).toBe('No overdue invoices, quiet deals or tasks.');
    expect(todayClearText(off('tickets', 'invoices', 'leads'))).toBe(
      'No quiet deals or overdue tasks.'
    );
    expect(todayClearText(off('tickets', 'invoices', 'tasks'))).toBe('No quiet deals.');
    expect(todayClearText(off('tickets', 'invoices', 'deals'))).toBe('No overdue tasks.');
    expect(todayClearText(off('tickets', 'invoices', 'deals', 'tasks'))).toBe(
      'Nothing is waiting on you.'
    );
  });

  it('drops tickets from the notifications line when Tickets is off', () => {
    expect(notificationsEmptyText(null)).toContain('CRM ticket activity');
    expect(notificationsEmptyText([row('tickets', { available: false })])).toBe(
      'Notifications arrive for automation rules and updates from BottleCRM Support.'
    );
  });

  it('joins the words whose module is on as prose', () => {
    /** @type {[string | null, string][]} */
    const words = [
      [null, 'accounts'],
      ['leads', 'leads'],
      ['deals', 'deals'],
      ['tickets', 'tickets']
    ];
    const off = (...keys) => MODULE_KEYS.map((k) => row(k, { available: !keys.includes(k) }));
    expect(wordsOn(null, words)).toBe('accounts, leads, deals and tickets');
    expect(wordsOn(off('tickets'), words)).toBe('accounts, leads and deals');
    expect(wordsOn(off('leads', 'deals'), words, 'or')).toBe('accounts or tickets');
    expect(wordsOn(off('leads', 'deals', 'tickets'), words)).toBe('accounts');
    expect(wordsOn(off('leads'), [['leads', 'a lead']])).toBe('');
  });
});
