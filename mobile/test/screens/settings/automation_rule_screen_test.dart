import 'dart:async';

import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/automation.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/settings/automation/automation_rule_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:bottle_crm/services/automation_text.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

const _id = '3f2b8c1e-7a4d-4e2b-9c1a-5d6e7f8a9b0c';
const _newId = '9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d';

const _lead = AutomationObject(
  key: 'lead',
  label: 'Lead',
  labelPlural: 'Leads',
  fields: [RuleField(key: 'title', label: 'Title')],
);

const _deal = AutomationObject(
  key: 'deal',
  label: 'Deal',
  labelPlural: 'Deals',
  fields: [
    RuleField(key: 'name', label: 'Name'),
    RuleField(key: 'amount', label: 'Amount', type: 'number'),
    RuleField(
      key: 'stage',
      label: 'Stage',
      type: 'choice',
      choices: [
        RuleChoice(value: 's-prop', label: 'Proposal', group: 'Sales'),
        RuleChoice(value: 's-won', label: 'Won', group: 'Sales'),
      ],
    ),
    RuleField(key: 'close_date', label: 'Close date', type: 'date'),
    RuleField(key: 'assigned_to', label: 'Assigned to', type: 'people'),
  ],
  parent: RuleParent(key: 'account', label: 'Account'),
);

AutomationCatalogue _catalogue({int maxConditions = 20}) => AutomationCatalogue(
  objects: const [_lead, _deal],
  operators: const {
    'text': ['eq', 'neq', 'contains', 'not_contains', 'empty', 'not_empty'],
    'number': ['eq', 'neq', 'gt', 'lt', 'empty', 'not_empty'],
    'choice': ['eq', 'neq', 'in', 'not_in', 'empty', 'not_empty'],
    'date': ['eq', 'neq', 'gt', 'lt', 'empty', 'not_empty'],
    'people': ['eq', 'includes', 'excludes', 'empty', 'not_empty'],
  },
  updateOnlyOperators: const ['was', 'was_not'],
  actions: const ['set_field', 'assign', 'create_task', 'notify', 'webhook'],
  people: const [RulePerson(id: 'p-asha', name: 'Asha')],
  maxConditions: maxConditions,
);

AutomationRule _rule({
  TriggerDraft? trigger,
  List<ConditionDraft>? conditions,
}) => AutomationRule(
  id: _id,
  name: 'Deal won: onboarding',
  objectKey: 'deal',
  trigger:
      trigger ?? TriggerDraft(event: 'updated', field: 'stage', to: 's-won'),
  conditions:
      conditions ?? [ConditionDraft(field: 'amount', op: 'gt', value: 0)],
  actions: [
    ActionDraft(
      type: 'notify',
      values: {
        'to': ['record_assignees'],
        'people': <String>[],
        'message': 'Kick off',
      },
    ),
  ],
);

AutomationRuleRow _row(String status) => AutomationRuleRow(
  id: _id,
  name: 'Deal won: onboarding',
  objectKey: 'deal',
  trigger: TriggerDraft(),
  status: status,
);

typedef _Call = ({String verb, String? id, Map<String, dynamic> body});

RuleWrite _accept(String verb, String? id, Map<String, dynamic> body) {
  final rule = AutomationRule.fromJson({
    'object_key': 'deal',
    ...body,
    'id': id ?? _newId,
  });
  _h.rules[rule.id] = rule;
  return (rule: rule, errors: null);
}

class _FakeApi extends AutomationApi {
  final List<_Call> calls = [];
  RuleWrite Function(String verb, String? id, Map<String, dynamic> body)
  answer = _accept;

  /// While set, a write waits for it, so a test can act mid-request.
  Completer<void>? hold;

  @override
  Future<RuleWrite> create(Map<String, dynamic> body) async {
    calls.add((verb: 'create', id: null, body: body));
    await hold?.future;
    return answer('create', null, body);
  }

  @override
  Future<RuleWrite> update(String id, Map<String, dynamic> body) async {
    calls.add((verb: 'update', id: id, body: body));
    await hold?.future;
    return answer('update', id, body);
  }
}

