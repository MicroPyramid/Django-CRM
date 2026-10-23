import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  actorName,
  pausedByModule,
  OBJECT_LABELS,
  notificationText,
  hubValue,
  showAutomationSetting,
  objectOf,
  fieldOf,
  triggerFields,
  operatorsFor,
  operatorLabel,
  valueKind,
  blankCondition,
  blankAction,
  actionTypes,
  targetsFor,
  recipientsFor,
  withStored,
  triggerSentence,
  runsLabel,
  STATUS,
  recordRoute,
  editorState,
  isDirty,
  tryBlocked,
  moveItem,
  keptValue,
  switchObject,
  changeHint,
  placeErrors,
  editorErrors,
  offersParent,
  taskAudience,
  applyTarget,
  applyField,
  applyAssignTo,
  actionLabel,
  actionOptions,
  recipientLabel,
  parentAssignees,
  applyClear,
  isClearing,
  setActionValue,
  shownValue,
  applyMode,
  ruleStatus,
  switchLabel,
  statusNote,
  runNotes,
  sentRows,
  replacePerson
} from '#lib/v2/automation.js';

const f = (key, label, type, extra = {}) => ({
  key,
  label,
  type,
  choices: [],
  settable: true,
  ...extra
});
const choice = (value, label, group = '', settable = true) => ({ value, label, group, settable });

const deal = {
  key: 'deal',
  label: 'Deal',
  label_plural: 'Deals',
  parent: { key: 'account', label: 'Account' },
  links: [
    { id: 'in:property.deal', label: 'Properties linked through Deals', object_key: 'obj:property' }
  ],
  fields: [
    f('name', 'Name', 'text'),
    f('amount', 'Amount', 'number'),
    f('close_date', 'Close date', 'date'),
    f('stage', 'Stage', 'choice', {
      choices: [choice('s1', 'Proposal', 'Sales'), choice('s2', 'Won', 'Sales')]
    }),
    f('stage_kind', 'Outcome', 'choice', {
      settable: false,
      choices: [
        choice('open', 'Open (any pipeline)'),
        choice('won', 'Won (any pipeline)', '', false),
        choice('lost', 'Lost (any pipeline)')
      ]
    }),
    f('assigned_to', 'Assigned to', 'people'),
    f('custom_fields.vip', 'VIP', 'boolean')
  ]
};
const lead = {
  key: 'lead',
  label: 'Lead',
  label_plural: 'Leads',
  parent: null,
  links: [],
  fields: [
    f('title', 'Title', 'text'),
    f('stage', 'Stage', 'choice', {
      settable: false,
      choices: [choice('l1', 'New', 'Leads', false)]
    }),
    f('assigned_to', 'Assigned to', 'people', { settable: false })
  ]
};
const custom = {
  key: 'obj:property',
  label: 'Property',
  label_plural: 'Properties',
  parent: null,
  links: [],
  fields: [f('name', 'Name', 'text')]
};
const catalogue = {
  objects: [deal, lead, custom],
  operators: {
    text: ['eq', 'neq', 'contains', 'not_contains', 'empty', 'not_empty'],
    number: ['eq', 'neq', 'gt', 'lt', 'empty', 'not_empty'],
    date: ['eq', 'neq', 'gt', 'lt', 'empty', 'not_empty'],
    choice: ['eq', 'neq', 'in', 'not_in', 'empty', 'not_empty'],
    boolean: ['true', 'false'],
    person: ['eq', 'includes', 'excludes', 'empty', 'not_empty'],
    people: ['eq', 'includes', 'excludes', 'empty', 'not_empty']
  },
  update_only_operators: ['was', 'was_not'],
  actions: ['set_field', 'assign', 'create_task', 'notify', 'webhook'],
  people: [{ id: 'p1', name: 'Asha' }],
  endpoints: [{ id: 'e1', description: 'hooks.example.com' }],
  limits: { conditions: 20, actions: 10 }
};
const ID = '123e4567-e89b-12d3-a456-426614174000';

describe('lookups', () => {
  it('finds an object and a field, or null', () => {
    expect(objectOf(catalogue, 'deal')).toBe(deal);
    expect(objectOf(catalogue, 'nope')).toBeNull();
    expect(objectOf(null, 'deal')).toBeNull();
    expect(fieldOf(deal, 'amount').label).toBe('Amount');
    expect(fieldOf(deal, 'x')).toBeNull();
    expect(fieldOf(null, 'x')).toBeNull();
  });

  it('lists every field but people as a trigger field', () => {
    expect(triggerFields(deal).map((x) => x.key)).not.toContain('assigned_to');
    expect(triggerFields(deal)).toHaveLength(deal.fields.length - 1);
  });
});

