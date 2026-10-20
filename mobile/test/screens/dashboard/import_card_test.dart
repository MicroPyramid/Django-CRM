import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/dashboard_data.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/dashboard_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/dashboard/dashboard_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// The home card that offers an import to a workspace with nothing in it
/// yet, the web home page's "Bring in your contacts" card. `GET /dashboard/`
/// decides both halves: `empty_workspace` (no real contact or lead the caller
/// can see) and `can_import` (the import views would let them in).
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('the two keys are read, and absent means no card', () {
    final both = DashboardData.fromJson(const {
      'empty_workspace': true,
      'can_import': true,
    });
    expect(both.emptyWorkspace, isTrue);
    expect(both.canImport, isTrue);
    expect(both.offersImport, isTrue);

    final old = DashboardData.fromJson(const {});
    expect(old.emptyWorkspace, isFalse);
    expect(old.canImport, isFalse);
    expect(old.offersImport, isFalse);
  });

  Future<GoRouter> pump(WidgetTester tester, DashboardData data) async {
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    tester.platformDispatcher.textScaleFactorTestValue = 1.3;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    final router = GoRouter(
      initialLocation: AppRoutes.dashboard,
      routes: [
        GoRoute(
          path: AppRoutes.dashboard,
          builder: (_, _) => const DashboardScreen(),
        ),
        GoRoute(
          path: AppRoutes.importWelcome,
          builder: (_, _) => const Text('the welcome screen'),
        ),
      ],
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith(_FakeAuth.new),
          dashboardProvider.overrideWith(() => _FakeDashboard(data)),
        ],
        child: MaterialApp.router(theme: AppTheme.light, routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();
    return router;
  }

  testWidgets('an empty workspace that may import is offered it, and the '
      'card opens the welcome screen', (tester) async {
    final router = await pump(
      tester,
      const DashboardData(emptyWorkspace: true, canImport: true),
    );

    expect(tester.takeException(), isNull);
    expect(find.text('Bring in your contacts'), findsOneWidget);
    expect(
      find.text(
        'Upload a spreadsheet and your workspace fills up in a minute.',
      ),
      findsOneWidget,
    );
    final button = find.ancestor(
      of: find.text('Import a spreadsheet'),
      matching: find.byWidgetPredicate((w) => w is ButtonStyleButton),
    );
    expect(tester.getSize(button).height, greaterThanOrEqualTo(44));

    await tester.tap(find.text('Import a spreadsheet'));
    await tester.pumpAndSettle();

    expect(find.text('the welcome screen'), findsOneWidget);
    // Pushed, so back returns to the dashboard.
    expect(router.canPop(), isTrue);
  });

  for (final (name, data) in [
    (
      'a workspace with records',
      const DashboardData(emptyWorkspace: false, canImport: true),
    ),
    (
      'a member who may not import',
      const DashboardData(emptyWorkspace: true, canImport: false),
    ),
  ]) {
    testWidgets('$name is not offered it', (tester) async {
      await pump(tester, data);

      expect(find.text('Bring in your contacts'), findsNothing);
      expect(find.text('Import a spreadsheet'), findsNothing);
      // The control: the dashboard itself did render.
      expect(find.text('Pipeline'), findsOneWidget);
    });
  }
}

class _FakeDashboard extends DashboardNotifier {
  _FakeDashboard(this.data);

  final DashboardData data;

  @override
  Future<DashboardData> build() async => data;

  @override
  Future<void> refresh() async {}
}

class _FakeAuth extends AuthNotifier {
  @override
  AuthState build() {
    const org = Organization(id: 'org-1', name: 'Test Org');
    return AuthState(
      user: const AuthUser(id: 'user-1', email: 'user@example.com'),
      organizations: [org],
      selectedOrganization: org,
      isAuthenticated: true,
    );
  }
}
