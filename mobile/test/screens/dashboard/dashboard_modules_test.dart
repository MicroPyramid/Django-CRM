import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/dashboard_data.dart';
import 'package:bottle_crm/data/models/org_module.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/dashboard_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/dashboard/dashboard_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../../support/modules_fixtures.dart';

const _data = DashboardData(
  leadsCount: 4,
  urgentCounts: UrgentCounts(
    overdueTasks: 2,
    tasksDueToday: 1,
    followupsToday: 3,
    hotLeads: 1,
  ),
  pipelineByStage: [
    PipelineStage(code: 'QUALIFIED', label: 'Qualified', count: 2, value: 100),
  ],
  hotLeads: [HotLead(id: 'l1', firstName: 'Hot', lastName: 'Harriet')],
  goalSummary: [
    DashboardGoal(
      id: 'g1',
      name: 'Q4 quota',
      goalType: 'REVENUE',
      targetValue: 100,
      progressValue: 40,
      progressPercent: 40,
      status: 'on_track',
    ),
  ],
);

Future<void> _pump(WidgetTester tester, OrgModulesAnswer? answer) async {
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final router = GoRouter(
    initialLocation: AppRoutes.dashboard,
    routes: [
      GoRoute(
        path: AppRoutes.dashboard,
        builder: (_, _) => const DashboardScreen(),
      ),
      GoRoute(
        path: AppRoutes.dealCreate,
        builder: (_, _) => const Text('the deal form'),
      ),
      GoRoute(
        path: AppRoutes.taskCreate,
        builder: (_, _) => const Text('the task form'),
      ),
      GoRoute(
        path: AppRoutes.leadCreate,
        builder: (_, _) => const Text('the lead form'),
      ),
    ],
  );
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        ...modulesOverrides(FakeOrgModules(() async => answer)),
        authProvider.overrideWith(_FakeAuth.new),
        dashboardProvider.overrideWith(() => _FakeDashboard()),
      ],
      child: MaterialApp.router(theme: AppTheme.light, routerConfig: router),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('home shows every section while every module is on', (
    tester,
  ) async {
    await _pump(tester, modulesAnswer());
    for (final t in [
      'Pipeline',
      'Leads',
      'Overdue',
      'Follow-ups',
      'Pipeline Overview',
      'Where you stand',
      'Hot Leads',
      'Upcoming Tasks',
    ]) {
      expect(find.text(t), findsWidgets, reason: t);
    }
  });

  testWidgets('home hides the sections and quick actions of off modules', (
    tester,
  ) async {
    await _pump(tester, modulesAnswer(off: ['deals']));
    expect(find.text('Pipeline'), findsNothing);
    expect(find.text('Open Deals'), findsNothing);
    expect(find.text('Conversion'), findsNothing);
    expect(find.text('Pipeline Overview'), findsNothing);
    expect(find.text('Where you stand'), findsNothing, reason: 'needs deals');
    expect(find.text('Leads'), findsOneWidget);
    expect(find.text('Upcoming Tasks'), findsOneWidget);
    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();
    expect(find.text('Add Deal'), findsNothing);
    expect(find.text('Add Lead'), findsOneWidget);
    expect(find.text('Add Task'), findsOneWidget);
  });

  testWidgets('with leads and tasks off, the urgent badges and lead sections '
      'go', (tester) async {
    await _pump(tester, modulesAnswer(off: ['leads', 'tasks']));
    for (final t in [
      'Overdue',
      'Due Today',
      'Follow-ups',
      'Hot Leads',
      'Needs Attention',
      'Upcoming Tasks',
      'Leads',
    ]) {
      expect(find.text(t), findsNothing, reason: t);
    }
    expect(find.text('Pipeline'), findsOneWidget);
    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();
    expect(find.text('Add Lead'), findsNothing);
    expect(find.text('Add Task'), findsNothing);
    expect(find.text('Add Deal'), findsOneWidget);
  });

  testWidgets('with deals and leads off the grid goes, and with no quick '
      'action left the button goes', (tester) async {
    await _pump(tester, modulesAnswer(off: ['deals', 'leads', 'tasks']));
    expect(find.text('Open Deals'), findsNothing);
    expect(find.text('Leads'), findsNothing);
    expect(find.byType(GridView), findsNothing);
    expect(find.byType(FloatingActionButton), findsNothing);
  });

  testWidgets('Add Deal and Add Task open their forms', (tester) async {
    await _pump(tester, modulesAnswer());
    for (final (row, form) in [
      ('Add Deal', 'the deal form'),
      ('Add Task', 'the task form'),
    ]) {
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();
      await tester.tap(find.text(row));
      await tester.pumpAndSettle();
      expect(find.text(form), findsOneWidget, reason: row);
      tester.state<NavigatorState>(find.byType(Navigator).first).pop();
      await tester.pumpAndSettle();
    }
  });
}

class _FakeDashboard extends DashboardNotifier {
  @override
  Future<DashboardData> build() async => _data;

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
