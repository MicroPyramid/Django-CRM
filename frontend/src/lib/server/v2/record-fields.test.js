import { describe, it, expect } from 'vitest';
import {
  pairForEdit,
  pairForDisplay,
  collectFromForm,
  linkFieldsForEdit,
  collectLinks,
  collectAssignees
} from './record-fields.js';
import * as lead from './lead-custom-fields.js';

const A = '11111111-1111-4111-8111-111111111111';
const B = '22222222-2222-4222-8222-222222222222';
const P1 = '33333333-3333-4333-8333-333333333333';
const P2 = '44444444-4444-4444-8444-444444444444';

const statusDefs = [
  {
    key: 'status',
    label: 'Status',
    field_type: 'dropdown',
    options: [{ value: 'available', label: 'Available' }]
  }
];

describe('pairForEdit', () => {
  it('keeps a stale dropdown value selectable', () => {
    const [pair] = pairForEdit(statusDefs, { status: 'let_agreed' });
    expect(pair.value).toBe('let_agreed');
    expect(pair.options.at(-1)).toEqual({
      value: 'let_agreed',
      label: 'let_agreed (no longer an option)'
    });
    expect(pair.options).toHaveLength(2);
  });

  it('adds no extra option for a current or empty value', () => {
    expect(pairForEdit(statusDefs, { status: 'available' })[0].options).toHaveLength(1);
    expect(pairForEdit(statusDefs, {})[0].options).toHaveLength(1);
    expect(pairForEdit(statusDefs, { status: null })[0].options).toHaveLength(1);
  });

  it('does not mutate the definition options', () => {
    pairForEdit(statusDefs, { status: 'gone' });
    expect(statusDefs[0].options).toHaveLength(1);
  });
});

describe('linkFieldsForEdit', () => {
  const fields = [
    { key: 'owner', label: 'Owner', field_type: 'link', target: 'contact', many: false },
    { key: 'note', label: 'Note', field_type: 'text' },
    { key: 'enquiries', label: 'Enquiries', field_type: 'link', target: 'lead', many: true }
  ];

  it('marks a one-record field held by a hidden link read-only', () => {
    const links = {
      owner: { many: false, records: [], hidden: 1 },
      enquiries: { many: true, records: [{ id: A, name: 'Asha' }], hidden: 2 }
    };
    const out = linkFieldsForEdit(fields, links);
    expect(out.map((f) => f.key)).toEqual(['owner', 'enquiries']);
    const [owner, enquiries] = out;
    expect(owner.readOnly).toBe(true);
    expect(enquiries).toMatchObject({
      readOnly: false,
      hidden: 2,
      records: [{ id: A, name: 'Asha' }]
    });
  });

  it('copes with no links answer for a field', () => {
    const [owner] = linkFieldsForEdit(fields, {});
    expect(owner).toMatchObject({ records: [], hidden: 0, readOnly: false, many: false });
  });
});

describe('collectLinks', () => {
  it('sends a link field only when its ids changed', () => {
    const form = new FormData();
    form.append('link_enquiries__was', `${A},${B}`);
    form.append('link_enquiries', B);
    form.append('link_enquiries', A);
    form.append('link_deals__was', A);
    expect(collectLinks(form, [{ key: 'enquiries' }, { key: 'deals' }, { key: 'owner' }])).toEqual({
      deals: []
    });
  });

  it('counts any picked id as a change when none were shown', () => {
    const form = new FormData();
    form.append('link_owner__was', '');
    form.append('link_owner', A);
    expect(collectLinks(form, [{ key: 'owner' }])).toEqual({ owner: [A] });
  });

  it('skips a field with nothing shown and nothing picked', () => {
    const form = new FormData();
    form.append('link_owner__was', '');
    expect(collectLinks(form, [{ key: 'owner' }])).toEqual({});
  });
});

describe('collectAssignees', () => {
  it('leaves assignees out when they did not change', () => {
    const form = new FormData();
    form.append('assigned_to__was', `${P1},${P2}`);
    form.append('assigned_to', P2);
    form.append('assigned_to', P1);
    expect(collectAssignees(form)).toBeUndefined();
  });

  it('sends assignees when one was removed', () => {
    const form = new FormData();
    form.append('assigned_to__was', `${P1},${P2}`);
    form.append('assigned_to', P1);
    expect(collectAssignees(form)).toEqual([P1]);
  });

  it('returns the picked ids when the form has no was field', () => {
    const form = new FormData();
    form.append('assigned_to', P1);
    expect(collectAssignees(form)).toEqual([P1]);
    expect(collectAssignees(new FormData())).toEqual([]);
  });
});

describe('lead-custom-fields re-exports', () => {
  it('still reads lead custom fields through the old module', () => {
    expect(lead.pairForEdit).toBe(pairForEdit);
    expect(lead.pairForDisplay).toBe(pairForDisplay);
    expect(lead.collectFromForm).toBe(collectFromForm);
    expect(typeof lead.displayValue).toBe('function');
    expect(typeof lead.leadFieldDefinitions).toBe('function');
    const form = new FormData();
    form.append('cf_status', ' available ');
    expect(lead.collectFromForm(form, statusDefs)).toEqual({ status: 'available' });
  });
});
