import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/deal.dart';
import 'package:bottle_crm/data/models/deal_pipeline.dart';
import 'package:bottle_crm/data/models/lead_source.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/deal_pipelines_provider.dart';
import 'package:bottle_crm/providers/deals_provider.dart';
import 'package:bottle_crm/providers/lead_sources_provider.dart';
import 'package:bottle_crm/screens/deals/deal_form_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// A deal's `lead_source` goes up only when the user picked another one, so a
/// key this build does not know survives an edit of anything else. An older
/// API keeps deals on its uppercase list, which the picker then offers.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const sources = LeadSourcesAnswer(
    sources: [
      LeadSource(id: 's1', key: 'email', label: 'Email', order: 1),
      LeadSource(id: 's2', key: 'google ads', label: 'Google ads', order: 2),
    ],
  );

  Deal deal(String source) => Deal.fromJson({
    'id': 'd1',
    'name': 'Engines for the Admiralty',
    'stage': 'PROSPECTING',
    'probability': 10,
    'currency': 'USD',
    'lead_source': source,
  });

  Future<_FakeDeals> open(
    WidgetTester tester, {
    Deal? stored,
    LeadSourcesAnswer answer = sources,
  }) async {
    final fake = _FakeDeals();
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith(_FakeAuth.new),
          dealPipelinesProvider.overrideWith(_FakePipelines.new),
          dealsProvider.overrideWith(() => fake),
          leadSourcesProvider.overrideWith(() => _FakeSources(answer)),
        ],
        child: MaterialApp.router(
          theme: AppTheme.light,
          routerConfig: GoRouter(
            initialLocation: '/deals/form',
            routes: [
              GoRoute(
                path: '/deals',
                builder: (_, _) => const Text('list'),
                routes: [
                  GoRoute(
                    path: 'form',
                    builder: (_, _) => stored == null
                        ? const DealFormScreen()
                        : DealFormScreen(dealId: 'd1', initialDeal: stored),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    return fake;
  }

  Future<void> pick(WidgetTester tester, String current, String to) async {
    final field = find.text(current);
    await tester.ensureVisible(field.first);
    await tester.tap(field.first);
    await tester.pumpAndSettle();
    await tester.tap(find.text(to).last);
    await tester.pumpAndSettle();
  }

  Future<void> save(WidgetTester tester, String label) async {
    final button = find.text(label);
    await tester.ensureVisible(button);
    await tester.tap(button);
    await tester.pumpAndSettle();
  }

  testWidgets('an untouched source is not sent on an edit', (tester) async {
    final fake = await open(tester, stored: deal('trade show'));
    expect(find.text('trade show'), findsOneWidget);
    await save(tester, 'Update Deal');

    expect(fake.updates.single.containsKey('lead_source'), isFalse);
  });

  testWidgets('a picked source is sent', (tester) async {
    final fake = await open(tester, stored: deal('google ads'));
    await pick(tester, 'Google ads', 'Email');
    await save(tester, 'Update Deal');

    expect(fake.updates.single['lead_source'], 'email');
  });

  testWidgets('choosing None clears it', (tester) async {
    final fake = await open(tester, stored: deal('google ads'));
    await pick(tester, 'Google ads', 'None');
    await save(tester, 'Update Deal');

    expect(fake.updates.single['lead_source'], '');
  });

  testWidgets('an older API offers its own uppercase deal list', (
    tester,
  ) async {
    final fake = await open(
      tester,
      stored: deal('CALL'),
      answer: const LeadSourcesAnswer.legacy(),
    );
    await pick(tester, 'Call', 'Website');
    await save(tester, 'Update Deal');

    expect(fake.updates.single['lead_source'], 'WEBSITE');
  });
}

class _FakeSources extends LeadSourcesNotifier {
  _FakeSources(this.answer);

  final LeadSourcesAnswer answer;

  @override
  Future<LeadSourcesAnswer> build() async => answer;
}

class _FakePipelines extends DealPipelinesNotifier {
  @override
  Future<List<DealPipeline>> build() async => [DealPipeline.legacy];
}

class _FakeDeals extends DealsNotifier {
  final List<Map<String, dynamic>> updates = [];

  @override
  Future<DealsListData> build() async => const DealsListData();

  @override
  Future<({bool success, String? error, Deal? deal})> updateDeal(
    String id,
    Deal deal, {
    bool withLeadSource = false,
  }) async {
    updates.add(deal.toJson(withLeadSource: withLeadSource));
    return (success: true, error: null, deal: null);
  }
}

class _FakeAuth extends AuthNotifier {
  @override
  AuthState build() {
    const org = Organization(
      id: 'org-1',
      name: 'Test Org',
      role: 'ADMIN',
      defaultCurrency: 'USD',
    );
    return AuthState(
      user: const AuthUser(id: 'user-1', email: 'user@example.com'),
      organizations: [org],
      selectedOrganization: org,
      isAuthenticated: true,
    );
  }
}