class _FakeRules extends AutomationRulesNotifier {
  _FakeRules(this.rows);

  final List<AutomationRuleRow> rows;

  @override
  Future<AutomationRulesAnswer> build() async {
    _h.rulesBuilds++;
    return AutomationRulesAnswer(rules: rows);
  }
}

class _Harness {
  int catalogueBuilds = 0;
  int rulesBuilds = 0;
  final Map<String, int> ruleFetches = {};
  final Map<String, AutomationRule> rules = {};
  final _FakeApi api = _FakeApi();
}

late _Harness _h;

Future<GoRouter> _open(
  WidgetTester tester,
  String path, {
  bool admin = true,
  Future<AutomationCatalogue> Function()? catalogue,
  AutomationRule? rule,
  List<AutomationRuleRow> rows = const [],
  bool settle = true,
}) async {
  _h = _Harness();
  _h.rules[_id] = rule ?? _rule();
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
          key: ValueKey('automation-rule-${state.pathParameters['ruleId']}'),
          ruleId: state.pathParameters['ruleId'],
        ),
      ),
    ],
  );
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        isOrgAdminProvider.overrideWithValue(admin),
        automationCatalogueProvider.overrideWith((ref) {
          _h.catalogueBuilds++;
          return (catalogue ?? () async => _catalogue())();
        }),
        automationRulesProvider.overrideWith(() => _FakeRules(rows)),
        automationRuleProvider.overrideWith((ref, id) async {
          _h.ruleFetches[id] = (_h.ruleFetches[id] ?? 0) + 1;
          final found = _h.rules[id];
          if (found == null) throw Exception('No such automation rule.');
          return found;
        }),
        automationApiProvider.overrideWithValue(_h.api),
      ],
      child: MaterialApp.router(theme: AppTheme.light, routerConfig: router),
    ),
  );
  await tester.pumpAndSettle();
  router.push(path);
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
  }
  return router;
}

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

Future<void> _pressBack(WidgetTester tester) async {
  tester.state<NavigatorState>(find.byType(Navigator).last).maybePop();
  await tester.pumpAndSettle();
}

Future<void> _rename(WidgetTester tester, String name) async {
  await tester.enterText(find.widgetWithText(TextField, 'Name'), name);
  await tester.pump();
}

const _neutral =
    "This rule can't be switched on for this organization right now.";

