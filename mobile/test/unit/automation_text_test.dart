import 'package:bottle_crm/data/models/automation.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:bottle_crm/services/automation_text.dart';
import 'package:flutter_test/flutter_test.dart';

const uuid = '3f2b8c1e-5a4d-4e2f-9b7a-1c2d3e4f5a6b';

Map<String, dynamic> field(
  String key,
  String label,
  String type, {
  bool settable = true,
  List<Map<String, dynamic>> choices = const [],
}) => {
  'key': key,
  'label': label,
  'type': type,
  'settable': settable,
  'choices': choices,
};

AutomationCatalogue catalogue({
  bool settableAssignees = true,
  bool endpoints = true,
  bool links = true,
}) => AutomationCatalogue.fromJson({
  'objects': [
    {
      'key': 'deal',
      'label': 'Deal',
      'label_plural': 'Deals',
      'parent': {'key': 'account', 'label': 'Account'},
      'links': links
          ? [
              {
                'id': 'out:properties',
                'label': 'Properties linked through Deals',
                'object_key': 'obj:property',
              },
            ]
          : [],
      'fields': [
        field(
          'stage',
          'Stage',
          'choice',
          choices: [
            {'value': 's1', 'label': 'Proposal', 'group': 'Sales'},
          ],
        ),
        field(
          'stage_kind',
          'Outcome',
          'choice',
          settable: false,
          choices: [
            {'value': 'won', 'label': 'Won (any pipeline)', 'settable': false},
          ],
        ),
        field('amount', 'Amount', 'number'),
        field('close_date', 'Close date', 'date'),
        field('is_hot', 'Hot', 'boolean'),
        field('name', 'Name', 'text'),
        field(
          'assigned_to',
          'Assignees',
          'people',
          settable: settableAssignees,
        ),
      ],
    },
    {
      'key': 'account',
      'label': 'Account',
      'label_plural': 'Accounts',
      'fields': [field('name', 'Name', 'text')],
    },
    {
      'key': 'obj:property',
      'label': 'Property',
      'label_plural': 'Properties',
      'fields': [
        field(
          'status',
          'Status',
          'choice',
          choices: [
            {'value': 'sold', 'label': 'Sold'},
          ],
        ),
      ],
    },
    {
      'key': 'task',
      'label': 'Task',
      'label_plural': 'Tasks',
      'parent': {'key': 'deal', 'label': 'Deal'},
      'fields': [field('name', 'Name', 'text')],
    },
  ],
  'operators': {
    'text': ['eq', 'neq', 'contains', 'not_contains', 'empty', 'not_empty'],
    'number': ['eq', 'gt', 'lt'],
    'date': ['eq', 'gt', 'lt'],
    'choice': ['eq', 'neq', 'in', 'not_in'],
    'boolean': ['true', 'false'],
    'person': ['eq', 'neq'],
    'people': ['eq', 'includes', 'excludes', 'empty', 'not_empty'],
  },
  'update_only_operators': ['was', 'was_not'],
  'actions': ['set_field', 'assign', 'create_task', 'notify', 'webhook'],
  'people': [
    {'id': 'p1', 'name': 'Ravi'},
    {'id': 'p2', 'name': 'Meera'},
  ],
  'endpoints': endpoints
      ? [
          {'id': 'e1', 'description': 'Billing hook'},
        ]
      : [],
});

AutomationObject obj(AutomationCatalogue c, String key) =>
    c.objects.firstWhere((o) => o.key == key);

AutomationRuleRow rowWith({
  String status = 'on',
  String statusText = '',
  int runs = 0,
  int failures = 0,
}) => AutomationRuleRow(
  id: uuid,
  trigger: TriggerDraft(),
  status: status,
  statusText: statusText,
  runs7d: runs,
  failures7d: failures,
);

ApiResponse<Map<String, dynamic>> failed(
  int code, {
  Map<String, dynamic>? body,
  String? message,
}) => ApiResponse<Map<String, dynamic>>(
  success: false,
  data: body,
  message: message,
  statusCode: code,
);