describe('operators', () => {
  it('offers was and was_not only on an updated trigger, never on people', () => {
    const amount = fieldOf(deal, 'amount');
    const people = fieldOf(deal, 'assigned_to');
    expect(operatorsFor(catalogue, amount, 'updated')).toEqual([
      ...catalogue.operators.number,
      'was',
      'was_not'
    ]);
    expect(operatorsFor(catalogue, amount, 'created')).toEqual(catalogue.operators.number);
    expect(operatorsFor(catalogue, people, 'updated')).toEqual(catalogue.operators.people);
    expect(operatorsFor(catalogue, null, 'updated')).toEqual([]);
  });

  it('picks the value input for each type and operator', () => {
    const t = (/** @type {string} */ type) => ({ type });
    const table = [
      [t('text'), 'eq', 'text'],
      [t('number'), 'gt', 'number'],
      [t('date'), 'lt', 'date'],
      [t('choice'), 'eq', 'choice'],
      [t('choice'), 'in', 'choices'],
      [t('choice'), 'not_in', 'choices'],
      [t('people'), 'eq', 'people'],
      [t('people'), 'includes', 'person'],
      [t('people'), 'excludes', 'person'],
      [t('person'), 'eq', 'person'],
      [t('boolean'), 'was', 'boolean'],
      [t('boolean'), 'was_not', 'boolean'],
      [t('text'), 'was', 'text'],
      [t('number'), 'empty', 'none'],
      [t('people'), 'not_empty', 'none'],
      [t('boolean'), 'true', 'none'],
      [t('boolean'), 'false', 'none']
    ];
    for (const [field, op, kind] of table)
      expect(valueKind(/** @type {any} */ (field), /** @type {string} */ (op))).toBe(kind);
  });

  it('labels operators, with dates and people reading their own way', () => {
    const labels = {
      eq: 'is',
      neq: 'is not',
      contains: 'contains',
      not_contains: 'does not contain',
      gt: 'is more than',
      lt: 'is less than',
      in: 'is any of',
      not_in: 'is none of',
      true: 'is true',
      false: 'is false',
      includes: 'includes',
      excludes: 'does not include',
      empty: 'is empty',
      not_empty: 'is not empty',
      was: 'was',
      was_not: 'was not'
    };
    for (const [op, label] of Object.entries(labels)) expect(operatorLabel(op, 'text')).toBe(label);
    expect(operatorLabel('gt', 'date')).toBe('is after');
    expect(operatorLabel('lt', 'date')).toBe('is before');
    expect(operatorLabel('eq', 'people')).toBe('is exactly');
    expect(operatorLabel('zzz', 'text')).toBe('zzz');
  });
});

describe('blanks', () => {
  it('makes a blank condition and each blank action', () => {
    expect(blankCondition()).toEqual({ field: '', op: '', value: null });
    expect(blankAction('create_task')).toEqual({
      type: 'create_task',
      title: '',
      due_in_days: 2,
      priority: 'Medium',
      assign_to: 'record',
      person: null
    });
    expect(blankAction('notify')).toEqual({ type: 'notify', to: [], people: [], message: '' });
    expect(blankAction('set_field')).toEqual({
      type: 'set_field',
      target: 'record',
      field: '',
      value: null
    });
    expect(blankAction('assign')).toEqual({ type: 'assign', mode: 'replace', people: [] });
    expect(blankAction('webhook')).toEqual({ type: 'webhook', endpoint: '' });
  });

  it('gives each call its own arrays', () => {
    expect(blankAction('notify').to).not.toBe(blankAction('notify').to);
  });
});

describe('actionTypes', () => {
  it('leaves out assign without settable assignees, and webhook on a custom object or with no endpoints', () => {
    expect(actionTypes(catalogue, deal)).toEqual(catalogue.actions);
    expect(actionTypes(catalogue, lead)).toEqual(['set_field', 'create_task', 'notify', 'webhook']);
    expect(actionTypes(catalogue, custom)).toEqual(['set_field', 'create_task', 'notify']);
    expect(actionTypes({ ...catalogue, endpoints: [] }, deal)).not.toContain('webhook');
  });
});

describe('targets and recipients', () => {
  it('offers the parent and each link as a target', () => {
    const t = targetsFor(catalogue, deal);
    expect(t.map((x) => [x.value, x.label])).toEqual([
      ['record', 'This deal'],
      ['parent', 'Its account'],
      ['in:property.deal', 'Properties linked through Deals']
    ]);
    expect(t[0].object).toBe(deal);
    expect(t[1].object.key).toBe('account');
    expect(t[2].object).toBe(custom);
    expect(targetsFor(catalogue, lead).map((x) => x.value)).toEqual(['record']);
    expect(targetsFor(catalogue, { ...deal, links: [] }).map((x) => x.value)).toEqual([
      'record',
      'parent'
    ]);
  });

  it('lists who a notification can reach', () => {
    expect(recipientsFor(deal).map((x) => x.label)).toEqual([
      'Its assignees',
      'Who created it',
      "The account's assignees",
      'All admins',
      'Assignees of Properties linked through Deals'
    ]);
    expect(recipientsFor(deal)[2].value).toBe('parent_assignees');
    expect(recipientsFor(deal)[4].value).toBe('linked:in:property.deal');
    expect(
      recipientsFor({ key: 'task', label: 'Task', parent: null, links: [] }).map((x) => x.label)
    ).toEqual(['Its assignees', 'Who created it', "Its parent's assignees", 'All admins']);
    expect(recipientsFor(lead).map((x) => x.value)).toEqual([
      'record_assignees',
      'record_creator',
      'admins'
    ]);
  });
});

describe('withStored', () => {
  const options = [choice('a', 'Alpha', 'G'), choice('b', 'Beta')];

  it('keeps a stored value the options lost, marked as gone', () => {
    const out = withStored(options, ['a', 'zz']);
    expect(out).toHaveLength(3);
    expect(out[2]).toMatchObject({ value: 'zz', label: 'zz (no longer available)', gone: true });
    expect(out[0].gone).toBeUndefined();
  });

  it('takes one value or none, and does not duplicate', () => {
    expect(withStored(options, 'a')).toHaveLength(2);
    expect(withStored(options, null)).toHaveLength(2);
    expect(withStored(options, '')).toHaveLength(2);
    expect(withStored(options, ['x', 'x'])).toHaveLength(3);
  });

  it('labels a missing person without the id', () => {
    const out = withStored([{ value: 'p1', label: 'Asha' }], ['p1', 'p9'], { person: true });
    expect(out[1]).toMatchObject({ value: 'p9', label: 'Someone no longer active', gone: true });
  });
});

