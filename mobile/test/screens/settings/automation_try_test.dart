import 'dart:async';

import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/automation.dart';
import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/settings/automation/automation_rule_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

const _id = '3f2b8c1e-7a4d-4e2b-9c1a-5d6e7f8a9b0c';

const _deal = AutomationObject(
  key: 'deal',
  label: 'Deal',
  labelPlural: 'Deals',
  fields: [RuleField(key: 'name', label: 'Name')],
);

AutomationRule _rule({bool active = true}) => AutomationRule(
  id: _id,
  name: 'Deal won',
  objectKey: 'deal',
  trigger: TriggerDraft(event: 'created'),
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
  isActive: active,
  owner: active ? const RulePerson(id: 'p1', name: 'Asha') : null,
);

AutomationRuleRow _row(String status) => AutomationRuleRow(
  id: _id,
  name: 'Deal won',
  objectKey: 'deal',
  trigger: TriggerDraft(event: 'created'),
  status: status,
);

class _FakeApi extends AutomationApi {
  final List<String> calls = [];
  Completer<void>? hold;
  ({List<RunStep> steps, String? error}) tried = (steps: [], error: null);
  String? deleteError;

  @override
  Future<({List<RunStep> steps, String? error})> tryRule(
    String id,
    String recordId,
  ) async {
    calls.add('try:$id:$recordId');
    await hold?.future;
    return tried;
  }

  @override
  Future<RuleWrite> update(String id, Map<String, dynamic> body) async {
    calls.add('update:$id');
    _current = AutomationRule.fromJson({
      'object_key': 'deal',
      ...body,
      'id': id,
      'is_active': _current.isActive,
    });
    return (rule: _current, errors: null);
  }

  @override
  Future<String?> switchOff(String id) async {
    calls.add('off:$id');
    await hold?.future;
    _current = _rule(active: false);
    _status = 'off';
    return null;
  }

  @override
  Future<String?> delete(String id) async {
    calls.add('delete:$id');
    await hold?.future;
    return deleteError;
  }
}

class _FakeRules extends AutomationRulesNotifier {
  @override
  Future<AutomationRulesAnswer> build() async =>
      AutomationRulesAnswer(rules: [_row(_status)]);
}

late _FakeApi _api;
late AutomationRule _current;
String _status = 'on';

Future<void> _open(
  WidgetTester tester,
  String path, {
  AutomationRule? rule,
  String status = 'on',
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
        path: AppRoutes.settingsAutomationRunsDetail,
        builder: (_, _) => const Scaffold(body: Text('the runs')),
      ),
      GoRoute(
        path: AppRoutes.settingsAutomationRuleDetail,
        builder: (_, state) =>
            AutomationRuleScreen(ruleId: state.pathParameters['ruleId']),
      ),
    ],
  );
  _current = rule ?? _rule();
  _status = status;
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        isOrgAdminProvider.overrideWithValue(true),
        automationCatalogueProvider.overrideWith(
          (ref) async => const AutomationCatalogue(
            objects: [_deal],
            actions: ['notify'],
            people: [RulePerson(id: 'p1', name: 'Asha')],
          ),
        ),
        automationRulesProvider.overrideWith(() => _FakeRules()),
        automationRuleProvider.overrideWith((ref, id) async => _current),
        automationApiProvider.overrideWithValue(_api),
        linkTargetSearchProvider.overrideWith(
          (ref, arg) async => [
            const LinkedRecord(
              id: 'rec-1',
              object: 'deal',
              name: 'Acme <b>big</b> deal',
            ),
          ],
        ),
      ],
      child: MaterialApp.router(theme: AppTheme.light, routerConfig: router),
    ),
  );
  await tester.pumpAndSettle();
  router.push(path);
  await tester.pumpAndSettle();
}

