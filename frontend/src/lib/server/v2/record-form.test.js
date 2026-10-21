import { describe, it, expect } from 'vitest';
import { readRecordForm } from './record-form.js';

const A = '11111111-1111-4111-8111-111111111111';
const P1 = '33333333-3333-4333-8333-333333333333';

const definition = {
  key: 'property',
  name_label: 'Address',
  fields: [
    { key: 'rooms', label: 'Rooms', field_type: 'number', is_active: true },
    { key: 'furnished', label: 'Furnished', field_type: 'checkbox', is_active: true },
    { key: 'enquiries', label: 'Enquiries', field_type: 'link', target: 'lead', many: true },
    { key: 'owner', label: 'Owner', field_type: 'link', target: 'contact', many: false }
  ]
};

/** @param {[string, string][]} pairs */
function formOf(pairs) {
  const form = new FormData();
  for (const [name, value] of pairs) form.append(name, value);
  return form;
}

describe('readRecordForm', () => {
  it('builds a create body from the form', () => {
    const body = readRecordForm(
      formOf([
        ['name', '  12 Elm Road '],
        ['cf__rendered', 'rooms,furnished'],
        ['cf_rooms', '3'],
        ['link_enquiries__was', ''],
        ['link_enquiries', A],
        ['assigned_to', P1]
      ]),
      definition
    );
    expect(body).toEqual({
      name: '12 Elm Road',
      custom_fields: { rooms: '3', furnished: false },
      links: { enquiries: [A] },
      assigned_to: [P1]
    });
  });

  it('sends nothing for a link or assignee list that did not change', () => {
    const body = readRecordForm(
      formOf([
        ['name', 'X'],
        ['link_enquiries__was', A],
        ['link_enquiries', A],
        ['assigned_to__was', '']
      ]),
      definition
    );
    expect(body.links).toBeUndefined();
    expect(body.assigned_to).toBeUndefined();
  });

  it('never sends a link field the form rendered with no inputs and no __was', () => {
    const body = readRecordForm(
      formOf([
        ['name', 'X'],
        ['link_owner', A]
      ]),
      definition
    );
    expect(body.links).toBeUndefined();
  });

  it('leaves out a checkbox the form did not render, so a newer stored value survives', () => {
    const body = readRecordForm(
      formOf([
        ['name', 'X'],
        ['cf__rendered', 'rooms'],
        ['cf_rooms', '3']
      ]),
      definition
    );
    expect(body.custom_fields).toEqual({ rooms: '3' });
    expect(body.custom_fields).not.toHaveProperty('furnished');
  });

  it('still sends false for a rendered, unchecked checkbox', () => {
    const body = readRecordForm(
      formOf([
        ['name', 'X'],
        ['cf__rendered', 'furnished']
      ]),
      definition
    );
    expect(body.custom_fields).toEqual({ furnished: false });
  });

  it('sends a field emptied on purpose as an empty list', () => {
    const body = readRecordForm(
      formOf([
        ['name', 'X'],
        ['link_enquiries__was', A]
      ]),
      definition
    );
    expect(body.links).toEqual({ enquiries: [] });
  });

  it('sends nothing the form was not built to send', () => {
    const body = readRecordForm(
      formOf([
        ['name', 'X'],
        ['org', 'o'],
        ['created_by', 'c'],
        ['object', 'obj'],
        ['id', 'i'],
        ['cf__rendered', 'rooms,furnished,secret'],
        ['cf_secret', 'z'],
        ['link_owner', A]
      ]),
      definition
    );
    expect(Object.keys(body).sort()).toEqual(['assigned_to', 'custom_fields', 'name']);
    expect(Object.keys(body.custom_fields).sort()).toEqual(['furnished']);
  });
});