describe('triggerSentence', () => {
  const rule = (trigger) => ({ object_key: 'deal', trigger });

  it('says the trigger in words', () => {
    expect(triggerSentence(rule({ event: 'created' }), catalogue)).toBe('Created');
    expect(triggerSentence(rule({ event: 'updated' }), catalogue)).toBe('Updated');
    expect(triggerSentence(rule({ event: 'updated', field: 'stage' }), catalogue)).toBe(
      'Stage changes'
    );
    expect(triggerSentence(rule({ event: 'updated', field: 'stage', to: 's2' }), catalogue)).toBe(
      'Stage changes to Won'
    );
    expect(
      triggerSentence(rule({ event: 'updated', field: 'stage_kind', to: 'won' }), catalogue)
    ).toBe('Outcome changes to Won (any pipeline)');
    expect(
      triggerSentence(rule({ event: 'updated', field: 'custom_fields.vip', to: true }), catalogue)
    ).toBe('VIP changes to Yes');
    expect(
      triggerSentence(rule({ event: 'updated', field: 'custom_fields.vip', to: false }), catalogue)
    ).toBe('VIP changes to No');
    expect(triggerSentence(rule({ event: 'updated', field: 'amount', to: 500 }), catalogue)).toBe(
      'Amount changes to 500'
    );
    expect(triggerSentence(rule({ event: 'updated', field: 'gone' }), catalogue)).toBe(
      'A field that is no longer available changes'
    );
    expect(
      triggerSentence({ object_key: 'zzz', trigger: { event: 'updated', field: 'x' } }, catalogue)
    ).toBe('A field that is no longer available changes');
  });
});

describe('runs and status', () => {
  it('counts runs in words', () => {
    expect(runsLabel({ runs_7d: 0, failures_7d: 0 })).toBe('No runs');
    expect(runsLabel({ runs_7d: 1, failures_7d: 0 })).toBe('1 run');
    expect(runsLabel({ runs_7d: 14, failures_7d: 0 })).toBe('14 runs');
    expect(runsLabel({ runs_7d: 52, failures_7d: 1 })).toBe('52 runs, 1 failed');
    expect(runsLabel({})).toBe('No runs');
  });

  it('names the five statuses', () => {
    expect(STATUS).toEqual({
      on: { label: 'On', tone: 'moss' },
      off: { label: 'Off', tone: 'slate' },
      paused: { label: 'Paused', tone: 'clay' },
      over_limit: { label: 'Not running', tone: 'clay' },
      needs_attention: { label: 'Needs attention', tone: 'rust' }
    });
  });

  it('notes a status under its pill, leaving a paused rule to its own note', () => {
    const why = 'Asha left the organization.';
    expect(statusNote({ status: 'paused', status_text: why })).toBeNull();
    expect(statusNote({ status: 'needs_attention', status_text: why })).toBe(why);
    expect(statusNote({ status: 'over_limit', status_text: 'Not running yet.' })).toBe(
      'Not running yet.'
    );
    expect(statusNote({ status: 'on', status_text: 'On' })).toBeNull();
    expect(statusNote({ status: 'off', status_text: '' })).toBeNull();
    expect(statusNote(null)).toBeNull();
  });
});

describe('replacePerson', () => {
  it('shows the one person, or asks who stays when the stored rule holds several', () => {
    expect(replacePerson({ people: ['p1'] })).toEqual({
      id: 'p1',
      several: false
    });
    expect(replacePerson({ people: ['p1', 'p2'] })).toEqual({
      id: '',
      several: true
    });
    expect(replacePerson({ people: [] })).toEqual({ id: '', several: false });
    expect(replacePerson({})).toEqual({ id: '', several: false });
  });
});

describe('runNotes', () => {
  it('gives the reason and the rule that set the run off', () => {
    expect(
      runNotes({ reason: 'The endpoint answered 500.', triggered_by: { rule_name: 'Close it' } })
    ).toEqual({ reason: 'The endpoint answered 500.', by: 'Set off by "Close it"' });
    expect(runNotes({ reason: '', triggered_by: null })).toEqual({ reason: null, by: null });
    expect(runNotes({ reason: 5, triggered_by: { rule_name: ['x'] } })).toEqual({
      reason: null,
      by: null
    });
    expect(runNotes(null)).toEqual({ reason: null, by: null });
  });
});

describe('recordRoute', () => {
  it('routes each object to its page and refuses the rest', () => {
    expect(recordRoute('lead', ID)).toBe(`/leads/${ID}`);
    expect(recordRoute('contact', ID)).toBe(`/contacts/${ID}`);
    expect(recordRoute('account', ID)).toBe(`/accounts/${ID}`);
    expect(recordRoute('deal', ID)).toBe(`/pipeline/${ID}`);
    expect(recordRoute('ticket', ID)).toBe(`/tickets/${ID}`);
    expect(recordRoute('task', ID)).toBe(`/tasks/${ID}`);
    expect(recordRoute('obj:property', ID)).toBe(`/objects/property/${ID}`);
    expect(recordRoute('invoice', ID)).toBeNull();
    expect(recordRoute('deal', 'x')).toBeNull();
    expect(recordRoute('deal', null)).toBeNull();
    expect(recordRoute('obj:../x', ID)).toBeNull();
  });
});

