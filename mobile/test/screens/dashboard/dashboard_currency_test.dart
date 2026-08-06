import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/dashboard_data.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/dashboard_provider.dart';
import 'package:bottle_crm/screens/dashboard/dashboard_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// The dashboard took its currency symbol from the stored org record. Sign-in
/// and the org switch returned `{id, name, role}` and nothing else, so
/// `currencySymbol` was always null and every amount fell back to a dollar
/// sign. Those endpoints now send the currency (see
/// `TestOrgPayloadCarriesCurrency` on the backend), but the dashboard reads it
/// from `/api/dashboard/` instead, which reports the currency it actually
/// priced these totals in. The fake org below therefore carries no symbol on
/// purpose: the screen must not need one.
///
/// The same block reports how many deals were left out of those totals for
/// being in another currency. Ignoring it made a stage of foreign-currency
/// deals vanish from the chart, because the chart filtered on value and the
/// server had already zeroed it.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Widget host(DashboardData data) => ProviderScope(
    overrides: [
      authProvider.overrideWith(() => _FakeAuth()),
      dashboardProvider.overrideWith(() => _FakeDashboard(data)),
    ],
    child: MaterialApp(theme: AppTheme.light, home: const DashboardScreen()),
  );

  testWidgets('amounts print the org currency, not a dollar sign', (
    tester,
  ) async {
    await tester.pumpWidget(
      host(
        const DashboardData(
          revenueMetrics: RevenueMetrics(
            pipelineValue: 1463538,
            currency: 'EUR',
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('€'), findsWidgets);
    expect(find.textContaining(r'$'), findsNothing);
  });

  testWidgets('a stage holding only foreign-currency deals still appears', (
    tester,
  ) async {
    await tester.pumpWidget(
      host(
        const DashboardData(
          pipelineByStage: [
            PipelineStage(
              code: 'PROPOSAL',
              label: 'Proposal',
              count: 2,
              value: 0,
            ),
          ],
          revenueMetrics: RevenueMetrics(currency: 'USD'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // The stage is on the chart, and reports the deals it holds rather than a
    // priced zero it cannot back up.
    expect(find.text('Proposal'), findsOneWidget);
    expect(find.text('2 deals'), findsOneWidget);
  });

  testWidgets('deals left out of the totals are named', (tester) async {
    await tester.pumpWidget(
      host(
        const DashboardData(
          pipelineByStage: [
            PipelineStage(
              code: 'PROPOSAL',
              label: 'Proposal',
              count: 4,
              value: 90000,
            ),
          ],
          revenueMetrics: RevenueMetrics(
            pipelineValue: 90000,
            currency: 'USD',
            otherCurrencyCount: 3,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('3 deals in other currencies'), findsOneWidget);
  });

  testWidgets('an org with one currency gets no exclusion note', (
    tester,
  ) async {
    await tester.pumpWidget(
      host(
        const DashboardData(
          pipelineByStage: [
            PipelineStage(
              code: 'PROPOSAL',
              label: 'Proposal',
              count: 4,
              value: 90000,
            ),
          ],
          revenueMetrics: RevenueMetrics(pipelineValue: 90000),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('other currencies'), findsNothing);
  });

  testWidgets('the month result and the weighted forecast are on the board', (
    tester,
  ) async {
    await tester.pumpWidget(
      host(
        const DashboardData(
          revenueMetrics: RevenueMetrics(
            pipelineValue: 200000,
            weightedPipeline: 84000,
            wonThisMonth: 40000,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Won This Month'), findsOneWidget);
    expect(find.text('Weighted'), findsOneWidget);
  });
}

class _FakeDashboard extends DashboardNotifier {
  _FakeDashboard(this.data);

  final DashboardData data;

  @override
  Future<DashboardData> build() async => data;

  @override
  Future<void> refresh() async {}
}

/// Deliberately bare. If any assertion here starts depending on the org
/// record, this is the fake that will catch it.
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