void main() {
  final c = catalogue();
  final deal = obj(c, 'deal');
  RuleField f(String key) => deal.fields.firstWhere((x) => x.key == key);

  group('operators', () {
    test('offers was and was_not only on an updated trigger, never on '
        'people', () {
      expect(operatorsFor(c, f('amount'), 'created'), ['eq', 'gt', 'lt']);
      expect(operatorsFor(c, f('amount'), 'updated'), [
        'eq',
        'gt',
        'lt',
        'was',
        'was_not',
      ]);
      expect(operatorsFor(c, f('assigned_to'), 'updated'), [
        'eq',
        'includes',
        'excludes',
        'empty',
        'not_empty',
      ]);
      expect(operatorsFor(c, null, 'updated'), isEmpty);
    });

    test('picks the value input for each type and operator', () {
      ValueKind k(String key, String op) => valueKind(f(key), op);
      expect(k('name', 'eq'), ValueKind.text);
      expect(k('amount', 'gt'), ValueKind.number);
      expect(k('close_date', 'lt'), ValueKind.date);
      expect(k('stage', 'eq'), ValueKind.choice);
      expect(k('stage', 'in'), ValueKind.choices);
      expect(k('stage', 'not_in'), ValueKind.choices);
      expect(k('assigned_to', 'eq'), ValueKind.people);
      expect(k('assigned_to', 'includes'), ValueKind.person);
      expect(k('is_hot', 'was'), ValueKind.boolean);
      expect(k('amount', 'empty'), ValueKind.none);
      expect(k('is_hot', 'true'), ValueKind.none);
      expect(k('name', 'not_empty'), ValueKind.none);
      expect(
        valueKind(const RuleField(key: 'p', label: 'P', type: 'person'), 'eq'),
        ValueKind.person,
      );
    });

    test('labels every operator in the web copy', () {
      const labels = {
        'eq': 'is',
        'neq': 'is not',
        'contains': 'contains',
        'not_contains': 'does not contain',
        'gt': 'is more than',
        'lt': 'is less than',
        'in': 'is any of',
        'not_in': 'is none of',
        'true': 'is true',
        'false': 'is false',
        'includes': 'includes',
        'excludes': 'does not include',
        'empty': 'is empty',
        'not_empty': 'is not empty',
        'was': 'was',
        'was_not': 'was not',
      };
      labels.forEach((op, label) => expect(operatorLabel(op, 'text'), label));
      expect(operatorLabel('gt', 'date'), 'is after');
      expect(operatorLabel('lt', 'date'), 'is before');
      expect(operatorLabel('eq', 'people'), 'is exactly');
      expect(operatorLabel('eq', 'date'), 'is');
      expect(operatorLabel('odd'), 'odd');
    });
  });

  group('actions', () {
    test('leaves out assign without settable assignees, and webhook on a '
        'custom object or with no endpoints', () {
      expect(actionTypes(c, deal), [
        'set_field',
        'assign',
        'create_task',
        'notify',
        'webhook',
      ]);
      final noAssign = catalogue(settableAssignees: false);
      expect(actionTypes(noAssign, obj(noAssign, 'deal')), [
        'set_field',
        'create_task',
        'notify',
        'webhook',
      ]);
      expect(actionTypes(c, obj(c, 'account')), [
        'set_field',
        'create_task',
        'notify',
        'webhook',
      ]);
      expect(actionTypes(c, obj(c, 'obj:property')), [
        'set_field',
        'create_task',
        'notify',
      ]);
      final noHooks = catalogue(endpoints: false);
      expect(actionTypes(noHooks, obj(noHooks, 'deal')), [
        'set_field',
        'assign',
        'create_task',
        'notify',
      ]);
      expect(actionTypes(c, null), [
        'set_field',
        'create_task',
        'notify',
        'webhook',
      ]);
    });

    test('blanks each action with the web defaults', () {
      expect(blankAction('create_task').type, 'create_task');
      expect(blankAction('create_task').values, {
        'title': '',
        'due_in_days': 2,
        'priority': 'Medium',
        'assign_to': 'record',
        'person': null,
      });
      expect(blankAction('notify').values, {
        'to': <String>[],
        'people': <String>[],
        'message': '',
      });
      expect(blankAction('set_field').values, {
        'target': 'record',
        'field': '',
        'value': null,
      });
      expect(blankAction('assign').values, {
        'mode': 'replace',
        'people': <String>[],
      });
      expect(blankAction('webhook').values, {'endpoint': ''});
      expect(blankAction('other').values, isEmpty);
    });

    test('offers the parent and each link as a target', () {
      final t = targetsFor(c, deal);
      expect(t.map((x) => x.value), ['record', 'parent', 'out:properties']);
      expect(t.map((x) => x.label), [
        'This deal',
        'Its account',
        'Properties linked through Deals',
      ]);
      expect(t[1].object.key, 'account');
      expect(t[2].object.key, 'obj:property');
      final bare = catalogue(links: false);
      expect(targetsFor(bare, obj(bare, 'deal')).length, 2);
      expect(targetsFor(c, obj(c, 'account')).map((x) => x.value), ['record']);
      expect(targetsFor(c, null), isEmpty);
    });

    test('offers the recipients each object has', () {
      expect(recipientsFor(deal).map((x) => '${x.value}=${x.label}'), [
        'record_assignees=Its assignees',
        'record_creator=Who created it',
        "parent_assignees=The account's assignees",
        'admins=All admins',
        'linked:out:properties=Assignees of Properties linked through Deals',
      ]);
      expect(
        recipientsFor(obj(c, 'task')).map((x) => x.label),
        contains("Its parent's assignees"),
      );
      expect(recipientsFor(obj(c, 'account')).map((x) => x.value), [
        'record_assignees',
        'record_creator',
        'admins',
      ]);
    });
  });

  group('withStored', () {
    test('keeps a stored value the options lost, marked as gone', () {
      const options = [RuleOption(value: 'a', label: 'A')];
      final out = withStored(options, ['a', 'zz', 'zz', '', null]);
      expect(out.map((o) => o.value), ['a', 'zz']);
      expect(out.last.label, 'zz (no longer available)');
      expect(out.last.gone, isTrue);
      expect(out.first.gone, isFalse);
      expect(withStored(options, 'a'), hasLength(1));
      expect(withStored(options, null), hasLength(1));
      final people = withStored(options, 'p9', person: true);
      expect(people.last.label, 'Someone no longer active');
      expect(people.last.gone, isTrue);
    });

    test('a lost value reads as the label asked for, still marked', () {
      const options = [RuleOption(value: 'a', label: 'A')];
      final out = withStored(options, 'e-old', label: (_) => 'A removed link');
      expect(out.last.label, 'A removed link');
      expect(out.last.value, 'e-old');
      expect(out.last.gone, isTrue);
      expect(out.last.settable, isFalse);
    });
  });

  group('recipientLabel', () {
    test(
      'a recipient the object no longer offers reads as usual or marked',
      () {
        expect(recipientLabel('record_assignees'), 'Its assignees');
        expect(recipientLabel('record_creator'), 'Who created it');
        expect(
          recipientLabel('parent_assignees'),
          "Its parent's assignees (no longer available)",
        );
        expect(recipientLabel('admins'), 'All admins');
        expect(recipientLabel('record'), 'Its assignees');
        expect(
          recipientLabel('parent'),
          "Its parent's assignees (no longer available)",
        );
        expect(recipientLabel('owner'), "The rule's owner");
        expect(recipientLabel('person'), 'A chosen person');
        expect(
          recipientLabel('linked:out:gone'),
          'Assignees of a removed link',
        );
        expect(recipientLabel('zz'), 'zz (no longer available)');
      },
    );
  });

  group('changeHint', () {
    const stage = RuleField(
      key: 'stage',
      label: 'Stage',
      type: 'choice',
      choices: [RuleChoice(value: 's-won', label: 'Won', group: 'Sales')],
    );
    const flag = RuleField(key: 'hot', label: 'Hot', type: 'boolean');
    const city = RuleField(key: 'city', label: 'City');

    test('says the rule runs once, on the move into the value', () {
      expect(
        changeHint(stage, 's-won'),
        'Runs once, when the stage moves into Won; '
        'later edits do not run it again.',
      );
      expect(
        changeHint(city, 'Pune'),
        'Runs once, when the city moves into Pune; '
        'later edits do not run it again.',
      );
    });

    test('reads a boolean as Yes or No and a lost option as stored', () {
      expect(changeHint(flag, true), contains('moves into Yes;'));
      expect(changeHint(flag, 'true'), contains('moves into Yes;'));
      expect(changeHint(flag, false), contains('moves into No;'));
      expect(changeHint(stage, 's-gone'), contains('moves into s-gone;'));
    });

    test('is null until there is a field and a value', () {
      expect(changeHint(null, 's-won'), isNull);
      expect(changeHint(stage, null), isNull);
      expect(changeHint(stage, ''), isNull);
    });
  });

  group('sentences', () {
    AutomationRule rule(TriggerDraft t) =>
        AutomationRule(id: uuid, objectKey: 'deal', trigger: t);

    test('says the trigger in words', () {
      String s(TriggerDraft t) => triggerSentence(rule(t), c);
      expect(s(TriggerDraft()), 'Created');
      expect(s(TriggerDraft(event: 'updated')), 'Updated');
      expect(
        s(TriggerDraft(event: 'updated', field: 'stage')),
        'Stage changes',
      );
      expect(
        s(TriggerDraft(event: 'updated', field: 'stage_kind', to: 'won')),
        'Outcome changes to Won (any pipeline)',
      );
      expect(
        s(TriggerDraft(event: 'updated', field: 'stage', to: 'gone')),
        'Stage changes to gone (no longer available)',
      );
      expect(
        s(TriggerDraft(event: 'updated', field: 'is_hot', to: true)),
        'Hot changes to Yes',
      );
      expect(
        s(TriggerDraft(event: 'updated', field: 'is_hot', to: 'false')),
        'Hot changes to No',
      );
      expect(
        s(TriggerDraft(event: 'updated', field: 'amount', to: '5')),
        'Amount changes to 5',
      );
      expect(
        s(TriggerDraft(event: 'updated', field: 'zzz')),
        'A field that is no longer available changes',
      );
    });

    test('says a condition in words', () {
      String s(String fieldKey, String op, dynamic v) => conditionSentence(
        ConditionDraft(field: fieldKey, op: op, value: v),
        deal,
        c,
      );
      expect(s('amount', 'gt', '0'), 'Amount is more than 0');
      expect(
        s('close_date', 'gt', '2026-01-02'),
        'Close date is after 2026-01-02',
      );
      expect(
        s('stage', 'in', ['s1', 'x']),
        'Stage is any of Proposal, x (no longer available)',
      );
      expect(s('is_hot', 'was', true), 'Hot was Yes');
      expect(s('name', 'empty', null), 'Name is empty');
      expect(s('assigned_to', 'includes', 'p1'), 'Assignees includes Ravi');
      expect(
        s('assigned_to', 'eq', ['p1', 'p2']),
        'Assignees is exactly Ravi, Meera',
      );
      expect(
        s('assigned_to', 'includes', 'p9'),
        'Assignees includes Someone no longer active',
      );
      expect(s('zzz', 'eq', 'a'), 'A field that is no longer available is a');
      expect(s('amount', 'eq', 2.0), 'Amount is 2');
    });

    test('says each action in words', () {
      String s(String type, Map<String, dynamic> values) =>
          actionSentence(ActionDraft(type: type, values: values), deal, c);
      expect(
        s('create_task', {'title': 'Kick-off call: {name}'}),
        'Create a task: Kick-off call: {name}',
      );
      expect(s('create_task', {'title': ''}), 'Create a task');
      expect(
        s('notify', {
          'to': ['parent_assignees'],
          'people': <String>[],
        }),
        "Notify the account's assignees",
      );
      expect(
        s('notify', {
          'to': ['record_assignees', 'admins'],
          'people': ['p1', 'p9'],
        }),
        'Notify its assignees, all admins, Ravi, Someone no longer active',
      );
      expect(s('notify', {'to': <String>[], 'people': <String>[]}), 'Notify');
      expect(
        s('set_field', {
          'target': 'out:properties',
          'field': 'status',
          'value': 'sold',
        }),
        'Set Status to Sold on Properties linked through Deals',
      );
      expect(
        s('set_field', {'target': 'record', 'field': 'amount', 'value': 3}),
        'Set Amount to 3 on this deal',
      );
      expect(
        s('set_field', {'target': 'parent', 'field': 'name', 'value': null}),
        'Clear Name on its account',
      );
      expect(
        s('set_field', {'target': 'record', 'field': 'zzz', 'value': 'a'}),
        'Set a field that is no longer available to a on this deal',
      );
      expect(
        s('assign', {
          'mode': 'replace',
          'people': ['p1'],
        }),
        'Assign to Ravi',
      );
      expect(
        s('assign', {
          'mode': 'rotate',
          'people': ['p1', 'p2'],
        }),
        'Assign in turn to Ravi, Meera',
      );
      expect(s('webhook', {'endpoint': 'e1'}), 'Send to Billing hook');
      expect(
        s('webhook', {'endpoint': 'e9'}),
        'Send to an endpoint that is no longer available',
      );
      expect(
        s('notify', {
          'to': ['linked:out:gone', 'zz'],
          'people': <String>[],
        }),
        'Notify assignees of a removed link, zz (no longer available)',
      );
      expect(s('mystery', {}), 'An action that is no longer available');
    });

    test('counts runs in words', () {
      expect(runsLabel(rowWith()), 'No runs');
      expect(runsLabel(rowWith(runs: 1)), '1 run');
      expect(runsLabel(rowWith(runs: 14)), '14 runs');
      expect(runsLabel(rowWith(runs: 52, failures: 1)), '52 runs, 1 failed');
    });

    test('labels statuses without plan words', () {
      expect(
        [
          for (final s in [
            'on',
            'off',
            'paused',
            'over_limit',
            'needs_attention',
          ])
            statusLabel(s),
        ],
        ['On', 'Off', 'Paused', 'Not running', 'Needs attention'],
      );
      expect(statusLabel('weird'), 'Off');
      expect(
        statusText(
          rowWith(
            status: 'over_limit',
            statusText: "Over this install's limit",
          ),
        ),
        'This rule is not running for this organization right now.',
      );
      expect(
        statusText(rowWith(status: 'paused', statusText: 'Owner left.')),
        'Owner left.',
      );
      expect(
        statusText(rowWith(status: 'needs_attention', statusText: 'Broken.')),
        'Broken.',
      );
      expect(statusText(rowWith(status: 'paused')), isNull);
      expect(statusText(rowWith(status: 'on', statusText: 'x')), isNull);
      expect(statusText(rowWith(status: 'off')), isNull);
    });

    test('ruleStatus reads the list row, or else the rule itself', () {
      AutomationRule rule({bool on = false, String paused = ''}) =>
          AutomationRule(
            id: uuid,
            trigger: TriggerDraft(),
            isActive: on,
            pausedReason: paused,
          );
      expect(ruleStatus(null, null), isNull);
      expect(
        ruleStatus(rule(), rowWith(status: 'needs_attention')),
        'needs_attention',
      );
      expect(ruleStatus(rule(on: true), null), 'on');
      expect(ruleStatus(rule(paused: 'Asha left.'), null), 'paused');
      expect(ruleStatus(rule(), null), 'off');
    });
  });

  group('ruleBody', () {
    RuleDraft draft() => RuleDraft(
      name: 'A',
      objectKey: 'deal',
      trigger: TriggerDraft(event: 'updated', field: 'stage_kind', to: 'won'),
      conditions: [ConditionDraft(field: 'amount', op: 'gt', value: '0')],
      actions: [
        ActionDraft(
          type: 'notify',
          values: {
            'to': ['admins'],
            'people': <String>[],
            'message': 'Won: {name}',
            'target': 'record',
            'junk': 1,
          },
        ),
      ],
    );

    test('builds the body with only the api keys, object_key on create, '
        'is_active only when switching on', () {
      expect(ruleBody(draft(), create: false), {
        'name': 'A',
        'match': 'all',
        'trigger': {'event': 'updated', 'field': 'stage_kind', 'to': 'won'},
        'conditions': [
          {'field': 'amount', 'op': 'gt', 'value': '0'},
        ],
        'actions': [
          {
            'type': 'notify',
            'to': ['admins'],
            'people': <String>[],
            'message': 'Won: {name}',
          },
        ],
      });
      final create = ruleBody(draft(), create: true);
      expect(create['object_key'], 'deal');
      expect(create.containsKey('is_active'), isFalse);
      expect(ruleBody(draft(), create: false).containsKey('object_key'), false);
      expect(
        ruleBody(draft(), create: false, switchOn: true)['is_active'],
        true,
      );
      expect(
        ruleBody(draft(), create: true, switchOn: true)['is_active'],
        true,
      );
    });

    test('sends no field or value on a created trigger', () {
      final d = draft()..trigger = TriggerDraft(field: 'stage', to: 'x');
      expect(ruleBody(d, create: false)['trigger'], {'event': 'created'});
    });

    test('sends no field or value for an updated trigger on any field', () {
      final d = draft()..trigger = TriggerDraft(event: 'updated', to: 'x');
      expect(ruleBody(d, create: false)['trigger'], {'event': 'updated'});
      d.trigger = TriggerDraft(event: 'updated', field: 'stage');
      expect(ruleBody(d, create: false)['trigger'], {
        'event': 'updated',
        'field': 'stage',
      });
    });

    test('keeps only the keys of each action type', () {
      Map<String, dynamic> body(String type, Map<String, dynamic> v) =>
          ruleBody(
                draft()..actions = [ActionDraft(type: type, values: v)],
                create: false,
              )['actions'][0]
              as Map<String, dynamic>;
      const stale = {
        'target': 't',
        'field': 'f',
        'value': 1,
        'mode': 'replace',
        'people': ['p'],
        'title': 'T',
        'due_in_days': 2,
        'priority': 'Low',
        'assign_to': 'record',
        'person': null,
        'to': ['admins'],
        'message': 'm',
        'endpoint': 'e',
        'junk': true,
      };
      expect(body('set_field', stale).keys, [
        'type',
        'target',
        'field',
        'value',
      ]);
      expect(body('assign', stale).keys, ['type', 'mode', 'people']);
      expect(body('create_task', stale).keys, [
        'type',
        'title',
        'due_in_days',
        'priority',
        'assign_to',
        'person',
      ]);
      expect(body('notify', stale).keys, ['type', 'to', 'people', 'message']);
      expect(body('webhook', stale).keys, ['type', 'endpoint']);
      expect(body('webhook', {'junk': 1}), {'type': 'webhook'});
    });

    test('sends a null value for an operator that takes none', () {
      final d = draft()
        ..conditions = [
          for (final op in ['empty', 'not_empty', 'true', 'false'])
            ConditionDraft(field: 'name', op: op, value: 'stale'),
          ConditionDraft(field: 'name', op: 'eq', value: 'keep'),
        ];
      final out = ruleBody(d, create: false)['conditions'] as List;
      expect(out.take(4).map((c) => c['value']), everyElement(isNull));
      expect(out.last['value'], 'keep');
    });

    test('sends person null unless the task is for a chosen person', () {
      Map<String, dynamic> task(String assignTo) =>
          ruleBody(
                draft()
                  ..actions = [
                    ActionDraft(
                      type: 'create_task',
                      values: {
                        'title': 'T',
                        'assign_to': assignTo,
                        'person': 'p1',
                      },
                    ),
                  ],
                create: false,
              )['actions'][0]
              as Map<String, dynamic>;
      expect(task('record')['person'], isNull);
      expect(task('record').containsKey('person'), isTrue);
      expect(task('person')['person'], 'p1');
    });

    test('omits an updated trigger value that is null or empty', () {
      final d = draft();
      d.trigger = TriggerDraft(event: 'updated', field: 'name', to: '');
      expect(ruleBody(d, create: false)['trigger'], {
        'event': 'updated',
        'field': 'name',
      });
      d.trigger = TriggerDraft(event: 'updated', field: 'is_hot', to: false);
      expect(ruleBody(d, create: false)['trigger']['to'], false);
    });

    test('always sends value on set_field, null when absent', () {
      final d = draft()
        ..actions = [
          ActionDraft(
            type: 'set_field',
            values: {'target': 'record', 'field': 'f'},
          ),
        ];
      final a = ruleBody(d, create: false)['actions'][0] as Map;
      expect(a.containsKey('value'), isTrue);
      expect(a['value'], isNull);
    });

    test('passes a stored id the catalogue no longer lists through '
        'unchanged', () {
      final d = draft()
        ..actions = [
          ActionDraft(
            type: 'assign',
            values: {
              'mode': 'replace',
              'people': ['gone-id'],
            },
          ),
        ];
      expect(ruleBody(d, create: false)['actions'][0]['people'], ['gone-id']);
    });
  });

  group('RuleErrors', () {
    test('maps row errors to row keys, first message per row', () {
      final e = RuleErrors.fromResponse(
        failed(
          400,
          body: {
            'errors': {
              'conditions[0].value': ['Enter a number.'],
              'actions[1].type': ['Unknown action.'],
              'actions[1].people': ['Second.'],
              'trigger.field': ['This field is not available.'],
              'name': ['Name it.'],
              'match': ['Pick one.'],
              'conditions': ['Too many.'],
              'actions': ['Add one.'],
              'trigger': ['Bad.'],
            },
          },
          message: 'ignored',
        ),
      );
      expect(e.general, isNull);
      expect(e.rows, {
        'conditions.0': 'Enter a number.',
        'actions.1': 'Unknown action.',
        'trigger': 'This field is not available.',
        'name': 'Name it.',
        'match': 'Pick one.',
        'conditions': 'Too many.',
        'actions': 'Add one.',
      });
    });

    test('keeps the first trigger message whichever path it came from', () {
      final e = RuleErrors.fromResponse(
        failed(
          400,
          body: {
            'errors': {
              'trigger.to': ['Enter a value.'],
              'trigger.field': ['Later.'],
            },
          },
        ),
      );
      expect(e.rows, {'trigger': 'Enter a value.'});
    });

    test('shows the neutral sentence for a plan_limit 403', () {
      final e = RuleErrors.fromResponse(
        failed(
          403,
          body: {
            'detail': 'This install allows 2 active automation rules.',
            'code': 'plan_limit',
          },
          message: 'This install allows 2 active automation rules.',
        ),
      );
      expect(
        e.general,
        "This rule can't be switched on for this organization right now.",
      );
      expect(e.rows, isEmpty);
    });

    test('sends a path with no row to general, first message', () {
      for (final path in ['is_active', 'object_key', 'ids']) {
        final e = RuleErrors.fromResponse(
          failed(
            400,
            body: {
              'errors': {
                path: ['First.', 'Second.'],
              },
            },
          ),
        );
        expect(e.general, 'First.');
        expect(e.rows, isEmpty);
      }
      final both = RuleErrors.fromResponse(
        failed(
          400,
          body: {
            'errors': {
              'name': ['Name it.'],
              'is_active': ['Nope.'],
            },
          },
        ),
      );
      expect(both.rows, {'name': 'Name it.'});
      expect(both.general, 'Nope.');
    });

    test('still gives a message when a 400 maps to no rows', () {
      for (final errors in <dynamic>[
        <String, dynamic>{},
        {'name': <String>[]},
        {
          'name': [3],
        },
        'plain',
      ]) {
        final e = RuleErrors.fromResponse(
          failed(400, body: {'errors': errors}, message: 'Server said no.'),
        );
        expect(e.rows, isEmpty);
        expect(e.general, 'Server said no.');
      }
    });

    test('gives the response message for any other failure', () {
      final other403 = RuleErrors.fromResponse(
        failed(403, body: {'detail': 'Admins only.'}, message: 'Admins only.'),
      );
      expect(other403.general, 'Admins only.');
      expect(other403.rows, isEmpty);
      final offline = RuleErrors.fromResponse(
        failed(0, message: 'Cannot reach the server.'),
      );
      expect(offline.general, 'Cannot reach the server.');
      final none = RuleErrors.fromResponse(failed(500));
      expect(none.general, isNotEmpty);
    });
  });

  group('recordPath', () {
    test('delegates to the app router', () {
      expect(recordPath('deal', uuid), linkedRecordRoute('deal', uuid));
      expect(recordPath('deal', uuid), isNotNull);
      expect(recordPath('obj:property', uuid), isNotNull);
      expect(recordPath('invoice', uuid), isNull);
    });

    test('refuses an id that is not a UUID', () {
      expect(recordPath('lead', 'a/b'), isNull);
      expect(recordPath('lead', 'abc'), isNull);
      expect(recordPath('lead', ''), isNull);
    });
  });
}