void main() {
  testWidgets(
    'a new rule picks its object, then shows When, Only if and Then',
    (tester) async {
      await _open(tester, AppRoutes.settingsAutomationNew);
      expect(find.text('New rule'), findsOneWidget);
      expect(find.text('WHEN'), findsOneWidget);
      expect(find.text('ONLY IF'), findsOneWidget);
      expect(find.text('THEN'), findsOneWidget);
      expect(find.text('Lead created'), findsOneWidget);

      await _choose(tester, 'Object', 'Deal');
      expect(find.text('Deal created'), findsOneWidget);

      await _tap(tester, find.text('Add condition'));
      await _choose(tester, 'Field', 'Amount');
      await _choose(tester, 'Operator', 'is more than');
      await tester.enterText(find.widgetWithText(TextFormField, 'Value'), '5');
      await _tap(tester, find.text('Done'));
      expect(find.text('Amount is more than 5'), findsOneWidget);

      // Another object takes the deal's conditions with it.
      await _choose(tester, 'Object', 'Lead');
      expect(find.text('Lead created'), findsOneWidget);
      expect(find.text('Amount is more than 5'), findsNothing);
      expect(find.text('Save'), findsOneWidget);
      expect(find.text('Save and switch on'), findsOneWidget);
    },
  );

  testWidgets('with no list row, the status comes from the rule itself', (
    tester,
  ) async {
    AutomationRule saved({bool on = false, String paused = ''}) =>
        AutomationRule(
          id: _id,
          name: 'Deal won: onboarding',
          objectKey: 'deal',
          trigger: TriggerDraft(event: 'created'),
          isActive: on,
          pausedReason: paused,
        );

    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rule: saved(paused: 'Asha left the organization.'),
    );
    expect(find.text('Paused'), findsOneWidget);
    expect(find.text('Save and take over'), findsOneWidget);

    await _open(tester, AppRoutes.settingsAutomationRule(_id), rule: saved());
    expect(find.text('Off'), findsOneWidget);
    expect(find.text('Save and switch on'), findsOneWidget);

    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rule: saved(on: true),
    );
    expect(find.text('On'), findsOneWidget);
    expect(find.text('Save and switch on'), findsNothing);
    expect(find.text('Save and take over'), findsNothing);
  });

  testWidgets('an existing rule shows its object as text, not a picker', (
    tester,
  ) async {
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rows: [_row('on')],
    );
    expect(find.text('Deal won: onboarding'), findsWidgets);
    expect(find.text('Deal updated: Stage changes to Won'), findsOneWidget);
    expect(find.text('Object'), findsNothing);
    expect(
      find.byWidgetPredicate((w) => w is DropdownButtonFormField),
      findsNothing,
    );
    expect(find.text('Amount is more than 0'), findsOneWidget);
    expect(find.text('1. Notify its assignees'), findsOneWidget);
  });

  testWidgets(
    'the trigger sheet offers any field or one field, and a changes-to value',
    (tester) async {
      await _open(tester, AppRoutes.settingsAutomationNew);
      await _choose(tester, 'Object', 'Deal');
      await _tap(tester, find.text('Deal created'));
      expect(find.text('is created'), findsOneWidget);
      await _tap(tester, find.text('is updated'));

      await _openDropdown(tester, 'Field');
      expect(find.text('Any field'), findsWidgets);
      expect(find.text('Amount'), findsWidgets);
      expect(find.text('Assigned to'), findsNothing);
      await tester.tap(find.text('Stage').last);
      await tester.pumpAndSettle();

      await _tap(tester, find.text('Only when it changes to'));
      await _choose(tester, 'Value', 'Sales: Won');
      expect(
        find.text(
          'Runs once, when the stage moves into Won; '
          'later edits do not run it again.',
        ),
        findsOneWidget,
      );
      await _tap(tester, find.text('Done'));
      expect(find.text('Deal updated: Stage changes to Won'), findsOneWidget);

      // Another field drops the value chosen for the first.
      await _tap(tester, find.text('Deal updated: Stage changes to Won'));
      await _choose(tester, 'Field', 'Amount');
      expect(find.textContaining('Runs once'), findsNothing);
      await _tap(tester, find.text('Done'));
      expect(find.text('Deal updated: Amount changes'), findsOneWidget);

      await _tap(tester, find.text('Save'));
      expect(_h.api.calls.single.body['trigger'], {
        'event': 'updated',
        'field': 'amount',
      });
    },
  );

  testWidgets('the condition sheet offers was only on an updated trigger', (
    tester,
  ) async {
    await _open(tester, AppRoutes.settingsAutomationNew);
    await _choose(tester, 'Object', 'Deal');
    await _tap(tester, find.text('Add condition'));
    expect(find.text('Add condition'), findsWidgets);
    await _choose(tester, 'Field', 'Amount');
    await _openDropdown(tester, 'Operator');
    expect(find.text('is more than'), findsWidgets);
    expect(find.text('was'), findsNothing);
    await tester.tap(find.text('is more than').last);
    await tester.pumpAndSettle();
    await _tap(tester, find.text('Cancel'));
    expect(find.textContaining('Amount is'), findsNothing);

    await _tap(tester, find.text('Deal created'));
    await _tap(tester, find.text('is updated'));
    await _tap(tester, find.text('Done'));
    await _tap(tester, find.text('Add condition'));
    await _choose(tester, 'Field', 'Amount');
    await _openDropdown(tester, 'Operator');
    expect(find.text('was'), findsWidgets);
    expect(find.text('was not'), findsWidgets);
    await tester.tap(find.text('was').last);
    await tester.pumpAndSettle();
    await tester.enterText(find.widgetWithText(TextFormField, 'Value'), '5');
    await _tap(tester, find.text('Done'));
    expect(find.text('Amount was 5'), findsOneWidget);
  });

  testWidgets('a stored option the catalogue lost stays selected and marked', (
    tester,
  ) async {
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rows: [_row('off')],
      rule: _rule(
        trigger: TriggerDraft(event: 'updated', field: 'stage', to: 's-gone'),
        conditions: [
          ConditionDraft(field: 'stage', op: 'eq', value: 's-old'),
          ConditionDraft(field: 'assigned_to', op: 'includes', value: 'p-left'),
        ],
      ),
    );
    expect(find.text('Stage is s-old (no longer available)'), findsOneWidget);
    expect(
      find.text('Assigned to includes Someone no longer active'),
      findsOneWidget,
    );

    await _tap(tester, find.text('Stage is s-old (no longer available)'));
    expect(find.text('s-old (no longer available)'), findsOneWidget);
    await _tap(tester, find.text('Done'));

    await _tap(
      tester,
      find.text('Assigned to includes Someone no longer active'),
    );
    expect(find.text('Someone no longer active'), findsOneWidget);
    await _tap(tester, find.text('Done'));

    await _tap(
      tester,
      find.text('Deal updated: Stage changes to s-gone (no longer available)'),
    );
    expect(find.text('s-gone (no longer available)'), findsOneWidget);
    await _tap(tester, find.text('Done'));

    await _tap(tester, find.text('Save'));
    final body = _h.api.calls.single.body;
    expect(body['trigger'], {
      'event': 'updated',
      'field': 'stage',
      'to': 's-gone',
    });
    expect(body['conditions'], [
      {'field': 'stage', 'op': 'eq', 'value': 's-old'},
      {'field': 'assigned_to', 'op': 'includes', 'value': 'p-left'},
    ]);
  });

  testWidgets(
    'Save sends the draft, Save and switch on adds is_active, and paused reads Save and take over',
    (tester) async {
      await _open(
        tester,
        AppRoutes.settingsAutomationRule(_id),
        rows: [_row('off')],
      );
      expect(find.text('Save and switch on'), findsOneWidget);
      await _rename(tester, 'Deal won: kick-off');
      await _tap(tester, find.text('Any of these'));
      await _tap(tester, find.text('Save'));
      var call = _h.api.calls.last;
      expect(call.verb, 'update');
      expect(call.id, _id);
      expect(call.body, {
        'name': 'Deal won: kick-off',
        'match': 'any',
        'trigger': {'event': 'updated', 'field': 'stage', 'to': 's-won'},
        'conditions': [
          {'field': 'amount', 'op': 'gt', 'value': 0},
        ],
        'actions': [
          {
            'type': 'notify',
            'to': ['record_assignees'],
            'people': <String>[],
            'message': 'Kick off',
          },
        ],
      });
      expect(find.text('Saved.'), findsOneWidget);
      expect(_h.rulesBuilds, 2);
      expect(_h.ruleFetches[_id], 2);

      await _tap(tester, find.text('Save and switch on'));
      expect(_h.api.calls.last.body['is_active'], isTrue);

      await _open(
        tester,
        AppRoutes.settingsAutomationRule(_id),
        rows: [_row('paused')],
      );
      expect(find.text('Save and switch on'), findsNothing);
      await _tap(tester, find.text('Save and take over'));
      expect(_h.api.calls.single.body['is_active'], isTrue);

      for (final status in ['on', 'over_limit', 'needs_attention']) {
        await _open(
          tester,
          AppRoutes.settingsAutomationRule(_id),
          rows: [_row(status)],
        );
        expect(find.text('Save'), findsOneWidget, reason: status);
        expect(find.text('Save and switch on'), findsNothing, reason: status);
        expect(find.text('Save and take over'), findsNothing, reason: status);
      }

      // A new rule is created, and its route gives way to the saved rule's.
      var router = await _open(tester, AppRoutes.settingsAutomationNew);
      await _rename(tester, 'New lead: welcome');
      await _tap(tester, find.text('Save'));
      call = _h.api.calls.single;
      expect(call.verb, 'create');
      expect(call.body['object_key'], 'lead');
      expect(call.body['name'], 'New lead: welcome');
      expect(call.body.containsKey('is_active'), isFalse);
      expect(
        router.routerDelegate.currentConfiguration.last.matchedLocation,
        AppRoutes.settingsAutomationRule(_newId),
      );
      expect(find.text('New rule'), findsNothing);
      expect(find.text('New lead: welcome'), findsWidgets);
      router.pop();
      await tester.pumpAndSettle();
      expect(find.text('the list'), findsOneWidget);

      router = await _open(tester, AppRoutes.settingsAutomationNew);
      await _tap(tester, find.text('Save and switch on'));
      expect(_h.api.calls.single.body['is_active'], isTrue);
      expect(_h.api.calls.single.body['object_key'], 'lead');
    },
  );

  testWidgets('a 400 marks the condition row and keeps the draft', (
    tester,
  ) async {
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rows: [_row('off')],
    );
    _h.api.answer = (_, _, _) => (
      rule: null,
      errors: RuleErrors.fromResponse(
        const ApiResponse<Map<String, dynamic>>(
          success: false,
          statusCode: 400,
          data: {
            'errors': {
              'conditions[0].value': ['Enter a number.'],
              'is_active': ['Must be a valid boolean.'],
            },
          },
        ),
      ),
    );
    await _rename(tester, 'Renamed');
    await _tap(tester, find.text('Save'));

    expect(find.text('Enter a number.'), findsOneWidget);
    expect(find.text('Must be a valid boolean.'), findsOneWidget);
    expect(find.text('Renamed'), findsOneWidget);
    expect(find.text('Amount is more than 0'), findsOneWidget);
    expect(find.text('Saved.'), findsNothing);
    expect(_h.rulesBuilds, 1);
    final card = tester.getRect(find.text('Amount is more than 0'));
    final error = tester.getRect(find.text('Enter a number.'));
    final add = tester.getRect(find.text('Add condition'));
    expect(error.top, greaterThan(card.bottom));
    expect(error.bottom, lessThan(add.top));

    _h.api.answer = _accept;
    await _tap(tester, find.text('Save'));
    expect(_h.api.calls.last.body['name'], 'Renamed');
    expect(find.text('Enter a number.'), findsNothing);
  });

  testWidgets('a plan_limit 403 shows the neutral sentence', (tester) async {
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rows: [_row('off')],
    );
    _h.api.answer = (_, _, _) => (
      rule: null,
      errors: RuleErrors.fromResponse(
        const ApiResponse<Map<String, dynamic>>(
          success: false,
          statusCode: 403,
          message: "Over this install's limit",
          data: {'detail': "Over this install's limit", 'code': 'plan_limit'},
        ),
      ),
    );
    await _rename(tester, 'Kept');
    await _tap(tester, find.text('Save and switch on'));
    expect(_h.api.calls.single.body['is_active'], isTrue);
    expect(find.text(_neutral), findsOneWidget);
    expect(find.textContaining("Over this install's limit"), findsNothing);
    expect(find.text('Kept'), findsOneWidget);
    expect(find.text('Save and switch on'), findsOneWidget);
  });

  testWidgets('leaving with unsaved changes asks first', (tester) async {
    final router = await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rows: [_row('on')],
    );
    await _pressBack(tester);
    expect(find.text('Discard changes?'), findsNothing);
    expect(find.text('the list'), findsOneWidget);

    router.push(AppRoutes.settingsAutomationRule(_id));
    await tester.pumpAndSettle();
    await _tap(tester, find.byTooltip('Remove condition 1'));
    await _pressBack(tester);
    expect(find.text('Discard changes?'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(find.text('the list'), findsNothing);

    await tester.tap(find.byTooltip('Back'));
    await tester.pumpAndSettle();
    expect(find.text('Discard changes?'), findsOneWidget);
    await tester.tap(find.text('Discard'));
    await tester.pumpAndSettle();
    expect(find.text('the list'), findsOneWidget);
  });

  testWidgets('add condition stops at the catalogue limit', (tester) async {
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      catalogue: () async => _catalogue(maxConditions: 2),
      rows: [_row('off')],
      rule: _rule(
        conditions: [
          ConditionDraft(field: 'amount', op: 'gt', value: 0),
          ConditionDraft(field: 'name', op: 'contains', value: 'Acme'),
        ],
      ),
    );
    expect(_button(tester, 'Add condition').onPressed, isNull);
    expect(find.text('A rule can have at most 2 conditions.'), findsOneWidget);

    await _tap(tester, find.byTooltip('Remove condition 2'));
    expect(find.text('Name contains Acme'), findsNothing);
    expect(_button(tester, 'Add condition').onPressed, isNotNull);
    expect(find.text('A rule can have at most 2 conditions.'), findsNothing);
  });

  testWidgets('a list value opens the multi-select sheet', (tester) async {
    await _open(tester, AppRoutes.settingsAutomationNew);
    await _choose(tester, 'Object', 'Deal');
    await _tap(tester, find.text('Add condition'));
    await _choose(tester, 'Field', 'Stage');
    await _choose(tester, 'Operator', 'is any of');
    await _tap(tester, find.text('Choose'));
    expect(find.text('Sales: Proposal'), findsOneWidget);
    await _tap(tester, find.text('Sales: Won'));
    await _tap(tester, find.text('Done').last);
    expect(find.text('Sales: Won'), findsOneWidget);
    await _tap(tester, find.text('Done'));
    expect(find.text('Stage is any of Won'), findsOneWidget);
  });

  testWidgets(
    'a condition value resets when its field or its kind of value changes',
    (tester) async {
      await _open(tester, AppRoutes.settingsAutomationNew);
      await _choose(tester, 'Object', 'Deal');
      await _tap(tester, find.text('Add condition'));
      await _choose(tester, 'Field', 'Stage');
      await _choose(tester, 'Value', 'Sales: Won');

      // Same kind of value: it stays.
      await _choose(tester, 'Operator', 'is not');
      expect(find.text('Sales: Won'), findsOneWidget);

      // A list instead of one option: it goes.
      await _choose(tester, 'Operator', 'is any of');
      expect(find.text('Choose'), findsOneWidget);
      expect(find.text('Sales: Won'), findsNothing);
      await _tap(tester, find.text('Choose'));
      await _tap(tester, find.text('Sales: Won'));
      await _tap(tester, find.text('Done').last);
      await _tap(tester, find.text('Done'));
      expect(find.text('Stage is any of Won'), findsOneWidget);

      // Another field: the operator and the value start over.
      await _tap(tester, find.text('Stage is any of Won'));
      await _choose(tester, 'Field', 'Amount');
      expect(find.text('is'), findsOneWidget);
      expect(
        tester
            .widget<TextField>(
              find.descendant(
                of: find.widgetWithText(TextFormField, 'Value'),
                matching: find.byType(TextField),
              ),
            )
            .controller
            ?.text,
        '',
      );
      await _tap(tester, find.text('Done'));
      expect(find.text('Amount is'), findsOneWidget);

      await _tap(tester, find.text('Save'));
      expect(_h.api.calls.single.body['conditions'], [
        {'field': 'amount', 'op': 'eq', 'value': null},
      ]);
    },
  );

  testWidgets('a member sees the notice and no automation provider is read', (
    tester,
  ) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id), admin: false);
    expect(
      find.text('Only an organization admin can see automation rules.'),
      findsOneWidget,
    );
    expect(_h.catalogueBuilds, 0);
    expect(_h.rulesBuilds, 0);
    expect(_h.ruleFetches, isEmpty);
    expect(find.text('Save'), findsNothing);
  });

  testWidgets('shows the loading state, then the error state with Try again', (
    tester,
  ) async {
    final never = Completer<AutomationCatalogue>();
    await _open(
      tester,
      AppRoutes.settingsAutomationNew,
      catalogue: () => never.future,
      settle: false,
    );
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('WHEN'), findsNothing);

    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      catalogue: () async => throw Exception('offline'),
    );
    expect(find.text('Could not load the rule'), findsOneWidget);
    final before = _h.catalogueBuilds;
    await _tap(tester, find.text('Try again'));
    expect(_h.catalogueBuilds, before + 1);

    // A new rule has no rule to load: the editor itself is what failed.
    await _open(
      tester,
      AppRoutes.settingsAutomationNew,
      catalogue: () async => throw Exception('offline'),
    );
    expect(find.text('Could not load the rule editor.'), findsOneWidget);
    expect(find.text('Could not load the rule'), findsNothing);
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('a stored date before 2000 opens the picker and saves as it is', (
    tester,
  ) async {
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rows: [_row('off')],
      rule: _rule(
        conditions: [
          ConditionDraft(field: 'close_date', op: 'gt', value: '1990-01-01'),
        ],
      ),
    );
    await _tap(tester, find.text('Close date is after 1990-01-01'));
    await _tap(tester, find.text('1990-01-01'));
    expect(tester.takeException(), isNull);
    expect(find.byType(DatePickerDialog), findsOneWidget);
    await tester.tap(find.text('Cancel').last);
    await tester.pumpAndSettle();
    expect(find.byType(DatePickerDialog), findsNothing);
    await _tap(tester, find.text('Done'));
    await _tap(tester, find.text('Save'));
    expect(_h.api.calls.single.body['conditions'], [
      {'field': 'close_date', 'op': 'gt', 'value': '1990-01-01'},
    ]);
  });

  testWidgets('a save in flight blocks edits to the form', (tester) async {
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rows: [_row('off')],
    );
    _h.api.hold = Completer<void>();
    await _tap(tester, find.text('Save'));
    expect(_h.api.calls, hasLength(1));

    await tester.tap(find.text('Amount is more than 0'), warnIfMissed: false);
    await tester.pumpAndSettle();
    expect(find.text('Edit condition'), findsNothing);
    await tester.tap(find.byTooltip('Remove condition 1'), warnIfMissed: false);
    await tester.pumpAndSettle();
    expect(find.text('Amount is more than 0'), findsOneWidget);
    expect(
      tester.widget<TextField>(find.widgetWithText(TextField, 'Name')).readOnly,
      isTrue,
    );

    _h.api.hold!.complete();
    await tester.pumpAndSettle();
    expect(find.text('Saved.'), findsOneWidget);
    await _tap(tester, find.text('Amount is more than 0'));
    expect(find.text('Edit condition'), findsOneWidget);
  });

  testWidgets('a stored field the catalogue lost stays selected and says so', (
    tester,
  ) async {
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rows: [_row('off')],
      rule: _rule(
        conditions: [ConditionDraft(field: 'old_field', op: 'eq', value: 'x')],
      ),
    );
    await _tap(tester, find.text('A field that is no longer available is x'));
    expect(find.text('old_field (no longer available)'), findsOneWidget);
    expect(
      find.text('This field is no longer available. Choose another.'),
      findsOneWidget,
    );
    await _tap(tester, find.text('Done'));
    await _tap(tester, find.text('Save'));
    expect(_h.api.calls.single.body['conditions'], [
      {'field': 'old_field', 'op': 'eq', 'value': 'x'},
    ]);
  });

  testWidgets(
    'another object on a new rule keeps the event and drops the trigger field',
    (tester) async {
      await _open(tester, AppRoutes.settingsAutomationNew);
      await _choose(tester, 'Object', 'Deal');
      await _tap(tester, find.text('Deal created'));
      await _tap(tester, find.text('is updated'));
      await _choose(tester, 'Field', 'Stage');
      await _tap(tester, find.text('Done'));
      expect(find.text('Deal updated: Stage changes'), findsOneWidget);

      await _choose(tester, 'Object', 'Lead');
      expect(find.text('Lead updated'), findsOneWidget);
      await _tap(tester, find.text('Save'));
      expect(_h.api.calls.single.body['trigger'], {'event': 'updated'});
    },
  );

  testWidgets('choosing Any field drops field from the saved trigger', (
    tester,
  ) async {
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rows: [_row('off')],
    );
    await _tap(tester, find.text('Deal updated: Stage changes to Won'));
    await _choose(tester, 'Field', 'Any field');
    expect(find.text('Only when it changes to'), findsNothing);
    await _tap(tester, find.text('Done'));
    expect(find.text('Deal updated'), findsOneWidget);
    await _tap(tester, find.text('Save'));
    expect(_h.api.calls.single.body['trigger'], {'event': 'updated'});
  });
}
