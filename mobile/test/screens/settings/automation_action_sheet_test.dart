import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/automation.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/settings/automation/automation_rule_screen.dart';
import 'package:bottle_crm/services/automation_text.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

const _id = '3f2b8c1e-7a4d-4e2b-9c1a-5d6e7f8a9b0c';

const _lead = AutomationObject(
  key: 'lead',
  label: 'Lead',
  labelPlural: 'Leads',
  fields: [
    RuleField(key: 'title', label: 'Title'),
    RuleField(key: 'assigned_to', label: 'Assigned to', type: 'people'),
  ],
);

const _account = AutomationObject(
  key: 'account',
  label: 'Account',
  labelPlural: 'Accounts',
  fields: [
    RuleField(
      key: 'status',
      label: 'Status',
      type: 'choice',
      choices: [
        RuleChoice(value: 'open', label: 'Open'),
        RuleChoice(value: 'sold', label: 'Sold'),
        RuleChoice(value: 'system', label: 'System', settable: false),
      ],
    ),
    RuleField(key: 'website', label: 'Website'),
    RuleField(key: 'score', label: 'Score', type: 'number', settable: false),
  ],
);

const _deal = AutomationObject(
  key: 'deal',
  label: 'Deal',
  labelPlural: 'Deals',
  fields: [
    RuleField(key: 'name', label: 'Name'),
    RuleField(key: 'amount', label: 'Amount', type: 'number'),
    RuleField(key: 'assigned_to', label: 'Assigned to', type: 'people'),
  ],
  parent: RuleParent(key: 'account', label: 'Account'),
  links: [
    RuleLinkSpec(
      id: 'properties',
      label: 'Properties linked through Deals',
      objectKey: 'property',
    ),
  ],
);

const _property = AutomationObject(
  key: 'property',
  label: 'Property',
  labelPlural: 'Properties',
  fields: [
    RuleField(
      key: 'state',
      label: 'State',
      type: 'choice',
      choices: [RuleChoice(value: 'listed', label: 'Listed')],
    ),
  ],
);

const _task = AutomationObject(
  key: 'task',
  label: 'Task',
  labelPlural: 'Tasks',
  fields: [
    RuleField(key: 'title', label: 'Title'),
    RuleField(key: 'assigned_to', label: 'Assigned to', type: 'people'),
  ],
);

const _custom = AutomationObject(
  key: 'obj:thing',
  label: 'Thing',
  labelPlural: 'Things',
  fields: [RuleField(key: 'name', label: 'Name')],
);

AutomationCatalogue _catalogue({
  int maxActions = 10,
  List<RuleEndpoint> endpoints = const [
    RuleEndpoint(id: 'e-1', description: 'Slack channel'),
  ],
}) => AutomationCatalogue(
  objects: const [_lead, _deal, _task, _account, _property, _custom],
  operators: const {
    'text': ['eq'],
  },
  actions: const ['set_field', 'assign', 'create_task', 'notify', 'webhook'],
  people: const [
    RulePerson(id: 'p-asha', name: 'Asha'),
    RulePerson(id: 'p-ben', name: 'Ben'),
  ],
  endpoints: endpoints,
  maxActions: maxActions,
);

AutomationRule _rule({
  String objectKey = 'deal',
  required List<ActionDraft> actions,
}) => AutomationRule(
  id: _id,
  name: 'Deal won: onboarding',
  objectKey: objectKey,
  trigger: TriggerDraft(),
  actions: actions,
);

ActionDraft _notify([String message = 'Kick off']) => ActionDraft(
  type: 'notify',
  values: {
    'to': ['record_assignees'],
    'people': <String>[],
    'message': message,
  },
);

ActionDraft _task1(String title) =>
    blankAction('create_task')..values['title'] = title;

class _FakeApi extends AutomationApi {
  final List<Map<String, dynamic>> bodies = [];
  RuleErrors? fail;

