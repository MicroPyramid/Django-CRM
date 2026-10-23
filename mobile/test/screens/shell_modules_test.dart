import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/data/models/org_module.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/settings/more_screen.dart';
import 'package:bottle_crm/screens/settings/settings_hub_screen.dart';
import 'package:bottle_crm/widgets/common/app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../support/modules_fixtures.dart';

class _NoObjects extends CustomObjectsNotifier {
  @override
  Future<CustomObjectsAnswer?> build() async => null;
}

/// Opening More reloads the answer, so a reload must serve the latest one.
class _Modules extends FakeOrgModules {
  _Modules(OrgModulesAnswer? first) : this._(_Latest(first));

  _Modules._(this._latest) : super(() async => _latest.answer);

  final _Latest _latest;

  void show(OrgModulesAnswer? next) {
    _latest.answer = next;
    state = AsyncData(next);
  }
}

class _Latest {
  _Latest(this.answer);

  OrgModulesAnswer? answer;
}

OrgModulesAnswer _ordered(List<String> order, {List<String> off = const []}) {
  final base = modulesAnswer(off: off);
  return OrgModulesAnswer(
    canEdit: true,
    modules: [
      for (final k in order) base.modules.firstWhere((m) => m.key == k),
    ],
  );
}

Future<void> _phone(WidgetTester tester) async {
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

Future<ProviderContainer> _shell(
  WidgetTester tester,
  _Modules fake, {
  String start = '/b0',
}) async {
  final container = ProviderContainer(
    overrides: [
      ...modulesOverrides(fake),
      customObjectsProvider.overrideWith(_NoObjects.new),
    ],
  );
  addTearDown(container.dispose);
  final router = GoRouter(
    initialLocation: start,
    routes: [
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) => AppShell(navigationShell: shell),
        branches: [
          for (var i = 0; i < 5; i++)
            StatefulShellBranch(
              routes: [
                GoRoute(
                  path: '/b$i',
                  builder: (_, _) => Scaffold(body: Text('branch $i')),
                ),
              ],
            ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.more,
                builder: (_, _) => const MoreScreen(),
              ),
            ],
          ),
        ],
      ),
    ],
  );
  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: MaterialApp.router(routerConfig: router),
    ),
  );
  await tester.pumpAndSettle();
  return container;
}