Future<void> _tap(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
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

void main() {
  testWidgets('an owner with no name still reads as switched on', (
    tester,
  ) async {
    AutomationRule owned(String name) => AutomationRule(
      id: _id,
      name: 'Deal won',
      objectKey: 'deal',
      trigger: TriggerDraft(event: 'created'),
      isActive: true,
      owner: RulePerson(id: 'p1', name: name),
    );
    for (final name in ['', '   ']) {
      await _open(
        tester,
        AppRoutes.settingsAutomationRule(_id),
        rule: owned(name),
      );
      expect(find.text('Switched on'), findsOneWidget, reason: '"$name"');
      expect(find.textContaining('Switched on by'), findsNothing);
    }
    await _open(
      tester,
      AppRoutes.settingsAutomationRule(_id),
      rule: owned('  Asha  '),
    );
    expect(find.text('Switched on by Asha'), findsOneWidget);
  });

  testWidgets(
    'Try picks a record of the rule object and lists what each action would do',
    (tester) async {
      await _open(tester, AppRoutes.settingsAutomationRule(_id));
      expect(find.text('On'), findsOneWidget);
      expect(find.text('Switched on by Asha'), findsOneWidget);
      _api.tried = (
        steps: const [
          RunStep(action: 0, type: 'notify', status: 'planned', text: 'Notify'),
          RunStep(action: 1, type: 'x', status: 'skipped', text: 'Left out'),
          RunStep(action: 2, type: 'y', status: 'failed', text: 'Breaks'),
        ],
        error: null,
      );
      await _tap(tester, find.text('Try it on a record'));
      expect(find.text('Try it on a record'), findsWidgets);
      await _tap(tester, find.text('Acme <b>big</b> deal'));
      expect(_api.calls, ['try:$_id:rec-1']);
      expect(
        find.text('Tried on "Acme <b>big</b> deal". Nothing was changed.'),
        findsOneWidget,
      );
      expect(
        find.text(
          'The trigger and conditions are not checked: this is what the '
          'actions would do.',
        ),
        findsOneWidget,
      );
      expect(find.text('Notify'), findsOneWidget);
      expect(find.text('Skipped'), findsOneWidget);
      expect(find.text('Would fail'), findsOneWidget);
      final failed = tester.widget<Text>(find.text('Breaks'));
      expect(failed.style?.color, AppColors.danger600);
    },
  );

  testWidgets('a try the server refuses shows its message', (tester) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id));
    _api.tried = (
      steps: const [],
      error: 'That record does not exist, or you cannot open it.',
    );
    await _tap(tester, find.text('Try it on a record'));
    await _tap(tester, find.text('Acme <b>big</b> deal'));
    expect(
      find.text('That record does not exist, or you cannot open it.'),
      findsOneWidget,
    );
    expect(find.textContaining('Nothing was changed'), findsNothing);
  });

  testWidgets(
    'Try is disabled with Save first while the draft differs from the saved rule',
    (tester) async {
      await _open(tester, AppRoutes.settingsAutomationRule(_id));
      expect(_button(tester, 'Try it on a record').onPressed, isNotNull);
      expect(find.text('Save first: Try uses the saved rule.'), findsNothing);
      await tester.enterText(find.widgetWithText(TextField, 'Name'), 'Other');
      await tester.pump();
      await tester.ensureVisible(find.text('Try it on a record'));
      await tester.pumpAndSettle();
      expect(_button(tester, 'Try it on a record').onPressed, isNull);
      expect(find.text('Save first: Try uses the saved rule.'), findsOneWidget);
    },
  );

  testWidgets('a new rule shows the save-to-try hint instead', (tester) async {
    await _open(tester, AppRoutes.settingsAutomationNew);
    expect(find.text('Save the rule to try it on a record.'), findsOneWidget);
    expect(_button(tester, 'Try it on a record').onPressed, isNull);
    expect(find.text('Run history'), findsNothing);
    expect(find.text('Delete rule'), findsNothing);
    expect(find.text('Switch off'), findsNothing);
  });

  testWidgets(
    'Switch off shows only while the rule is on, and sends is_active false',
    (tester) async {
      await _open(tester, AppRoutes.settingsAutomationRule(_id));
      expect(find.text('Switch off'), findsOneWidget);
      expect(
        tester
            .getSize(
              find.ancestor(
                of: find.text('Switch off'),
                matching: find.byType(OutlinedButton),
              ),
            )
            .height,
        48,
      );
      await _tap(tester, find.text('Switch off'));
      expect(_api.calls, ['off:$_id']);
      expect(find.text('Switch off'), findsNothing);
      expect(find.text('Off'), findsOneWidget);

      await _open(
        tester,
        AppRoutes.settingsAutomationRule(_id),
        rule: _rule(active: false),
        status: 'off',
      );
      expect(find.text('Off'), findsOneWidget);
      expect(find.text('Switch off'), findsNothing);
    },
  );

  testWidgets('Run history opens the runs screen', (tester) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id));
    await _tap(tester, find.text('Run history'));
    expect(find.text('the runs'), findsOneWidget);
  });

  testWidgets('buttons are disabled while a request is in flight', (
    tester,
  ) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id));
    _api.hold = Completer<void>();
    await tester.ensureVisible(find.text('Switch off'));
    await tester.tap(find.text('Switch off'));
    await tester.pump();
    expect(_button(tester, 'Switch off').onPressed, isNull);
    expect(_button(tester, 'Delete rule').onPressed, isNull);
    expect(_button(tester, 'Try it on a record').onPressed, isNull);
    _api.hold!.complete();
    await tester.pumpAndSettle();
    expect(_button(tester, 'Delete rule').onPressed, isNotNull);
  });

  testWidgets('Delete asks first, then leaves the editor', (tester) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id));
    await _tap(tester, find.text('Delete rule'));
    expect(find.text('Delete this rule?'), findsOneWidget);
    expect(find.text('Its run history goes too.'), findsOneWidget);
    await _tap(tester, find.text('Keep it'));
    expect(_api.calls, isEmpty);
    expect(find.text('Deal won'), findsWidgets);

    await _tap(tester, find.text('Delete rule'));
    await _tap(tester, find.text('Delete permanently'));
    expect(_api.calls, ['delete:$_id']);
    expect(find.text('the list'), findsOneWidget);
  });

  testWidgets('a failed delete stays on the editor and says why', (
    tester,
  ) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id));
    _api.deleteError = 'Could not delete the rule.';
    await _tap(tester, find.text('Delete rule'));
    await _tap(tester, find.text('Delete permanently'));
    expect(find.text('Could not delete the rule.'), findsOneWidget);
    expect(find.text('the list'), findsNothing);
  });

  testWidgets('a step text holding markup shows as plain text', (tester) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id));
    _api.tried = (
      steps: const [
        RunStep(status: 'planned', text: '<script>x</script> **bold**'),
      ],
      error: null,
    );
    await _tap(tester, find.text('Try it on a record'));
    await _tap(tester, find.text('Acme <b>big</b> deal'));
    expect(find.text('<script>x</script> **bold**'), findsOneWidget);
  });

  testWidgets('Try re-enables after a successful save', (tester) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id));
    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'Other');
    await tester.pump();
    await tester.ensureVisible(find.text('Try it on a record'));
    await tester.pumpAndSettle();
    expect(_button(tester, 'Try it on a record').onPressed, isNull);
    await _tap(tester, find.text('Save'));
    expect(_api.calls, ['update:$_id']);
    expect(_button(tester, 'Try it on a record').onPressed, isNotNull);
    expect(find.text('Save first: Try uses the saved rule.'), findsNothing);
  });

  testWidgets('deleting with a dirty draft leaves without the discard prompt', (
    tester,
  ) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id));
    await tester.enterText(find.widgetWithText(TextField, 'Name'), 'Other');
    await tester.pump();
    await _tap(tester, find.text('Delete rule'));
    await _tap(tester, find.text('Delete permanently'));
    expect(find.text('Discard changes?'), findsNothing);
    expect(find.text('the list'), findsOneWidget);
  });

  testWidgets('back does nothing while a request is in flight', (tester) async {
    await _open(tester, AppRoutes.settingsAutomationRule(_id));
    _api.hold = Completer<void>();
    await tester.ensureVisible(find.text('Switch off'));
    await tester.tap(find.text('Switch off'));
    await tester.pump();
    tester.state<NavigatorState>(find.byType(Navigator).last).maybePop();
    await tester.pump();
    expect(find.text('the list'), findsNothing);
    _api.hold!.complete();
    await tester.pumpAndSettle();
  });
}
