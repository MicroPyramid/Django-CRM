import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/data/models/org_module.dart';
import 'package:bottle_crm/data/models/automation.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/screens/settings/apps_screen.dart';
import 'package:bottle_crm/screens/settings/settings_hub_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../../support/modules_fixtures.dart';

class _NoObjects extends CustomObjectsNotifier {
  @override
  Future<CustomObjectsAnswer?> build() async => null;
}

class _NoRules extends AutomationRulesNotifier {
  @override
  Future<AutomationRulesAnswer> build() async =>
      const AutomationRulesAnswer(rules: []);
}

Future<FakeOrgModules> _pump(
  WidgetTester tester, {
  OrgModulesAnswer? answer,
  bool noAnswer = false,
  bool admin = true,
  bool fail = false,
  List<String> refusals = const [],
  Widget home = const AppsScreen(),
}) async {
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final fake = FakeOrgModules(() async {
    if (fail) throw Exception('boom');
    return noAnswer ? null : (answer ?? modulesAnswer());
  }, refusals: refusals);
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        ...modulesOverrides(fake, admin: admin),
        customObjectsProvider.overrideWith(_NoObjects.new),
        automationRulesProvider.overrideWith(_NoRules.new),
      ],
      child: MaterialApp.router(
        theme: AppTheme.light,
        routerConfig: GoRouter(
          initialLocation: '/here',
          routes: [
            GoRoute(path: '/here', builder: (_, _) => home),
            GoRoute(
              path: '/more/settings/web-forms',
              builder: (_, _) => const Text('web forms page'),
            ),
            GoRoute(
              path: '/more/settings/inbound-email',
              builder: (_, _) => const Text('inbound email page'),
            ),
          ],
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
  return fake;
}

Finder _switchOf(String label) => find.descendant(
  of: find
      .ancestor(of: find.text(label), matching: find.byType(Container))
      .first,
  matching: find.byType(Switch),
);

Finder _mover(String tooltip) =>
    find.byWidgetPredicate((w) => w is IconButton && w.tooltip == tooltip);

Switch _sw(WidgetTester tester, String label) =>
    tester.widget<Switch>(_switchOf(label));

void main() {
  testWidgets('admins see the Modules row after Organization, and members do '
      'not', (tester) async {
    await _pump(tester, home: const SettingsHubScreen());
    await tester.scrollUntilVisible(
      find.text('Modules'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    final org = tester.getTopLeft(find.text('Organization').last).dy;
    final modules = tester.getTopLeft(find.text('Modules')).dy;
    expect(modules, greaterThan(org));
    expect(
      find.text(
        'Switch off the parts of BottleCRM this organization does '
        'not use',
      ),
      findsOneWidget,
    );

    await _pump(tester, admin: false, home: const SettingsHubScreen());
    await tester.scrollUntilVisible(
      find.text('Help center'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Modules'), findsNothing);

    await _pump(tester, noAnswer: true, home: const SettingsHubScreen());
    await tester.scrollUntilVisible(
      find.text('Help center'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Modules'), findsNothing);
  });

  testWidgets('groups the modules under Sell, Serve and Bill in the served '
      'order', (tester) async {
    await _pump(tester);
    expect(find.text('Modules'), findsOneWidget);
    expect(find.textContaining('Nothing is deleted'), findsOneWidget);
    final sell = tester.getTopLeft(find.text('SELL')).dy;
    final serve = tester.getTopLeft(find.text('SERVE')).dy;
    expect(sell, lessThan(tester.getTopLeft(find.text('Pipeline')).dy));
    expect(
      tester.getTopLeft(find.text('Pipeline')).dy,
      lessThan(tester.getTopLeft(find.text('Leads')).dy),
    );
    expect(tester.getTopLeft(find.text('Goals')).dy, lessThan(serve));
    expect(serve, lessThan(tester.getTopLeft(find.text('Tasks')).dy));
    await tester.drag(find.byType(Scrollable).first, const Offset(0, -1200));
    await tester.pumpAndSettle();
    expect(find.text('BILL'), findsOneWidget);
    expect(find.text('Timesheet'), findsOneWidget);
  });

  testWidgets('switching off asks with the stops text, and Keep it on sends '
      'nothing', (tester) async {
    final fake = await _pump(tester);
    await tester.tap(_switchOf('Leads'));
    await tester.pumpAndSettle();
    expect(find.text('Switch off Leads?'), findsOneWidget);
    expect(find.text('Stops leads.'), findsOneWidget);
    await tester.tap(find.text('Keep it on'));
    await tester.pumpAndSettle();
    expect(fake.saved, isEmpty);

    await tester.tap(_switchOf('Leads'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Switch off'));
    await tester.pumpAndSettle();
    expect(fake.saved, hasLength(1));
    expect(fake.saved.single.off, ['leads']);
    expect(fake.saved.single.order.first, 'deals');
  });

  testWidgets('switching on sends at once, with the served order', (
    tester,
  ) async {
    final fake = await _pump(tester, answer: modulesAnswer(off: ['tasks']));
    expect(_sw(tester, 'Tasks').value, isFalse);
    await tester.tap(_switchOf('Tasks'));
    await tester.pumpAndSettle();
    expect(find.byType(AlertDialog), findsNothing);
    expect(fake.saved.single.off, isEmpty);
    expect(fake.saved.single.order, [
      'deals',
      'leads',
      'goals',
      'tasks',
      'tickets',
      'knowledge_base',
      'documents',
      'invoices',
      'timesheet',
    ]);
  });

  testWidgets('a module whose need is off shows Needs Pipeline and cannot be '
      'switched on', (tester) async {
    await _pump(tester, answer: modulesAnswer(off: ['deals']));
    expect(
      find.text('Needs Pipeline. It comes back when Pipeline is switched on.'),
      findsOneWidget,
    );
    expect(_sw(tester, 'Goals').onChanged, isNull);
    expect(_sw(tester, 'Goals').value, isFalse);

    await _pump(tester, answer: modulesAnswer(off: ['deals', 'goals']));
    expect(find.text('Needs Pipeline.'), findsOneWidget);
    expect(_sw(tester, 'Goals').onChanged, isNull);
  });

  testWidgets('the need reads with the served label', (tester) async {
    await _pump(
      tester,
      answer: modulesAnswer(off: ['deals'], labels: {'deals': 'Jobs'}),
    );
    expect(
      find.text('Needs Jobs. It comes back when Jobs is switched on.'),
      findsOneWidget,
    );
  });

  testWidgets('a refusal lists every message and links to web forms and '
      'inbound email', (tester) async {
    await _pump(tester, refusals: ['First refusal.', 'Second refusal.']);
    await tester.tap(_switchOf('Tickets'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Switch off'));
    await tester.pumpAndSettle();
    expect(find.text('First refusal.'), findsOneWidget);
    expect(find.text('Second refusal.'), findsOneWidget);
    await tester.tap(find.text('Inbound email'));
    await tester.pumpAndSettle();
    expect(find.text('inbound email page'), findsOneWidget);
    await _pump(tester, refusals: ['First refusal.']);
    await tester.tap(_switchOf('Leads'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Switch off'));
    await tester.pumpAndSettle();
    expect(find.text('Inbound email'), findsNothing);
    await tester.tap(find.text('Web forms'));
    await tester.pumpAndSettle();
    expect(find.text('web forms page'), findsOneWidget);
  });

  testWidgets('a refusal on a module with no forms shows no links', (
    tester,
  ) async {
    await _pump(tester, refusals: ['No.']);
    await tester.tap(_switchOf('Tasks'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Switch off'));
    await tester.pumpAndSettle();
    expect(find.text('No.'), findsOneWidget);
    expect(find.text('Web forms'), findsNothing);
    expect(find.text('Inbound email'), findsNothing);
  });

  testWidgets('moves up and down within a group and disables at the ends', (
    tester,
  ) async {
    final fake = await _pump(tester);
    final up = _mover('Move up');
    final down = _mover('Move down');
    expect(tester.widget<IconButton>(up.first).onPressed, isNull);
    expect(tester.widget<IconButton>(down.first).onPressed, isNotNull);
    // Goals is the last of Sell: its down button is the third.
    expect(tester.widget<IconButton>(down.at(2)).onPressed, isNull);
    await tester.tap(down.first);
    await tester.pumpAndSettle();
    expect(fake.saved.single.order.take(3), ['leads', 'deals', 'goals']);
    await tester.tap(up.at(2));
    await tester.pumpAndSettle();
    expect(fake.saved.last.order.take(3), ['deals', 'goals', 'leads']);
  });

  testWidgets(
    'a member who opens it sees the notice and no write is possible',
    (tester) async {
      final fake = await _pump(tester, admin: false);
      expect(
        find.text('Only an organization admin can manage apps and modules.'),
        findsOneWidget,
      );
      expect(find.byType(Switch), findsNothing);
      expect(fake.saved, isEmpty);

      await _pump(tester, answer: modulesAnswer(canEdit: false));
      expect(
        find.text('Only an organization admin can switch modules on or off.'),
        findsOneWidget,
      );
      expect(find.byType(Switch), findsNothing);
    },
  );

  testWidgets('an older server shows that it does not offer modules', (
    tester,
  ) async {
    await _pump(tester, noAnswer: true);
    expect(
      find.text('This server does not offer modules yet.'),
      findsOneWidget,
    );
    expect(find.byType(Switch), findsNothing);
  });

  testWidgets('a failure shows the error state with Try again', (tester) async {
    await _pump(tester, fail: true);
    expect(find.text('Could not load modules'), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });
}