describe('the draft', () => {
  const saved = {
    id: ID,
    name: 'Chase',
    object_key: 'deal',
    match: 'any',
    is_active: true,
    owner: { id: 'o', name: 'O' },
    trigger: { event: 'updated', field: 'stage', to: 's2' },
    conditions: [{ field: 'amount', op: 'gt', value: 5 }],
    actions: [{ type: 'notify', to: ['admins'], people: [], message: 'Hi' }]
  };

  it('starts a new rule on the chosen object', () => {
    const d = editorState(null, 'deal');
    expect(d).toMatchObject({
      name: '',
      object_key: 'deal',
      match: 'all',
      trigger: { event: 'created' },
      conditions: [],
      actions: []
    });
  });

  it('copies only the rule keys, deeply', () => {
    const d = editorState(saved, 'deal');
    expect(Object.keys(d).sort()).toEqual(
      ['actions', 'conditions', 'match', 'name', 'object_key', 'trigger'].sort()
    );
    d.actions[0].to.push('x');
    expect(saved.actions[0].to).toEqual(['admins']);
  });

  it('is dirty only when the rule would change', () => {
    const d = editorState(saved, 'deal');
    expect(isDirty(d, editorState(saved, 'deal'))).toBe(false);
    const reordered = {
      actions: d.actions,
      trigger: { to: 's2', field: 'stage', event: 'updated' },
      object_key: 'deal',
      conditions: d.conditions,
      name: d.name,
      match: d.match
    };
    expect(isDirty(reordered, d)).toBe(false);
    expect(isDirty({ ...d, name: 'Other' }, d)).toBe(true);
    expect(isDirty({ ...d, conditions: [] }, d)).toBe(true);
    const changed = editorState(saved, 'deal');
    changed.actions[0].message = 'Bye';
    expect(isDirty(changed, d)).toBe(true);
  });
});

describe('the draft under a reactive proxy', () => {
  const wrapped = () => ({
    name: 'R',
    object_key: 'deal',
    match: 'all',
    trigger: new Proxy({ event: 'updated', field: 'stage', to: 's1' }, {}),
    conditions: new Proxy([{ field: 'stage', op: 'in', value: new Proxy(['s1', 's2'], {}) }], {}),
    actions: new Proxy(
      [{ type: 'notify', to: new Proxy(['admins'], {}), people: new Proxy([], {}), message: 'x' }],
      {}
    )
  });

  it('copies and compares without structuredClone', () => {
    const draft = wrapped();
    const copy = editorState(draft, 'deal');
    expect(copy.conditions[0].value).toEqual(['s1', 's2']);
    expect(isDirty(draft, copy)).toBe(false);
    expect(isDirty(wrapped(), editorState(null, 'deal'))).toBe(true);
  });
});

describe('an absent action value', () => {
  it('reads the same as null for a condition, but not for set_field', () => {
    const a = editorState(
      {
        conditions: [{ field: 'f', op: 'empty' }],
        actions: [{ type: 'set_field', target: 'record', field: 'f' }]
      },
      'deal'
    );
    const b = editorState(
      {
        conditions: [{ field: 'f', op: 'empty', value: null }],
        actions: [{ type: 'set_field', target: 'record', field: 'f', value: null }]
      },
      'deal'
    );
    expect(a.conditions[0].value).toBeNull();
    expect('value' in a.actions[0]).toBe(false);
    expect(isDirty(a, b)).toBe(true);
    expect(isDirty(b, b)).toBe(false);
  });
});

describe('moveItem', () => {
  it('moves an item and keeps the ends', () => {
    const list = ['a', 'b', 'c'];
    expect(moveItem(list, 1, -1)).toEqual(['b', 'a', 'c']);
    expect(moveItem(list, 1, 1)).toEqual(['a', 'c', 'b']);
    expect(moveItem(list, 0, -1)).toEqual(['a', 'b', 'c']);
    expect(moveItem(list, 2, 1)).toEqual(['a', 'b', 'c']);
    expect(moveItem(list, 0, 1)).not.toBe(list);
    expect(list).toEqual(['a', 'b', 'c']);
  });
});

describe('showAutomationSetting', () => {
  it('shows admins the row unless the API has no automation', () => {
    const summary = { active: 1, failing: 0, attention: false };
    expect(showAutomationSetting(summary, true)).toBe(true);
    expect(showAutomationSetting(null, true)).toBe(true);
    expect(showAutomationSetting(false, true)).toBe(false);
  });

  it('never shows a member the row', () => {
    expect(showAutomationSetting({ active: 1, failing: 0, attention: false }, false)).toBe(false);
    expect(showAutomationSetting(null, false)).toBe(false);
  });
});

describe('hubValue', () => {
  it('answers no value and no warning without a summary', () => {
    expect(hubValue(null)).toEqual({ value: null, warn: false });
  });

  it('words the active count, the failing count and the warning', () => {
    const at = (active, failing, attention = false) => hubValue({ active, failing, attention });
    expect(at(0, 0).value).toBe('No active rules');
    expect(at(1, 0).value).toBe('1 active rule');
    expect(at(2, 0).value).toBe('2 active rules');
    expect(at(2, 1).value).toBe('2 active rules, 1 failing');
    expect(at(1, 2).value).toBe('1 active rule, 2 failing');
    expect(at(1, 0, true).warn).toBe(true);
    expect(at(1, 0, false).warn).toBe(false);
  });
});

describe('keptValue', () => {
  const field = (key) => fieldOf(deal, key);

  it('keeps the value while the new operator reads the same kind', () => {
    expect(keptValue(field('amount'), 'gt', 'lt', 5)).toBe(5);
    expect(keptValue(field('stage'), 'in', 'not_in', ['s1'])).toEqual(['s1']);
    expect(keptValue(field('stage'), 'eq', 'was', 's1')).toBe('s1');
    expect(keptValue(field('custom_fields.vip'), 'was', 'was_not', true)).toBe(true);
  });

  it('drops it when the operator takes none or reads another kind', () => {
    expect(keptValue(field('amount'), 'gt', 'empty', 5)).toBeNull();
    expect(keptValue(field('custom_fields.vip'), 'was', 'true', true)).toBeNull();
    expect(keptValue(field('stage'), 'eq', 'in', 's1')).toBeNull();
    expect(keptValue(field('stage'), 'in', 'eq', ['s1'])).toBeNull();
    expect(keptValue(field('assigned_to'), 'eq', 'includes', ['p1'])).toBeNull();
    expect(keptValue(null, 'eq', 'neq', 'x')).toBeNull();
    expect(keptValue(field('amount'), 'gt', 'lt', undefined)).toBeNull();
  });
});