  @override
  Future<RuleWrite> create(Map<String, dynamic> body) async {
    bodies.add(body);
    return (
      rule: AutomationRule.fromJson({'object_key': 'lead', ...body, 'id': _id}),
      errors: null,
    );
  }

  @override
  Future<RuleWrite> update(String id, Map<String, dynamic> body) async {
    bodies.add(body);
    if (fail != null) return (rule: null, errors: fail);
    return (
      rule: AutomationRule.fromJson({'object_key': 'deal', ...body, 'id': id}),
      errors: null,
    );
  }
}

class _FakeRules extends AutomationRulesNotifier {
  @override
  Future<AutomationRulesAnswer> build() async =>
      AutomationRulesAnswer(rules: const []);
}

late _FakeApi _api;

Future<void> _open(
  WidgetTester tester, {
  AutomationRule? rule,
  AutomationCatalogue? catalogue,
}) async {
  _api = _FakeApi();
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final router = GoRouter(
    initialLocation: '/list',
    routes: [
      GoRoute(
        path: '/list',
        builder: (_, _) => const Scaffold(body: Text('the list')),
      ),
      GoRoute(
        path: AppRoutes.settingsAutomationNew,
        builder: (_, _) => const AutomationRuleScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsAutomationRuleDetail,
        builder: (_, state) => AutomationRuleScreen(
          key: ValueKey('rule-${state.pathParameters['ruleId']}'),
          ruleId: state.pathParameters['ruleId'],
        ),
      ),
    ],
  );
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        isOrgAdminProvider.overrideWithValue(true),
        automationCatalogueProvider.overrideWith(
          (ref) async => catalogue ?? _catalogue(),
        ),
        automationRulesProvider.overrideWith(_FakeRules.new),
        automationRuleProvider.overrideWith((ref, id) async => rule!),
        automationApiProvider.overrideWithValue(_api),
      ],
      child: MaterialApp.router(theme: AppTheme.light, routerConfig: router),
    ),
  );
  await tester.pumpAndSettle();
  router.push(
    rule == null
        ? AppRoutes.settingsAutomationNew
        : AppRoutes.settingsAutomationRule(_id),
  );
  await tester.pumpAndSettle();
}

Finder _iconButton(String tooltip) => find.ancestor(
  of: find.byTooltip(tooltip),
  matching: find.byType(IconButton),
);

