import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/dashboard_data.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/dashboard_provider.dart';
import 'package:bottle_crm/screens/dashboard/dashboard_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Four KPI cards summarised four lists and none was tappable, so the number
/// was a dead end. Three have an obvious list behind them. Conversion does
/// not, and stays a plain card rather than being given a destination that does
/// not exist.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('the cards that summarise a list are tappable, and Conversion '
      'is not', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith(() => _FakeAuth()),
          dashboardProvider.overrideWith(() => _FakeDashboard()),
        ],
        child: MaterialApp(
          theme: AppTheme.light,
          home: const DashboardScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    for (final label in ['Pipeline', 'Open Deals', 'Leads']) {
      expect(
        find.ancestor(of: find.text(label), matching: find.byType(InkWell)),
        findsWidgets,
        reason: '$label should reach the list it summarises',
      );
    }
    expect(
      find.ancestor(
        of: find.text('Conversion'),
        matching: find.byType(InkWell),
      ),
      findsNothing,
    );
  });
}

class _FakeDashboard extends DashboardNotifier {
  @override
  Future<DashboardData> build() async => const DashboardData(
    leadsCount: 6,
    revenueMetrics: RevenueMetrics(
      pipelineValue: 1463538,
      openOpportunitiesCount: 2,
      conversionRate: 5,
    ),
  );

  @override
  Future<void> refresh() async {}
}

class _FakeAuth extends AuthNotifier {
  @override
  AuthState build() {
    const org = Organization(
      id: 'org-1',
      name: 'Test Org',
      currencySymbol: r'$',
    );
    return AuthState(
      user: const AuthUser(id: 'user-1', email: 'user@example.com'),
      organizations: [org],
      selectedOrganization: org,
      isAuthenticated: true,
    );
  }
}