describe('switchObject', () => {
  const draft = {
    name: 'Won',
    object_key: 'deal',
    match: 'any',
    trigger: { event: 'updated', field: 'stage_kind', to: 'won' },
    conditions: [{ field: 'amount', op: 'gt', value: 0 }],
    actions: [
      { type: 'set_field', target: 'parent', field: 'name', value: 'x' },
      {
        type: 'notify',
        to: ['record_assignees', 'parent_assignees', 'linked:in:property.deal', 'admins'],
        people: ['p1'],
        message: 'Hi {name}'
      },
      { type: 'create_task', title: 'Call', due_in_days: 2, priority: 'High', assign_to: 'record' }
    ]
  };

  it("drops what named the old object's fields and links", () => {
    expect(switchObject(draft, catalogue, 'lead')).toEqual({
      name: 'Won',
      object_key: 'lead',
      match: 'any',
      trigger: { event: 'updated' },
      conditions: [],
      actions: [
        blankAction('set_field'),
        {
          type: 'notify',
          to: ['record_assignees', 'admins'],
          people: ['p1'],
          message: 'Hi {name}'
        },
        draft.actions[2]
      ]
    });
  });

  it('drops a webhook the new object cannot take', () => {
    const hook = { type: 'webhook', endpoint: ID };
    const d = { ...draft, actions: [hook] };
    expect(switchObject(d, catalogue, 'lead').actions).toEqual([hook]);
    expect(switchObject(d, catalogue, 'obj:property').actions).toEqual([]);
    expect(switchObject(d, { ...catalogue, endpoints: [] }, 'lead').actions).toEqual([]);
  });

  it('drops an assign where the new object has no settable assignees', () => {
    const assign = { type: 'assign', mode: 'replace', people: ['p1'] };
    const d = { ...draft, actions: [assign] };
    expect(switchObject(d, catalogue, 'deal').actions).toEqual([assign]);
    expect(switchObject(d, catalogue, 'obj:property').actions).toEqual([]);
  });

  it('resets a task for the parent where the new object has none', () => {
    const task = (assign_to, person = null) => ({
      type: 'create_task',
      title: 'x',
      due_in_days: null,
      priority: 'Low',
      assign_to,
      person
    });
    const d = { ...draft, actions: [task('parent'), task('owner'), task('person', 'p1')] };
    expect(switchObject(d, catalogue, 'lead').actions).toEqual([
      task('record'),
      task('owner'),
      task('person', 'p1')
    ]);
    expect(switchObject(d, catalogue, 'deal').actions[0].assign_to).toBe('parent');
  });

  it('leaves the draft it was given alone', () => {
    const before = JSON.stringify(draft);
    const next = switchObject(new Proxy(draft, {}), catalogue, 'lead');
    next.actions[2].title = 'Changed';
    expect(JSON.stringify(draft)).toBe(before);
  });
});

describe('changeHint', () => {
  it('names the field and the value it moves into', () => {
    expect(changeHint(fieldOf(deal, 'stage_kind'), 'won')).toBe(
      'Runs once, when the outcome moves into Won (any pipeline); later edits do not run it again.'
    );
    expect(changeHint(fieldOf(deal, 'custom_fields.vip'), false)).toBe(
      'Runs once, when the vip moves into No; later edits do not run it again.'
    );
    expect(changeHint(fieldOf(deal, 'amount'), 100)).toContain('the amount moves into 100;');
    expect(changeHint(fieldOf(deal, 'stage'), 'gone')).toContain('moves into gone;');
  });

  it('says nothing without a field or a value', () => {
    expect(changeHint(null, 'won')).toBeNull();
    for (const to of [undefined, null, ''])
      expect(changeHint(fieldOf(deal, 'amount'), to)).toBeNull();
  });
});

describe('placeErrors', () => {
  const shown = (/** @type {string} */ key) => ['name', 'trigger', 'conditions.0'].includes(key);

  it('keeps the rows the page shows and words the rest as one general line', () => {
    expect(
      placeErrors(
        {
          general: null,
          rows: {
            name: 'Name it.',
            'conditions.0': 'Enter a number.',
            'conditions.3': 'Enter a value.',
            'actions.1': 'Choose a person.',
            object_key: 'Rules cannot be built on this object.'
          }
        },
        shown
      )
    ).toEqual({
      general:
        'Condition 4: Enter a value. Action 2: Choose a person. Rules cannot be built on this object.',
      rows: { name: 'Name it.', 'conditions.0': 'Enter a number.' }
    });
  });

  it('passes a general error through, and answers nothing for no errors', () => {
    expect(placeErrors({ general: 'Over the limit.', rows: {} }, shown)).toEqual({
      general: 'Over the limit.',
      rows: {}
    });
    expect(placeErrors(null, shown)).toEqual({ general: null, rows: {} });
    expect(placeErrors(undefined, shown)).toEqual({ general: null, rows: {} });
  });
});

