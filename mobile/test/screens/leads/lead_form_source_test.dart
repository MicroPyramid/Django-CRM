import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/lead.dart';
import 'package:bottle_crm/data/models/lead_source.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/lead_sources_provider.dart';
import 'package:bottle_crm/providers/leads_provider.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/screens/leads/lead_form_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:bottle_crm/widgets/common/common.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// The lead form sends `source`, `source_detail` and `source_ref` only when
/// the user changed them.
///
/// The org edits its source list, so a lead can hold a key this build has
/// never seen. Sending the form's copy back on every save is how older builds
/// turned every such source into `other`; the server now guards builds that
/// send no version, and this one sends its version, so it must keep the
/// promise itself.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const sources = LeadSourcesAnswer(
    sources: [
      LeadSource(id: 's1', key: 'email', label: 'Email', order: 1),
      LeadSource(id: 's2', key: 'google ads', label: 'Google ads', order: 2),
    ],
  );

  Lead lead({String source = 'google ads'}) => Lead.fromJson({
    'id': 'lead-1',
    'title': 'Engine enquiry',
    'first_name': 'Ada',
    'last_name': 'Lovelace',
    'email': 'ada@example.com',
    'company_name': 'Analytical Engines',
    'status': 'assigned',
    'source': source,
    'source_detail': 'Spring open day',
    'source_ref': 'ad-42',
  });

  Future<_FakeLeads> open(
    WidgetTester tester, {
    Lead? stored,
    LeadSourcesAnswer answer = sources,
  }) async {
    final fake = _FakeLeads(stored);
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith(_FakeAuth.new),
          leadsProvider.overrideWith(() => fake),
          leadSourcesProvider.overrideWith(() => _FakeSources(answer)),
          usersProvider.overrideWithValue(const []),
          tagsProvider.overrideWithValue(const []),
        ],
        child: MaterialApp.router(
          theme: AppTheme.light,
          routerConfig: GoRouter(
            initialLocation: '/leads/form',
            routes: [
              GoRoute(
                path: '/leads',
                builder: (_, _) => const Text('list'),
                routes: [
                  GoRoute(
                    path: 'form',
                    builder: (_, _) => stored == null
                        ? const LeadFormScreen()
                        : const LeadFormScreen(leadId: 'lead-1'),
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

  Future<void> save(WidgetTester tester, String label) async {
    await tester.tap(find.text(label));
    await tester.pumpAndSettle();
  }

  Future<void> pickSource(
    WidgetTester tester,
    String current,
    String to,
  ) async {
    final field = find.text(current);
    await tester.ensureVisible(field.first);
    await tester.tap(field.first);
    await tester.pumpAndSettle();
    await tester.tap(find.text(to).last);
    await tester.pumpAndSettle();
  }

  testWidgets('an untouched save sends no source, sub-source or reference', (
    tester,
  ) async {
    final fake = await open(tester, stored: lead());
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Analytical Engines'),
      'Difference Engines',
    );
    await save(tester, 'Update Lead');

    final body = fake.updates.single;
    expect(body['company_name'], 'Difference Engines');
    expect(body.containsKey('source'), isFalse);
    expect(body.containsKey('source_detail'), isFalse);
    expect(body.containsKey('source_ref'), isFalse);
  });

  testWidgets('a source the list lacks is shown, kept, and not sent', (
    tester,
  ) async {
    final fake = await open(tester, stored: lead(source: 'trade show'));
    expect(find.text('trade show'), findsOneWidget);
    await save(tester, 'Update Lead');
    expect(fake.updates.single.containsKey('source'), isFalse);
  });

  testWidgets('picking another source sends it', (tester) async {
    final fake = await open(tester, stored: lead());
    await pickSource(tester, 'Google ads', 'Email');
    await save(tester, 'Update Lead');

    expect(fake.updates.single['source'], 'email');
    expect(fake.updates.single.containsKey('source_detail'), isFalse);
  });

  testWidgets('clearing the source sends null', (tester) async {
    final fake = await open(tester, stored: lead());
    await pickSource(tester, 'Google ads', 'None');
    await save(tester, 'Update Lead');
    expect(fake.updates.single.containsKey('source'), isTrue);
    expect(fake.updates.single['source'], isNull);
  });

  testWidgets('editing the sub-source sends only that', (tester) async {
    final fake = await open(tester, stored: lead());
    final field = find.widgetWithText(
      FloatingLabelInput,
      'Sub-source (Optional)',
    );
    await tester.ensureVisible(field);
    await tester.enterText(
      find.descendant(of: field, matching: find.byType(TextFormField)),
      'Autumn open day',
    );
    await save(tester, 'Update Lead');

    final body = fake.updates.single;
    expect(body['source_detail'], 'Autumn open day');
    expect(body.containsKey('source'), isFalse);
    expect(body.containsKey('source_ref'), isFalse);
  });

  testWidgets('a new lead with no source sends none of the three', (
    tester,
  ) async {
    final fake = await open(tester);
    Future<void> type(String label, String text) async {
      final field = find.widgetWithText(FloatingLabelInput, label);
      await tester.ensureVisible(field);
      await tester.enterText(
        find.descendant(of: field, matching: find.byType(TextFormField)),
        text,
      );
    }

    await type('Lead Title *', 'Compiler enquiry');
    await type('First Name *', 'Grace');
    await type('Last Name *', 'Hopper');
    await type('Email *', 'grace@example.com');
    await type('Company *', 'Navy');
    await save(tester, 'Create Lead');

    final body = fake.creates.single;
    expect(body.containsKey('source'), isFalse);
    expect(body.containsKey('source_detail'), isFalse);
    expect(body.containsKey('source_ref'), isFalse);
  });

  testWidgets('an older API hides the sub-source and reference fields', (
    tester,
  ) async {
    await open(tester, answer: const LeadSourcesAnswer.legacy());
    expect(find.text('Sub-source (Optional)'), findsNothing);
    expect(find.text('Reference (Optional)'), findsNothing);
  });
}

class _FakeSources extends LeadSourcesNotifier {
  _FakeSources(this.answer);

  final LeadSourcesAnswer answer;

  @override
  Future<LeadSourcesAnswer> build() async => answer;
}

class _FakeAuth extends AuthNotifier {
  @override
  AuthState build() {
    final org = Organization(id: 'org-1', name: 'Test Org', role: 'ADMIN');
    return AuthState(
      user: AuthUser(id: 'u1', email: 'ada@example.com'),
      organizations: [org],
      selectedOrganization: org,
      isAuthenticated: true,
    );
  }
}

class _FakeLeads extends LeadsNotifier {
  _FakeLeads(this.stored);

  final Lead? stored;
  final List<Map<String, dynamic>> updates = [];
  final List<Map<String, dynamic>> creates = [];

  @override
  Future<LeadsListData> build() async => const LeadsListData();

  @override
  Future<LeadDetail?> getLeadDetail(
    String id, {
    void Function()? onNotFound,
  }) async => LeadDetail(lead: stored!);

  @override
  Future<ApiResponse<Map<String, dynamic>>> updateLead(
    String id,
    Map<String, dynamic> leadData,
  ) async {
    updates.add(leadData);
    return const ApiResponse(success: true, data: {}, statusCode: 200);
  }

  @override
  Future<ApiResponse<Map<String, dynamic>>> createLead(
    Map<String, dynamic> leadData,
  ) async {
    creates.add(leadData);
    return const ApiResponse(success: true, data: {}, statusCode: 201);
  }
}
