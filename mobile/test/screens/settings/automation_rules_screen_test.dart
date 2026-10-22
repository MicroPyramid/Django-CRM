import 'dart:async';
import 'package:bottle_crm/data/models/custom_object.dart';

import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/automation.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/screens/settings/automation/automation_rules_screen.dart';
import 'package:bottle_crm/screens/settings/settings_hub_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _catalogue = AutomationCatalogue(
  objects: [
    AutomationObject(
      key: 'deal',
      label: 'Deal',
      labelPlural: 'Deals',
      fields: [
        RuleField(
          key: 'stage',
          label: 'Stage',
          type: 'choice',
          choices: [RuleChoice(value: 'won', label: 'Won')],
        ),
      ],
    ),
    AutomationObject(key: 'lead', label: 'Lead', labelPlural: 'Leads'),
    AutomationObject(key: 'ticket', label: 'Ticket', labelPlural: 'Tickets'),
  ],
);

AutomationRuleRow _row(
  String id,
  String name, {
  String object = 'lead',
  TriggerDraft? trigger,
  String status = 'on',
  String statusText = '',
  int runs = 0,
  int failed = 0,
}) => AutomationRuleRow(
  id: id,
  name: name,
  objectKey: object,
  trigger: trigger ?? TriggerDraft(),
  status: status,
  statusText: statusText,
  runs7d: runs,
  failures7d: failed,
);

class _FakeRules extends AutomationRulesNotifier {
  _FakeRules(this.answer);

  final Future<AutomationRulesAnswer> Function() answer;
  static final List<(String, String)> moves = [];
  static int builds = 0;
  static Completer<String?>? pending;
  static int refreshes = 0;

  @override
  Future<AutomationRulesAnswer> build() {
    builds++;
    return answer();
  }

  @override
  Future<void> refresh() async {
    refreshes++;
  }

  @override
  Future<String?> move(String id, String direction) {
    moves.add((id, direction));
    return pending?.future ?? Future.value(null);
  }
}

Future<void> _pump(
  WidgetTester tester, {
  bool admin = true,
  Future<AutomationRulesAnswer> Function()? rules,
  Future<AutomationCatalogue> Function()? catalogue,
  Widget home = const AutomationRulesScreen(),
  bool settle = true,
}) async {
  _FakeRules.moves.clear();
  _FakeRules.builds = 0;
  _FakeRules.refreshes = 0;
  _FakeRules.pending = null;
  _gate = null;
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        isOrgAdminProvider.overrideWithValue(admin),
        customObjectsProvider.overrideWith(_NoObjects.new),
        automationRulesProvider.overrideWith(
          () => _FakeRules(
            rules ?? () async => const AutomationRulesAnswer(rules: []),
          ),
        ),
        automationCatalogueProvider.overrideWith(
          (ref) => _gate?.future ?? (catalogue ?? () async => _catalogue)(),
        ),
      ],
      child: MaterialApp(home: home),
    ),
  );
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    await tester.pump();
  }
}

Completer<AutomationCatalogue>? _gate;

class _NoObjects extends CustomObjectsNotifier {
  @override
  Future<CustomObjectsAnswer?> build() async => null;
}