describe('editorErrors', () => {
  const a = { field: 'amount', op: 'gt', value: 'x' };
  const b = { field: 'closed_on', op: 'eq', value: null };
  const c = { field: 'name', op: 'eq', value: '' };
  const save = {
    general: null,
    rows: {
      name: 'Name it.',
      trigger: 'Enter a value.',
      'conditions.0': 'Enter a number.',
      'conditions.1': 'Enter a date as YYYY-MM-DD.',
      'conditions.5': 'Late.',
      'actions.0': 'Choose a person.',
      object_key: 'Rules cannot be built on this object.'
    }
  };

  it('puts each condition message on the row it was sent as', () => {
    const sent = sentRows({ conditions: [a, b] });
    expect(editorErrors(save, sent, { conditions: [a, b] }).conditions).toEqual([
      'Enter a number.',
      'Enter a date as YYYY-MM-DD.'
    ]);
    expect(editorErrors(save, sent, { conditions: [b, c] }).conditions).toEqual([
      'Enter a date as YYYY-MM-DD.',
      null
    ]);
  });

  it('keeps the section messages and words the rest as the general line', () => {
    const out = editorErrors(save, sentRows({ conditions: [a, b] }), { conditions: [b] });
    expect(out.rows).toMatchObject({ name: 'Name it.', trigger: 'Enter a value.' });
    expect(out.general).toBe(
      'Condition 6: Late. Action 1: Choose a person. Rules cannot be built on this object.'
    );
  });

  it('answers nothing before a save', () => {
    expect(editorErrors(undefined, sentRows({ conditions: [] }), { conditions: [a] })).toEqual({
      general: null,
      rows: {},
      conditions: [null],
      actions: []
    });
  });

  it('puts each action message on the row object it was sent as', () => {
    const x = { type: 'webhook', endpoint: '' };
    const y = { type: 'notify', to: [], people: [], message: '' };
    const z = { type: 'assign', mode: 'replace', people: [] };
    const sent = sentRows({ conditions: [], actions: [x, y] });
    const msgs = {
      general: null,
      rows: {
        'actions.0': 'Choose an endpoint.',
        'actions.1': 'Choose who to notify.',
        actions: 'Add at least one action.'
      }
    };
    const out = editorErrors(msgs, sent, { conditions: [], actions: [y, z, x] });
    expect(out.actions).toEqual(['Choose who to notify.', null, 'Choose an endpoint.']);
    expect(out.rows.actions).toBeUndefined();
    expect(out.general).toBeNull();
  });

  it('keeps the list error while the actions are the ones sent, drops it after a change', () => {
    const x = { type: 'webhook', endpoint: '' };
    const save = { general: null, rows: { actions: 'Add at least one action.' } };
    expect(
      editorErrors(save, sentRows({ conditions: [], actions: [] }), { conditions: [], actions: [] })
        .rows
    ).toEqual({
      actions: 'Add at least one action.'
    });
    const same = editorErrors(save, sentRows({ conditions: [], actions: [x] }), {
      conditions: [],
      actions: [x]
    });
    expect(same.rows.actions).toBe('Add at least one action.');
    const added = editorErrors(save, sentRows({ conditions: [], actions: [] }), {
      conditions: [],
      actions: [x]
    });
    expect(added.rows.actions).toBeUndefined();
  });

  it('words an action error for a row never sent as general', () => {
    const out = editorErrors(
      { general: null, rows: { 'actions.3': 'Late.' } },
      sentRows({ conditions: [], actions: [] }),
      { conditions: [], actions: [] }
    );
    expect(out.general).toBe('Action 4: Late.');
  });

  it('drops a row message once that row has changed since the save', () => {
    const x = { field: 'amount', op: 'gt', value: 'x' };
    const y = { field: 'closed_on', op: 'eq', value: 'soon' };
    const z = { type: 'webhook', endpoint: '' };
    const sent = sentRows({ conditions: [x, y], actions: [z] });
    const msgs = {
      general: null,
      rows: {
        'conditions.0': 'Enter a number.',
        'conditions.1': 'Enter a date as YYYY-MM-DD.',
        'actions.0': 'Choose an endpoint.'
      }
    };
    x.value = '5';
    z.endpoint = 'e1';
    const out = editorErrors(msgs, sent, { conditions: [x, y], actions: [z] });
    expect(out.conditions).toEqual([null, 'Enter a date as YYYY-MM-DD.']);
    expect(out.actions).toEqual([null]);
    expect(out.general).toBeNull();
  });
});

describe('offersParent and taskAudience', () => {
  it('offers a parent on deal, ticket (with a parent) and task only', () => {
    expect(offersParent(deal)).toBe(true);
    expect(offersParent({ key: 'ticket', parent: { key: 'account', label: 'Account' } })).toBe(
      true
    );
    expect(offersParent({ key: 'ticket', parent: null })).toBe(false);
    expect(offersParent({ key: 'task', parent: null })).toBe(true);
    expect(offersParent(lead)).toBe(false);
    expect(offersParent(custom)).toBe(false);
    expect(offersParent(null)).toBe(false);
  });

  it('lists who a task is for, lower-case mid-sentence', () => {
    expect(taskAudience(deal)).toEqual([
      { value: 'record', label: 'Its assignees' },
      { value: 'parent', label: "The account's assignees" },
      { value: 'owner', label: "The rule's owner" },
      { value: 'person', label: 'A chosen person' }
    ]);
    expect(taskAudience({ key: 'task', parent: null }).map((o) => o.label)).toEqual([
      'Its assignees',
      "Its parent's assignees",
      "The rule's owner",
      'A chosen person'
    ]);
    expect(taskAudience(lead).map((o) => o.value)).toEqual(['record', 'owner', 'person']);
  });
});

describe('what a change in a row clears', () => {
  it('changing a set_field target clears its field and value, in place', () => {
    const a = { type: 'set_field', target: 'record', field: 'stage', value: 's2' };
    applyTarget(a, 'parent');
    expect(a).toEqual({ type: 'set_field', target: 'parent', field: '', value: undefined });
    expect(JSON.parse(JSON.stringify(a))).toEqual({
      type: 'set_field',
      target: 'parent',
      field: ''
    });
  });

  it('choosing a field leaves the value unset, not cleared', () => {
    const a = { type: 'set_field', target: 'record', field: '', value: null };
    applyField(a, 'amount');
    expect(a.field).toBe('amount');
    expect('value' in JSON.parse(JSON.stringify(a))).toBe(false);
  });

  it('create_task.person is null unless the task is for a chosen person', () => {
    const t = { type: 'create_task', assign_to: 'person', person: 'p1' };
    applyAssignTo(t, 'owner');
    expect(t).toEqual({ type: 'create_task', assign_to: 'owner', person: null });
    applyAssignTo(t, 'person');
    expect(t.person).toBeNull();
    t.person = 'p1';
    applyAssignTo(t, 'person');
    expect(t.person).toBe('p1');
  });

  it('names each action type, and a type the catalogue lost by its key', () => {
    expect(actionLabel('create_task')).toBe('Create a task');
    expect(actionLabel('set_field')).toBe('Set a field');
    expect(actionLabel('mystery')).toBe('mystery');
  });
});