void main() {
  testWidgets('the bar and the More sheet follow the modules, and an org '
      'switch redraws them', (tester) async {
    final fake = _Modules(modulesAnswer());
    await _shell(tester, fake);

    for (final l in ['Home', 'Leads', 'Deals', 'Tickets', 'More']) {
      expect(find.text(l), findsOneWidget, reason: l);
    }
    expect(find.text('Tasks'), findsNothing);

    await tester.tap(find.text('More'));
    await tester.pumpAndSettle();
    expect(find.text('Tasks'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);
    await tester.tapAt(const Offset(10, 10));
    await tester.pumpAndSettle();

    fake.show(modulesAnswer(off: ['deals']));
    await tester.pumpAndSettle();
    expect(find.text('Deals'), findsNothing);
    expect(find.text('Tasks'), findsOneWidget, reason: 'Tasks took the slot');
    await tester.tap(find.text('More'));
    await tester.pumpAndSettle();
    expect(find.text('Tasks'), findsOneWidget, reason: 'only the bar has it');
    expect(find.text('Settings'), findsOneWidget);
    await tester.tapAt(const Offset(10, 10));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Tasks'));
    await tester.pumpAndSettle();
    expect(find.text('branch 4'), findsOneWidget);

    fake.show(modulesAnswer(off: ['tasks']));
    await tester.pumpAndSettle();
    expect(find.text('Tasks'), findsNothing);
    expect(find.text('Deals'), findsOneWidget);
    await tester.tap(find.text('More'));
    await tester.pumpAndSettle();
    expect(find.text('Tasks'), findsNothing);
    expect(find.text('Settings'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('More lists accounts, contacts, notifications, then the modules '
      'that are on, in order', (tester) async {
    final fake = _Modules(
      _ordered(
        [
          'timesheet',
          'invoices',
          'documents',
          'knowledge_base',
          'tasks',
          'goals',
          'deals',
          'leads',
          'tickets',
        ],
        off: ['documents'],
      ),
    );
    await _shell(tester, fake, start: AppRoutes.more);

    final labels = [
      'Accounts',
      'Contacts',
      'Notifications',
      'Timesheet',
      'Invoices',
      'Knowledge base',
      'Tasks',
      'Goals',
    ];
    double top(String l) => tester.getTopLeft(find.text(l).first).dy;
    for (var i = 1; i < labels.length; i++) {
      expect(
        top(labels[i]),
        greaterThan(top(labels[i - 1])),
        reason: labels[i],
      );
    }
    expect(find.text('Documents'), findsNothing);
    expect(find.text('Articles for your team and your customers'), findsOne);

    fake.show(modulesAnswer(off: ['tasks', 'invoices', 'knowledge_base']));
    await tester.pumpAndSettle();
    for (final l in ['Tasks', 'Invoices', 'Knowledge base']) {
      expect(find.text(l), findsNothing, reason: l);
    }
    for (final l in ['Accounts', 'Contacts', 'Notifications', 'Goals']) {
      expect(find.text(l), findsOneWidget, reason: l);
    }
    expect(find.text('Documents'), findsOneWidget);
    expect(find.text('Timesheet'), findsOneWidget);
  });

  testWidgets('More shows every module row when the server has no answer', (
    tester,
  ) async {
    await _shell(tester, _Modules(null), start: AppRoutes.more);
    for (final l in [
      'Tasks',
      'Goals',
      'Knowledge base',
      'Documents',
      'Invoices',
      'Timesheet',
    ]) {
      expect(find.text(l), findsOneWidget, reason: l);
    }
  });

  testWidgets('the hub hides the rows of off modules and shows Products while '
      'products are on', (tester) async {
    await _phone(tester);
    final fake = _Modules(modulesAnswer());
    await tester.pumpWidget(
      ProviderScope(
        key: UniqueKey(),
        overrides: [
          ...modulesOverrides(fake),
          customObjectsProvider.overrideWith(_NoObjects.new),
        ],
        child: const MaterialApp(home: SettingsHubScreen()),
      ),
    );
    await tester.pumpAndSettle();
    Future<void> see(Finder f) => tester.scrollUntilVisible(
      f,
      200,
      scrollable: find.byType(Scrollable).first,
    );

    expect(find.text('Lead pipelines'), findsOneWidget);
    expect(find.text('Deal pipelines'), findsOneWidget);
    expect(find.text('Products'), findsOneWidget);
    expect(
      tester.getTopLeft(find.text('Products')).dy,
      greaterThan(tester.getTopLeft(find.text('Deal pipelines')).dy),
    );
    expect(find.text('TICKETS'), findsOneWidget);
    expect(find.text('Routing'), findsOneWidget);
    await see(find.text('Help center'));
    expect(find.text('Help center'), findsOneWidget);

    fake.show(modulesAnswer(off: ['leads', 'tickets', 'knowledge_base']));
    await tester.pumpAndSettle();
    expect(find.text('Lead pipelines'), findsNothing);
    expect(find.text('TICKETS'), findsNothing);
    expect(find.text('Routing'), findsNothing);
    expect(find.text('Approval rules'), findsNothing);
    expect(find.text('Help center'), findsNothing);
    expect(find.text('Deal pipelines'), findsOneWidget);
    expect(find.text('Products'), findsOneWidget);

    fake.show(modulesAnswer(off: ['deals', 'invoices']));
    await tester.pumpAndSettle();
    expect(find.text('Deal pipelines'), findsNothing);
    expect(find.text('Products'), findsNothing);
    expect(find.text('Lead pipelines'), findsOneWidget);
  });
}