void main() {
  testWidgets('admins see the Automation row and members do not', (
    tester,
  ) async {
    await _pump(tester, home: const SettingsHubScreen());
    await tester.scrollUntilVisible(
      find.text('Automation'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Automation'), findsOneWidget);

    await _pump(tester, admin: false, home: const SettingsHubScreen());
    await tester.scrollUntilVisible(
      find.text('Help center'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Automation'), findsNothing);
    expect(_FakeRules.builds, 0);
  });

  testWidgets('the hub hides Automation from admins where the API has none', (
    tester,
  ) async {
    await _pump(
      tester,
      home: const SettingsHubScreen(),
      rules: () async => throw const AutomationNotOffered(),
    );
    await tester.scrollUntilVisible(
      find.text('Help center'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Automation'), findsNothing);
  });

  testWidgets(
    'the hub keeps Automation when the rules fail for another reason',
    (tester) async {
      await _pump(
        tester,
        home: const SettingsHubScreen(),
        rules: () async => throw Exception('boom'),
      );
      await tester.scrollUntilVisible(
        find.text('Automation'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      expect(find.text('Automation'), findsOneWidget);
    },
  );

  testWidgets(
    'the screen says rules are not available where the API has none',
    (tester) async {
      await _pump(
        tester,
        rules: () async => throw const AutomationNotOffered(),
      );
      expect(
        find.text('Automation rules are not available here.'),
        findsOneWidget,
      );
      expect(find.text('Try again'), findsNothing);
    },
  );

  testWidgets(
    'a member who opens the screen sees the notice and no request is made',
    (tester) async {
      await _pump(tester, admin: false);
      expect(
        find.text('Only an organization admin can see automation rules.'),
        findsOneWidget,
      );
      expect(_FakeRules.builds, 0);
      expect(find.byTooltip('New rule'), findsNothing);
    },
  );

  testWidgets('lists each rule with its object, trigger, runs and status', (
    tester,
  ) async {
    await _pump(
      tester,
      rules: () async => AutomationRulesAnswer(
        rules: [
          _row(
            'a',
            'Deal won: onboarding',
            object: 'deal',
            trigger: TriggerDraft(event: 'updated', field: 'stage', to: 'won'),
            runs: 14,
          ),
          _row('b', 'New lead: rotate owners', runs: 52, failed: 1),
          _row('c', 'Quiet one', object: 'ticket', status: 'off'),
        ],
      ),
    );
    expect(find.text('Deal won: onboarding'), findsOneWidget);
    expect(find.text('Deal, Stage changes to Won'), findsOneWidget);
    expect(find.text('14 runs'), findsOneWidget);
    expect(find.text('Lead, Created'), findsOneWidget);
    expect(find.text('52 runs, 1 failed'), findsOneWidget);
    expect(find.text('No runs'), findsOneWidget);
    expect(find.text('On'), findsNWidgets(2));
    expect(find.text('Off'), findsOneWidget);
    expect(find.byTooltip('New rule'), findsOneWidget);
  });

  testWidgets('falls back to the object key when the catalogue fails', (
    tester,
  ) async {
    await _pump(
      tester,
      catalogue: () async => throw Exception('no catalogue'),
      rules: () async =>
          AutomationRulesAnswer(rules: [_row('a', 'Rule A', object: 'deal')]),
    );
    expect(find.text('Rule A'), findsOneWidget);
    expect(find.textContaining('deal'), findsOneWidget);
    expect(find.text('Try again'), findsNothing);
  });

  testWidgets('shows a note for each paused rule saying how to take it over', (
    tester,
  ) async {
    await _pump(
      tester,
      rules: () async => AutomationRulesAnswer(
        rules: [
          _row(
            'a',
            'Ticket follow-up',
            object: 'ticket',
            status: 'paused',
            statusText: 'Priya is no longer an admin.',
          ),
          _row('b', 'Other', status: 'paused', statusText: 'Paused too.'),
          _row('c', 'Fine'),
        ],
      ),
    );
    expect(
      find.text(
        '"Ticket follow-up": Priya is no longer an admin. '
        'Switch it on again to take it over.',
      ),
      findsOneWidget,
    );
    expect(
      find.text('"Other": Paused too. Switch it on again to take it over.'),
      findsOneWidget,
    );
    expect(find.textContaining('"Fine"'), findsNothing);
    expect(find.textContaining('Priya is no longer an admin.'), findsOneWidget);
    expect(find.textContaining('Paused too.'), findsOneWidget);
  });

  testWidgets(
    'shows Not running with the neutral sentence for an over_limit rule, and no summary line',
    (tester) async {
      await _pump(
        tester,
        rules: () async => AutomationRulesAnswer(
          summary: '5 of 2 active rules',
          rules: [_row('a', 'Over', status: 'over_limit')],
        ),
      );
      expect(find.text('Not running'), findsOneWidget);
      // The paused tone, as on the web: a rule that does not run either way.
      expect(
        tester.widget<Text>(find.text('Not running')).style?.color,
        AppColors.warning600,
      );
      expect(
        find.text('This rule is not running for this organization right now.'),
        findsOneWidget,
      );
      expect(find.textContaining('5 of 2 active rules'), findsNothing);
    },
  );

  testWidgets('moves a rule up and disables up on the first rule', (
    tester,
  ) async {
    await _pump(
      tester,
      rules: () async => AutomationRulesAnswer(
        rules: [_row('a', 'First'), _row('b', 'Second')],
      ),
    );
    Finder button(String tip) => find.ancestor(
      of: find.byTooltip(tip),
      matching: find.byType(IconButton),
    );
    final ups = button('Move up');
    final downs = button('Move down');
    expect(ups, findsNWidgets(2));
    expect(tester.widget<IconButton>(ups.at(0)).onPressed, isNull);
    expect(tester.widget<IconButton>(downs.at(1)).onPressed, isNull);

    _FakeRules.pending = Completer<String?>();
    await tester.tap(ups.at(1));
    await tester.pump();
    expect(_FakeRules.moves, [('b', 'up')]);
    expect(tester.widget<IconButton>(ups.at(1)).onPressed, isNull);
    expect(tester.widget<IconButton>(downs.at(0)).onPressed, isNull);

    _FakeRules.pending!.complete('Could not change the order.');
    await tester.pump();
    await tester.pump();
    expect(find.text('Could not change the order.'), findsOneWidget);
    expect(tester.widget<IconButton>(ups.at(1)).onPressed, isNotNull);
  });

  testWidgets('shows a rule name holding markup as plain text', (tester) async {
    const name = '<b>Bold</b><script>alert(1)</script>';
    await _pump(
      tester,
      rules: () async => AutomationRulesAnswer(rules: [_row('a', name)]),
    );
    expect(find.text(name), findsOneWidget);
  });

  testWidgets('shows the empty state and the error state with Try again', (
    tester,
  ) async {
    await _pump(tester);
    expect(find.text('No rules yet'), findsOneWidget);
    expect(
      find.text(
        'A rule does something when a record is created or changes: assign '
        'it, create a task, notify people, or set a field.',
      ),
      findsOneWidget,
    );

    await _pump(tester, rules: () async => throw Exception('boom'));
    expect(find.text('Could not load automation rules'), findsOneWidget);
    await tester.tap(find.text('Try again'));
    await tester.pump();
    expect(_FakeRules.refreshes, 1);
  });

  testWidgets('a paused rule with no text falls back to its status label', (
    tester,
  ) async {
    await _pump(
      tester,
      rules: () async =>
          AutomationRulesAnswer(rules: [_row('a', 'Quiet', status: 'paused')]),
    );
    expect(
      find.text('"Quiet": Paused. Switch it on again to take it over.'),
      findsOneWidget,
    );
  });

  testWidgets('shows no label from the old catalogue while it reloads', (
    tester,
  ) async {
    await _pump(
      tester,
      rules: () async =>
          AutomationRulesAnswer(rules: [_row('a', 'Rule A', object: 'deal')]),
    );
    expect(find.text('Deal, Created'), findsOneWidget);

    final pending = Completer<AutomationCatalogue>();
    _gate = pending;
    ProviderScope.containerOf(
      tester.element(find.byType(AutomationRulesScreen)),
    ).invalidate(automationCatalogueProvider);
    await tester.pump();
    expect(find.text('Deal, Created'), findsNothing);
    expect(find.text('deal, Created'), findsOneWidget);
    pending.complete(_catalogue);
    await tester.pumpAndSettle();
    expect(find.text('Deal, Created'), findsOneWidget);
  });

  testWidgets('shows the loading state while the rules load', (tester) async {
    final never = Completer<AutomationRulesAnswer>();
    await _pump(tester, rules: () => never.future, settle: false);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('No rules yet'), findsNothing);
  });
}