describe('ruleStatus and switchLabel', () => {
  it("reads the list row's status, else what the rule says, and null for a new rule", () => {
    expect(ruleStatus(null, null)).toBeNull();
    expect(ruleStatus({ is_active: false }, { status: 'over_limit' })).toBe('over_limit');
    expect(ruleStatus({ is_active: true }, null)).toBe('on');
    expect(ruleStatus({ is_active: false, paused_reason: 'left' }, null)).toBe('paused');
    expect(ruleStatus({ is_active: false, paused_reason: '' }, null)).toBe('off');
  });

  it('offers to switch on, to take over, or nothing when the rule is already on', () => {
    expect(switchLabel(null)).toBe('Save and switch on');
    expect(switchLabel('off')).toBe('Save and switch on');
    expect(switchLabel('paused')).toBe('Save and take over');
    for (const status of ['on', 'over_limit', 'needs_attention']) {
      expect(switchLabel(status)).toBeNull();
    }
  });
});

describe('lost values read plainly', () => {
  it('withStored takes a label for a lost value, else the default', () => {
    const out = withStored([], ['a', 'b'], { label: (v) => (v === 'a' ? 'Lost A' : undefined) });
    expect(out.map((o) => o.label)).toEqual(['Lost A', 'b (no longer available)']);
  });

  it('names a lost recipient or audience by its usual label, marking a lost parent', () => {
    expect(recipientLabel('admins')).toBe('All admins');
    expect(recipientLabel('parent_assignees')).toBe("Its parent's assignees (no longer available)");
    expect(recipientLabel('parent')).toBe("Its parent's assignees (no longer available)");
    expect(recipientLabel('linked:in:property.deal')).toBe('Assignees of a removed link');
    expect(recipientLabel('zzz')).toBe('zzz (no longer available)');
  });

  it('marks a stored action type the catalogue lost', () => {
    expect(actionOptions(catalogue, deal, 'create_task').map((o) => o.label)).toEqual([
      'Set a field',
      'Assign',
      'Create a task',
      'Notify',
      'Send to an endpoint'
    ]);
    const lost = actionOptions(catalogue, deal, 'teleport');
    expect(lost.at(-1)).toMatchObject({
      value: 'teleport',
      label: 'teleport (no longer available)'
    });
    const hook = actionOptions(catalogue, custom, 'webhook');
    expect(hook.at(-1)).toMatchObject({
      label: 'Send to an endpoint (no longer available)',
      gone: true
    });
  });

  it('shares one parent label between recipients and the task audience', () => {
    expect(parentAssignees(deal)).toBe("The account's assignees");
    expect(parentAssignees({ key: 'task', parent: null })).toBe("Its parent's assignees");
    expect(parentAssignees(lead)).toBeNull();
    const fromRecipients = recipientsFor(deal).find((r) => r.value === 'parent_assignees');
    const fromAudience = taskAudience(deal).find((r) => r.value === 'parent');
    expect(fromRecipients?.label).toBe(fromAudience?.label);
  });
});

describe('clear or unset', () => {
  it('a null from an input is not chosen, never a clear', () => {
    const a = { type: 'set_field', field: 'stage' };
    setActionValue(a, null);
    expect(a.value).toBeUndefined();
    expect(isClearing(a)).toBe(false);
    setActionValue(a, 's1');
    expect(a.value).toBe('s1');
    setActionValue(a, false);
    expect(a.value).toBe(false);
    setActionValue(a, 0);
    expect(a.value).toBe(0);
  });

  it('shows the placeholder while nothing is chosen', () => {
    expect(shownValue({})).toBeNull();
    expect(shownValue({ value: undefined })).toBeNull();
    expect(shownValue({ value: 's1' })).toBe('s1');
    expect(shownValue({ value: false })).toBe(false);
  });

  it('ticking clears, unticking restores what was there, else leaves it unchosen', () => {
    const a = { type: 'set_field', field: 'stage', value: 's2' };
    const before = a.value;
    applyClear(a, true, before);
    expect(a.value).toBeNull();
    expect(isClearing(a)).toBe(true);
    applyClear(a, false, before);
    expect(a.value).toBe('s2');
    const b = { type: 'set_field', field: 'stage' };
    applyClear(b, true, undefined);
    applyClear(b, false, undefined);
    expect(isClearing(b)).toBe(false);
    expect('value' in JSON.parse(JSON.stringify(b))).toBe(false);
  });

  it('a deliberate clear is dirty against an unchosen value', () => {
    const base = { name: 'n', actions: [{ type: 'set_field', target: 'record', field: 'f' }] };
    const cleared = {
      name: 'n',
      actions: [{ type: 'set_field', target: 'record', field: 'f', value: null }]
    };
    expect(isDirty(editorState(base, 'deal'), editorState(cleared, 'deal'))).toBe(true);
  });

  it('changing assign mode empties the people', () => {
    const a = { type: 'assign', mode: 'replace', people: ['p1'] };
    applyMode(a, 'rotate');
    expect(a).toEqual({ type: 'assign', mode: 'rotate', people: [] });
  });
});