Future<void> _tap(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Finder _dropdown(String label) => find.ancestor(
  of: find.text(label),
  matching: find.byWidgetPredicate((w) => w is DropdownButtonFormField),
);

Future<void> _openDropdown(WidgetTester tester, String label) =>
    _tap(tester, _dropdown(label).first);

Future<void> _choose(WidgetTester tester, String label, String item) async {
  await _openDropdown(tester, label);
  await tester.tap(find.text(item).last);
  await tester.pumpAndSettle();
}

ButtonStyleButton _button(WidgetTester tester, String label) =>
    tester.widget<ButtonStyleButton>(
      find
          .ancestor(
            of: find.text(label),
            matching: find.byWidgetPredicate((w) => w is ButtonStyleButton),
          )
          .first,
    );

Future<void> _addAction(WidgetTester tester, String type) async {
  await _tap(tester, find.text('Add action'));
  if (type != 'Create a task') await _choose(tester, 'Action', type);
}

Future<void> _pickPeople(WidgetTester tester, List<String> names) async {
  await _tap(tester, find.text('Choose'));
  for (final n in names) {
    await _tap(tester, find.text(n));
  }
  await _tap(tester, find.text('Done').last);
}

Future<void> _save(WidgetTester tester) => _tap(tester, find.text('Save'));

List get _actions => _api.bodies.last['actions'] as List;

void main() {
  testWidgets('offers only the action types the object takes', (tester) async {
    await _open(tester, rule: _rule(actions: [_notify()]));
    await _tap(tester, find.text('Add action'));
    await _openDropdown(tester, 'Action');
    for (final t in const [
      'Set a field',
      'Assign',
      'Create a task',
      'Notify',
      'Send to an endpoint',
    ]) {
      expect(find.text(t), findsWidgets, reason: t);
    }
    await tester.tap(find.text('Notify').last);
    await tester.pumpAndSettle();
    await _tap(tester, find.text('Cancel'));

    await _open(
      tester,
      rule: _rule(objectKey: 'obj:thing', actions: [_notify()]),
    );
    await _tap(tester, find.text('Add action'));
    await _openDropdown(tester, 'Action');
    expect(find.text('Set a field'), findsWidgets);
    expect(find.text('Create a task'), findsWidgets);
    expect(find.text('Assign'), findsNothing);
    expect(find.text('Send to an endpoint'), findsNothing);
  });

  testWidgets(
    'set a field lists the record, its parent and each link, then that object settable fields',
    (tester) async {
      await _open(tester, rule: _rule(actions: [_notify()]));
      await _addAction(tester, 'Set a field');
      await _openDropdown(tester, 'On');
      expect(find.text('This deal'), findsWidgets);
      expect(find.text('Its account'), findsOneWidget);
      expect(find.text('Properties linked through Deals'), findsOneWidget);
      await tester.tap(find.text('Its account'));
      await tester.pumpAndSettle();

      await _openDropdown(tester, 'Set');
      expect(find.text('Status'), findsWidgets);
      expect(find.text('Website'), findsOneWidget);
      expect(find.text('Score'), findsNothing);
      expect(find.text('Amount'), findsNothing);
      await tester.tap(find.text('Status').last);
      await tester.pumpAndSettle();

      expect(_button(tester, 'Done').onPressed, isNull);
      await _choose(tester, 'Value', 'Sold');
      expect(find.text('System'), findsNothing);
      await _tap(tester, find.text('Done'));
      expect(find.text('2. Set Status to Sold on its account'), findsOneWidget);

      await _save(tester);
      expect(_actions[1], {
        'type': 'set_field',
        'target': 'parent',
        'field': 'status',
        'value': 'sold',
      });

      // Another target clears the field and the value.
      await _tap(tester, find.text('2. Set Status to Sold on its account'));
      await _choose(tester, 'On', 'Properties linked through Deals');
      expect(_button(tester, 'Done').onPressed, isNull);
      expect(find.text('Sold'), findsNothing);
    },
  );

  testWidgets('clear it instead sends a null value', (tester) async {
    await _open(tester, rule: _rule(actions: [_notify()]));
    await _addAction(tester, 'Set a field');
    await _choose(tester, 'Set', 'Name');
    await _tap(tester, find.text('Clear it instead'));
    expect(find.widgetWithText(TextFormField, 'Value'), findsNothing);
    await _tap(tester, find.text('Done'));
    expect(find.text('2. Clear Name on this deal'), findsOneWidget);
    await _save(tester);
    expect(_actions[1], {
      'type': 'set_field',
      'target': 'record',
      'field': 'name',
      'value': null,
    });
  });

  testWidgets(
    'assign in turn needs 2 to 20 people and says it replaces current assignees',
    (tester) async {
      await _open(tester, rule: _rule(actions: [_notify()]));
      await _addAction(tester, 'Assign');
      expect(find.text('Replaces current assignees.'), findsOneWidget);
      expect(_button(tester, 'Done').onPressed, isNull);
      await _choose(tester, 'Person', 'Asha');
      expect(_button(tester, 'Done').onPressed, isNotNull);

      await _choose(tester, 'Who', 'In turn');
      expect(
        find.text(
          'Choose 2 to 20 people; each new record goes to the next one.',
        ),
        findsOneWidget,
      );
      expect(find.text('Replaces current assignees.'), findsOneWidget);
      expect(_button(tester, 'Done').onPressed, isNull);
      await _tap(tester, find.text('Asha'));
      await _tap(tester, find.text('Ben'));
      await _tap(tester, find.text('Done').last);
      expect(_button(tester, 'Done').onPressed, isNotNull);
      await _tap(tester, find.text('Done'));
      expect(find.text('2. Assign in turn to Asha, Ben'), findsOneWidget);
      await _save(tester);
      expect(_actions[1], {
        'type': 'assign',
        'mode': 'rotate',
        'people': ['p-asha', 'p-ben'],
      });
    },
  );

  testWidgets('create a task carries title, due days, priority and who', (
    tester,
  ) async {
    await _open(tester, rule: _rule(actions: [_notify()]));
    await _tap(tester, find.text('Add action'));
    expect(find.text('Create a task'), findsWidgets);
    expect(_button(tester, 'Done').onPressed, isNull);
    expect(find.text("{name} becomes the record's name."), findsOneWidget);
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Title'),
      'Kick-off call: {name}',
    );
    await tester.pump();
    await tester.enterText(find.widgetWithText(TextFormField, 'Due in'), '400');
    await tester.pump();
    expect(_button(tester, 'Done').onPressed, isNull);
    await tester.enterText(find.widgetWithText(TextFormField, 'Due in'), '3');
    await tester.pump();
    expect(_button(tester, 'Done').onPressed, isNotNull);
    await _choose(tester, 'Priority', 'High');
    await _openDropdown(tester, 'For');
    expect(find.text('Its assignees'), findsWidgets);
    expect(find.text("The account's assignees"), findsOneWidget);
    expect(find.text("The rule's owner"), findsOneWidget);
    await tester.tap(find.text('A chosen person').last);
    await tester.pumpAndSettle();
    expect(_button(tester, 'Done').onPressed, isNull);
    await _choose(tester, 'Person', 'Ben');
    await _tap(tester, find.text('Done'));
    expect(
      find.text('2. Create a task: Kick-off call: {name}'),
      findsOneWidget,
    );
    await _save(tester);
    expect(_actions[1], {
      'type': 'create_task',
      'title': 'Kick-off call: {name}',
      'due_in_days': 3,
      'priority': 'High',
      'assign_to': 'person',
      'person': 'p-ben',
    });

    // Emptying the days field means no due date.
    await _tap(tester, find.text('2. Create a task: Kick-off call: {name}'));
    await tester.enterText(find.widgetWithText(TextFormField, 'Due in'), '');
    await tester.pump();
    await _choose(tester, 'For', 'Its assignees');
    await _tap(tester, find.text('Done'));
    await _save(tester);
    expect(_actions[1]['due_in_days'], isNull);
    expect(_actions[1]['person'], isNull);
  });

  testWidgets('notify offers the recipients for the object and a message', (
    tester,
  ) async {
    await _open(tester, rule: _rule(actions: [_notify()]));
    await _addAction(tester, 'Notify');
    for (final t in const [
      'Its assignees',
      'Who created it',
      "The account's assignees",
      'All admins',
      'Assignees of Properties linked through Deals',
    ]) {
      expect(find.text(t), findsOneWidget, reason: t);
    }
    expect(find.text('And these people'), findsWidgets);
    expect(_button(tester, 'Done').onPressed, isNull);
    await _tap(tester, find.text('All admins'));
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Message'),
      'Heads up',
    );
    await tester.pump();
    expect(
      find.text('In the app and by email, to active members only.'),
      findsOneWidget,
    );
    await _pickPeople(tester, ['Asha']);
    expect(_button(tester, 'Done').onPressed, isNotNull);
    await _tap(tester, find.text('Done'));
    expect(find.text('2. Notify all admins, Asha'), findsOneWidget);
    await _save(tester);
    expect(_actions[1], {
      'type': 'notify',
      'to': ['admins'],
      'people': ['p-asha'],
      'message': 'Heads up',
    });
  });

  testWidgets('a webhook offers the endpoints by description', (tester) async {
    await _open(tester, rule: _rule(actions: [_notify()]));
    await _addAction(tester, 'Send to an endpoint');
    expect(_button(tester, 'Done').onPressed, isNull);
    await _choose(tester, 'Endpoint', 'Slack channel');
    await _tap(tester, find.text('Done'));
    expect(find.text('2. Send to Slack channel'), findsOneWidget);
  });

  testWidgets('actions move up and down and stop at the catalogue limit', (
    tester,
  ) async {
    await _open(
      tester,
      catalogue: _catalogue(maxActions: 3),
      rule: _rule(actions: [_task1('A'), _task1('B'), _task1('C')]),
    );
    expect(_button(tester, 'Add action').onPressed, isNull);
    expect(find.text('A rule can have at most 3 actions.'), findsOneWidget);

    expect(
      tester.widget<IconButton>(_iconButton('Move action 1 up')).onPressed,
      isNull,
    );
    expect(
      tester.widget<IconButton>(_iconButton('Move action 3 down')).onPressed,
      isNull,
    );
    expect(
      tester.getSize(_iconButton('Move action 2 down')).height,
      greaterThanOrEqualTo(44),
    );

    await _tap(tester, find.byTooltip('Move action 2 up'));
    expect(find.text('1. Create a task: B'), findsOneWidget);
    expect(find.text('2. Create a task: A'), findsOneWidget);
    await _tap(tester, find.byTooltip('Move action 2 down'));
    expect(find.text('2. Create a task: C'), findsOneWidget);
    expect(find.text('3. Create a task: A'), findsOneWidget);

    await _tap(tester, find.byTooltip('Remove action 1'));
    expect(find.text('1. Create a task: C'), findsOneWidget);
    expect(_button(tester, 'Add action').onPressed, isNotNull);
    expect(find.text('A rule can have at most 3 actions.'), findsNothing);

    await _save(tester);
    expect([for (final a in _actions) a['title']], ['C', 'A']);
  });

  testWidgets('an empty rule hints at least one action', (tester) async {
    await _open(tester, rule: _rule(actions: [_notify()]));
    expect(find.text('Add at least one action.'), findsNothing);
    await _tap(tester, find.byTooltip('Remove action 1'));
    expect(find.text('Add at least one action.'), findsOneWidget);
  });

  testWidgets('a stored person, option and endpoint the catalogue lost stay', (
    tester,
  ) async {
    await _open(
      tester,
      catalogue: _catalogue(endpoints: const []),
      rule: _rule(
        actions: [
          ActionDraft(
            type: 'assign',
            values: {
              'mode': 'replace',
              'people': ['p-gone'],
            },
          ),
          ActionDraft(type: 'webhook', values: {'endpoint': 'e-old'}),
          blankAction('create_task')
            ..values['title'] = 'T'
            ..values['priority'] = 'Urgent',
        ],
      ),
    );
    await _tap(tester, find.text('1. Assign to Someone no longer active'));
    expect(find.text('Someone no longer active'), findsWidgets);
    expect(_button(tester, 'Done').onPressed, isNotNull);
    await _tap(tester, find.text('Cancel'));

    await _tap(
      tester,
      find.text('2. Send to an endpoint that is no longer available'),
    );
    expect(
      find.text('Send to an endpoint (no longer available)'),
      findsOneWidget,
    );
    expect(find.text('An endpoint no longer available'), findsOneWidget);
    await _tap(tester, find.text('Done'));

    await _tap(tester, find.text('3. Create a task: T'));
    expect(find.text('Urgent (no longer available)'), findsOneWidget);
    await _tap(tester, find.text('Done'));
    await _save(tester);
    expect(_actions[0]['people'], ['p-gone']);
    expect(_actions[1]['endpoint'], 'e-old');
    expect(_actions[2]['priority'], 'Urgent');
  });

  testWidgets('a lost target, recipient and task audience read marked', (
    tester,
  ) async {
    await _open(
      tester,
      rule: _rule(
        objectKey: 'lead',
        actions: [
          ActionDraft(
            type: 'notify',
            values: {
              'to': ['linked:out:gone', 'parent_assignees'],
              'people': <String>[],
              'message': 'Heads up',
            },
          ),
          blankAction('create_task')
            ..values['title'] = 'Call back'
            ..values['assign_to'] = 'parent',
          ActionDraft(
            type: 'set_field',
            values: {'target': 'out:gone', 'field': 'state', 'value': 'x'},
          ),
        ],
      ),
    );
    expect(
      find.text(
        '1. Notify assignees of a removed link, '
        "its parent's assignees (no longer available)",
      ),
      findsOneWidget,
    );
    await _tap(
      tester,
      find.text(
        '1. Notify assignees of a removed link, '
        "its parent's assignees (no longer available)",
      ),
    );
    expect(find.text('Assignees of a removed link'), findsOneWidget);
    expect(
      find.text("Its parent's assignees (no longer available)"),
      findsOneWidget,
    );
    await _tap(tester, find.text('Done'));

    await _tap(tester, find.text('2. Create a task: Call back'));
    expect(
      find.text("Its parent's assignees (no longer available)"),
      findsOneWidget,
    );
    await _tap(tester, find.text('Done'));

    await _tap(
      tester,
      find.text(
        '3. Set a field that is no longer available to x on '
        'a target that is no longer available',
      ),
    );
    expect(find.text('A removed link'), findsOneWidget);
    expect(
      find.text('This field is no longer available. Choose another.'),
      findsOneWidget,
    );
    expect(find.text('Clear it instead'), findsNothing);
    // A lost target cannot be confirmed; Cancel keeps the row as stored.
    expect(_button(tester, 'Done').onPressed, isNull);
    await _tap(tester, find.text('Cancel'));
    await _save(tester);
    expect(_actions[0]['to'], ['linked:out:gone', 'parent_assignees']);
    expect(_actions[1]['assign_to'], 'parent');
    expect(_actions[2], {
      'type': 'set_field',
      'target': 'out:gone',
      'field': 'state',
      'value': 'x',
    });
  });

  testWidgets('unticking Clear it instead brings back the value it held', (
    tester,
  ) async {
    await _open(tester, rule: _rule(actions: [_notify()]));
    await _addAction(tester, 'Set a field');
    await _choose(tester, 'Set', 'Name');
    await tester.enterText(find.widgetWithText(TextFormField, 'Value'), 'Acme');
    await tester.pumpAndSettle();
    await _tap(tester, find.text('Clear it instead'));
    expect(find.widgetWithText(TextFormField, 'Value'), findsNothing);
    await _tap(tester, find.text('Clear it instead'));
    expect(find.text('Acme'), findsOneWidget);
    expect(_button(tester, 'Done').onPressed, isNotNull);
    await _tap(tester, find.text('Done'));
    expect(find.text('2. Set Name to Acme on this deal'), findsOneWidget);
  });

  testWidgets('changing an action type replaces it with a blank one', (
    tester,
  ) async {
    await _open(tester, rule: _rule(actions: [_notify('Kick off')]));
    await _tap(tester, find.text('1. Notify its assignees'));
    await tester.scrollUntilVisible(
      find.widgetWithText(TextFormField, 'Message'),
      200,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('Kick off'), findsOneWidget);
    await _choose(tester, 'Action', 'Create a task');
    expect(find.text('Kick off'), findsNothing);
    expect(_button(tester, 'Done').onPressed, isNull);
  });

  testWidgets('a new rule drops what its new object cannot take', (
    tester,
  ) async {
    await _open(tester);
    await _choose(tester, 'Object', 'Deal');
    await _addAction(tester, 'Send to an endpoint');
    await _choose(tester, 'Endpoint', 'Slack channel');
    await _tap(tester, find.text('Done'));
    await _addAction(tester, 'Create a task');
    await tester.enterText(find.widgetWithText(TextFormField, 'Title'), 'Go');
    await tester.pump();
    await _choose(tester, 'For', "The account's assignees");
    await _tap(tester, find.text('Done'));
    expect(find.text('1. Send to Slack channel'), findsOneWidget);

    // Lead takes webhooks and has no parent: the task falls back to the record.
    await _choose(tester, 'Object', 'Lead');
    expect(find.text('1. Send to Slack channel'), findsOneWidget);
    await _tap(tester, find.text('2. Create a task: Go'));
    expect(find.text("The account's assignees"), findsNothing);
    expect(
      tester
          .widget<DropdownButtonFormField<String>>(_dropdown('For').first)
          .initialValue,
      'record',
    );
    await _tap(tester, find.text('Cancel'));

    // A custom object takes no webhook.
    await _choose(tester, 'Object', 'Thing');
    expect(find.text('1. Send to Slack channel'), findsNothing);
    expect(find.text('1. Create a task: Go'), findsOneWidget);
    await _save(tester);
    expect(_actions, hasLength(1));
    expect(_actions[0]['assign_to'], 'record');
  });

  testWidgets('a task keeps its parent choice when the new object has one', (
    tester,
  ) async {
    await _open(tester);
    await _choose(tester, 'Object', 'Deal');
    await _addAction(tester, 'Create a task');
    await tester.enterText(find.widgetWithText(TextFormField, 'Title'), 'Go');
    await tester.pump();
    await _choose(tester, 'For', "The account's assignees");
    await _tap(tester, find.text('Done'));
    await _choose(tester, 'Object', 'Task');
    await _tap(tester, find.text('Save'));
    expect(_api.bodies.last['actions'][0]['assign_to'], 'parent');
  });

  testWidgets('moving an action leaves no error mark on the wrong card', (
    tester,
  ) async {
    await _open(tester, rule: _rule(actions: [_task1('A'), _task1('B')]));
    _api.fail = RuleErrors(rows: {'actions.1': 'Enter a title of 1 to 200.'});
    await _save(tester);
    expect(find.text('Enter a title of 1 to 200.'), findsOneWidget);

    await _tap(tester, find.byTooltip('Move action 2 up'));
    expect(find.text('1. Create a task: B'), findsOneWidget);
    expect(find.text('Enter a title of 1 to 200.'), findsNothing);
  });

  testWidgets('a new rule drops an assign its new object cannot take', (
    tester,
  ) async {
    await _open(tester);
    await _choose(tester, 'Object', 'Deal');
    await _addAction(tester, 'Assign');
    await _choose(tester, 'Person', 'Asha');
    await _tap(tester, find.text('Done'));
    expect(find.text('1. Assign to Asha'), findsOneWidget);
    await _choose(tester, 'Object', 'Thing');
    expect(find.text('1. Assign to Asha'), findsNothing);
    expect(find.text('Add at least one action.'), findsOneWidget);
  });

  testWidgets('a stored one-person assign holding several asks for one', (
    tester,
  ) async {
    await _open(
      tester,
      rule: _rule(
        actions: [
          ActionDraft(
            type: 'assign',
            values: {
              'mode': 'replace',
              'people': ['p-asha', 'p-ben'],
            },
          ),
        ],
      ),
    );
    await _tap(tester, find.text('1. Assign to Asha, Ben'));
    expect(
      find.text('One person takes exactly one. Choose who stays.'),
      findsOneWidget,
    );
    expect(_button(tester, 'Done').onPressed, isNull);
    await _choose(tester, 'Person', 'Ben');
    expect(_button(tester, 'Done').onPressed, isNotNull);
    await _tap(tester, find.text('Done'));
    await _save(tester);
    expect(_actions[0]['people'], ['p-ben']);
  });
}
