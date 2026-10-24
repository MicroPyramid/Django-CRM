import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/providers/org_modules_provider.dart';
import 'package:bottle_crm/routes/app_routes.dart';
import 'package:bottle_crm/widgets/common/module_gate.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../support/modules_fixtures.dart';

List<String> _off = [];
Map<String, String> _labels = {};
final _key = GlobalKey();

Future<void> _pump(
  WidgetTester tester, {
  bool admin = true,
  String path = '/deals/:id',
}) async {
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final fake = FakeOrgModules(
    () async => modulesAnswer(off: _off, labels: _labels),
  );
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: modulesOverrides(fake, admin: admin),
      child: MaterialApp.router(
        theme: AppTheme.light,
        routerConfig: GoRouter(
          initialLocation: '/here',
          routes: [
            GoRoute(
              path: '/here',
              builder: (_, _) => ModuleGate(
                key: _key,
                path: path,
                child: const Text('the deal'),
              ),
            ),
            GoRoute(
              path: AppRoutes.dashboard,
              builder: (_, _) => const Text('home page'),
            ),
            GoRoute(
              path: AppRoutes.settingsApps,
              builder: (_, _) => const Text('modules page'),
            ),
          ],
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  setUp(() {
    _off = [];
    _labels = {};
  });

  testWidgets('the gate shows its child while the module is on', (
    tester,
  ) async {
    await _pump(tester);
    expect(find.text('the deal'), findsOneWidget);
    expect(find.textContaining('switched off'), findsNothing);
  });

  testWidgets('a core path is never gated', (tester) async {
    _off = ['deals', 'leads', 'tasks'];
    await _pump(tester, path: '/accounts/:id');
    expect(find.text('the deal'), findsOneWidget);
  });

  testWidgets('the gate shows the module view, and flips while open when the '
      'module goes off', (tester) async {
    _labels = {'deals': 'Opportunities'};
    await _pump(tester);
    expect(find.text('the deal'), findsOneWidget);

    _off = ['deals'];
    ProviderScope.containerOf(
      tester.element(find.byKey(_key)),
    ).invalidate(orgModulesProvider);
    await tester.pumpAndSettle();
    expect(find.text('the deal'), findsNothing);
    expect(find.text('Opportunities'), findsOneWidget);
    expect(find.text('Opportunities is switched off'), findsOneWidget);
    expect(
      find.text('Opportunities is switched off for this organization.'),
      findsOneWidget,
    );

    await tester.tap(find.text('Back to Home'));
    await tester.pumpAndSettle();
    expect(find.text('home page'), findsOneWidget);
  });

  testWidgets('admins get the settings button and members do not', (
    tester,
  ) async {
    _off = ['deals'];
    await _pump(tester);
    expect(find.text('Open Apps settings'), findsOneWidget);
    await tester.tap(find.text('Open Apps settings'));
    await tester.pumpAndSettle();
    expect(find.text('modules page'), findsOneWidget);

    await _pump(tester, admin: false);
    expect(find.text('Deals is switched off'), findsNothing);
    expect(find.text('Pipeline is switched off'), findsOneWidget);
    expect(find.text('Back to Home'), findsOneWidget);
    expect(find.text('Open Apps settings'), findsNothing);
  });

  testWidgets('products name invoices only when both modules are off', (
    tester,
  ) async {
    _off = ['invoices'];
    await _pump(tester, path: AppRoutes.products);
    expect(find.text('the deal'), findsOneWidget);

    _off = ['invoices', 'deals'];
    await _pump(tester, path: AppRoutes.products);
    expect(find.text('Invoices is switched off'), findsOneWidget);
  });

  testWidgets('a module whose need is off reads as off', (tester) async {
    _off = ['deals'];
    await _pump(tester, path: AppRoutes.goals);
    expect(find.text('Goals is switched off'), findsOneWidget);
  });
}