describe('tryBlocked', () => {
  const one = [{ id: 'r', name: 'R' }];
  it('says to save first while the draft is dirty, whatever else is true', () => {
    const hint = 'Save first: Try uses the saved rule.';
    expect(tryBlocked({ dirty: true, busy: false, chosen: one })).toBe(hint);
    expect(tryBlocked({ dirty: true, busy: true, chosen: [] })).toBe(hint);
  });
  it('blocks without a hint while sending or with no record chosen', () => {
    expect(tryBlocked({ dirty: false, busy: true, chosen: one })).toBe('');
    expect(tryBlocked({ dirty: false, busy: false, chosen: [] })).toBe('');
  });
  it('allows a clean draft with a record chosen', () => {
    expect(tryBlocked({ dirty: false, busy: false, chosen: one })).toBeNull();
  });
});

describe('notificationText', () => {
  const evil = '<img src=x onerror=alert(1)>';

  it('writes the text for each automation verb', () => {
    expect(
      notificationText({ verb: 'automation.message', data: { message: evil, rule: 'Won' } }, 'UTC')
    ).toEqual({ text: evil, source: 'From the rule "Won"' });
    expect(
      notificationText(
        { verb: 'automation.failed', data: { rule: 'Close it', reason: 'Bad stage.' } },
        'UTC'
      )
    ).toEqual({ text: 'The rule "Close it" failed: Bad stage.', source: null });
    expect(
      notificationText(
        { verb: 'automation.paused', data: { reason: 'Rules paused.', rules: ['A', 'B'] } },
        'UTC'
      )
    ).toEqual({ text: 'Rules paused. Paused: A, B.', source: null });
    const limit = notificationText(
      { verb: 'automation.limit', data: { window_start: '2026-10-22T14:00:00+00:00' } },
      'UTC'
    );
    expect(limit?.text).toMatch(
      /^Automation reached its limit of 1,000 runs in the hour from .+\. The rest of that hour's runs were skipped\.$/
    );
    expect(limit?.text).toContain('14:00');
    expect(limit?.source).toBeNull();
  });

  it('answers null for other verbs and for data of the wrong type', () => {
    expect(notificationText({ verb: 'case.commented', data: {} }, 'UTC')).toBeNull();
    expect(
      notificationText({ verb: 'automation.message', data: { message: 5, rule: 'R' } }, 'UTC')
    ).toBeNull();
    expect(
      notificationText({ verb: 'automation.message', data: { message: 'x', rule: null } }, 'UTC')
    ).toBeNull();
    expect(notificationText({ verb: 'automation.failed', data: { rule: 'R' } }, 'UTC')).toBeNull();
    expect(
      notificationText({ verb: 'automation.paused', data: { reason: 'r', rules: 'A' } }, 'UTC')
    ).toBeNull();
    expect(
      notificationText({ verb: 'automation.paused', data: { reason: 'r', rules: [1] } }, 'UTC')
    ).toBeNull();
    expect(
      notificationText({ verb: 'automation.limit', data: { window_start: 3 } }, 'UTC')
    ).toBeNull();
    expect(notificationText({ verb: 'automation.message', data: null }, 'UTC')).toBeNull();
    expect(notificationText(null, 'UTC')).toBeNull();
  });
});

describe('notificationText time zones', () => {
  const n = { verb: 'automation.limit', data: { window_start: '2026-10-22T14:00:00+00:00' } };

  it('writes the limit hour in the org zone', () => {
    const kolkata = notificationText(n, 'Asia/Kolkata')?.text ?? '';
    expect(kolkata).toContain('19:30');
    expect(kolkata).not.toContain('14:00');
  });

  it('falls back to UTC for an invalid zone', () => {
    expect(notificationText(n, 'Not/AZone')?.text).toBe(notificationText(n, 'UTC')?.text);
  });
});

describe('the limit sentence mid-sentence', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  /** @param {string} at */
  const from = (at) =>
    notificationText({ verb: 'automation.limit', data: { window_start: at } }, 'UTC')?.text;

  it('writes today and yesterday in lower case', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-10-22T15:00:00Z'));
    expect(from('2026-10-22T14:00:00+00:00')).toContain('in the hour from today 14:00.');
    expect(from('2026-10-21T14:00:00+00:00')).toContain('in the hour from yesterday 14:00.');
    expect(from('2026-10-19T14:00:00+00:00')).toContain('in the hour from 19 Oct 14:00.');
  });
});

describe('actorName', () => {
  it('prefers a name, then the email, then Someone', () => {
    expect(actorName({ actor: { name: 'Asha', user_details: { email: 'a@x.io' } } })).toBe('Asha');
    expect(actorName({ actor: { id: '1', user_details: { email: 'a@x.io' } } })).toBe('a@x.io');
    expect(actorName({ actor: { id: '1', user_details: null } })).toBe('Someone');
    expect(actorName({ actor: null })).toBe('Someone');
  });
});

describe('rules paused by a module', () => {
  const off = /** @type {any[]} */ ([{ key: 'tickets', label: 'Tickets', available: false }]);

  it('knows a rule paused by its module from one paused by its owner', () => {
    const paused = { status: 'paused', object_key: 'ticket' };
    expect(pausedByModule(paused, off)).toBe(true);
    expect(pausedByModule(paused, null)).toBe(false);
    expect(pausedByModule({ status: 'paused', object_key: 'lead' }, off)).toBe(false);
    expect(pausedByModule({ status: 'paused', object_key: 'obj:invoice' }, off)).toBe(false);
    expect(pausedByModule({ status: 'on', object_key: 'ticket' }, off)).toBe(false);
  });

  it('names an object the catalogue no longer lists', () => {
    expect(OBJECT_LABELS.ticket).toBe('Ticket');
    expect(Object.keys(OBJECT_LABELS)).toEqual(
      expect.arrayContaining(['lead', 'contact', 'account', 'deal', 'ticket', 'task'])
    );
  });
});
