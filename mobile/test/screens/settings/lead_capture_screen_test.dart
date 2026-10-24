import 'package:bottle_crm/data/models/lead_intake.dart';
import 'package:bottle_crm/data/models/lead_source.dart';
import 'package:bottle_crm/data/models/mailbox.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/lead_intakes_provider.dart';
import 'package:bottle_crm/providers/lead_sources_provider.dart';
import 'package:bottle_crm/providers/settings_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/settings/lead_capture_screen.dart';
import 'package:bottle_crm/screens/settings/lead_intake_detail_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

const _id = '3f2b8c1e-5a4d-4e8b-9c3a-1d2e3f4a5b6c';
const _key = 'lk_live_9b0f3c2a7e5d4c1b8a6f';

final _intake = LeadIntake.fromJson({
  'id': _id,
  'name': 'Google Ads, spring campaign for the coastal listings',
  'preset': 'google_ads',
  'url':
      'https://api.example.com/api/public/leads/$_id/?a-long-tail-that-must-wrap',
  'key_hint': 'a1b2',
  'mapping': [
    {'from': 'user_column_data.EMAIL', 'to': 'email'},
    {'from': 'user_column_data.FULL_NAME', 'to': 'first_name'},
  ],
  'default_source': 'google ads',
  'is_active': true,
  'last_received_at': '2026-10-20T09:00:00Z',
  'last_error': 'The last post had no email or phone, so it was rejected.',
});

final _deliveries = [
  IntakeDelivery.fromJson(const {
    'id': 'e1',
    'received_at': '2026-10-20T09:00:00Z',
    'result': 'created',
    'lead': 'l1',
    'external_id': 'gclid-1234567890',
  }),
  IntakeDelivery.fromJson(const {
    'id': 'e2',
    'received_at': '2026-10-19T09:00:00Z',
    'result': 'rejected',
    'error': 'No email or phone.',
  }),
];

MailboxesState _mailboxes({bool offered = true}) => MailboxesState(
  leadsOffered: offered,
  generatedDomain: offered ? 'in.example.com' : null,
  mailboxes: [
    Mailbox.fromJson({
      'id': 'm1',
      'address': 'acme-x1y2z3@in.example.com',
      'is_active': true,
      'creates': 'leads',
      'lead_source': 'email',
      'is_generated': true,
    }),
    Mailbox.fromJson({
      'id': 'm2',
      'address': 'help@acme.com',
      'is_active': true,
      'has_topic_arn': true,
    }),
  ],
);

/// Settings, Lead capture on the phone: web forms, webhooks and lead
/// addresses. A webhook's key is shown once, on a replace; an API older than
/// webhooks (404) loses that part of the screen and nothing else.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Future<_FakeIntakes> pump(
    WidgetTester tester, {
    bool admin = true,
    bool intakesOffered = true,
    bool leadAddresses = true,
    String start = AppRoutes.settingsLeadCapture,
    double textScale = 1.0,
    Size size = const Size(390, 844),
  }) async {
    final fake = _FakeIntakes(offered: intakesOffered);
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = Size(size.width * 3, size.height * 3);
    tester.platformDispatcher.textScaleFactorTestValue = textScale;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          isOrgAdminProvider.overrideWithValue(admin),
          leadIntakesProvider.overrideWith(() => fake),
          leadIntakeDeliveriesProvider.overrideWith(
            (ref, id) async => _deliveries,
          ),
          mailboxesProvider.overrideWith(
            () => _FakeMailboxes(_mailboxes(offered: leadAddresses)),
          ),
          leadSourcesProvider.overrideWith(_FakeSources.new),
        ],
        child: MaterialApp.router(
          routerConfig: GoRouter(
            initialLocation: start,
            routes: [
              GoRoute(
                path: AppRoutes.settingsLeadCapture,
                builder: (_, _) => const LeadCaptureScreen(),
              ),
              GoRoute(
                path: AppRoutes.settingsLeadCaptureWebhookDetail,
                builder: (_, s) => LeadIntakeDetailScreen(
                  intakeId: s.pathParameters['intakeId'] ?? '',
                ),
              ),
              GoRoute(
                path: AppRoutes.settingsWebForms,
                builder: (_, _) => const Text('web forms'),
              ),
              GoRoute(
                path: '/leads/:id',
                builder: (_, s) => Text('lead ${s.pathParameters['id']}'),
              ),
            ],
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    return fake;
  }

  final detail = AppRoutes.settingsLeadCaptureWebhook(_id);

  for (final scale in [1.0, 1.3]) {
    testWidgets('the list fits a 390px phone at ${scale}x text', (
      tester,
    ) async {
      await pump(tester, textScale: scale);
      expect(tester.takeException(), isNull);
      expect(find.text('WEBHOOKS'), findsOneWidget);
      expect(find.text('Receiving'), findsOneWidget);
      expect(find.text('LEAD ADDRESSES'), findsOneWidget);
      expect(find.text('acme-x1y2z3@in.example.com'), findsOneWidget);
      // The ticket address is the inbound email screen's, not this one's.
      expect(find.text('help@acme.com'), findsNothing);
    });

    testWidgets('a webhook fits a 390px phone at ${scale}x text', (
      tester,
    ) async {
      await pump(tester, start: detail, textScale: scale);
      expect(tester.takeException(), isNull);
      expect(find.text('Key ending a1b2'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.text('No email or phone.'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('both hold up at tablet width', (tester) async {
    await pump(tester, size: const Size(834, 1112), textScale: 1.3);
    expect(tester.takeException(), isNull);
    await pump(
      tester,
      start: detail,
      size: const Size(834, 1112),
      textScale: 1.3,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('an API without webhooks hides only that part', (tester) async {
    await pump(tester, intakesOffered: false);
    expect(find.text('WEBHOOKS'), findsNothing);
    expect(find.text('Web forms'), findsOneWidget);
    expect(find.text('LEAD ADDRESSES'), findsOneWidget);
  });

  testWidgets('an API without lead addresses hides that part', (tester) async {
    await pump(tester, leadAddresses: false);
    expect(find.text('LEAD ADDRESSES'), findsNothing);
    expect(find.text('Add a lead address'), findsNothing);
  });

  testWidgets('a member sees no webhooks and asks for none', (tester) async {
    final fake = await pump(tester, admin: false);
    expect(find.text('WEBHOOKS'), findsNothing);
    expect(fake.built, isFalse);
    expect(find.text('acme-x1y2z3@in.example.com'), findsOneWidget);
    expect(find.text('Add a lead address'), findsNothing);
  });

  testWidgets('a member opening a webhook link gets the notice', (
    tester,
  ) async {
    final fake = await pump(tester, admin: false, start: detail);
    expect(find.text('Administrators only'), findsOneWidget);
    expect(find.text('Replace key'), findsNothing);
    expect(fake.built, isFalse);
  });

  testWidgets('replacing the key shows the new one once', (tester) async {
    final fake = await pump(tester, start: detail);
    expect(find.text(_key), findsNothing);

    await tester.tap(find.text('Replace key'));
    await tester.pumpAndSettle();
    expect(find.textContaining('keeps working for 7 days'), findsOneWidget);
    await tester.tap(find.text('Replace key').last);
    await tester.pumpAndSettle();

    expect(fake.replaced, [_id]);
    expect(find.text(_key), findsOneWidget);
    expect(find.textContaining('only time the key is shown'), findsOneWidget);

    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();
    expect(find.text(_key), findsNothing);
    expect(find.text('Key ending a1b2'), findsOneWidget);
  });

  testWidgets('switching off sends the switch', (tester) async {
    final fake = await pump(tester, start: detail);
    await tester.tap(find.text('Turn off'));
    await tester.pumpAndSettle();
    expect(fake.switched, [(_id, false)]);
  });

  testWidgets('a delivery that made a lead opens it', (tester) async {
    await pump(tester, start: detail);
    await tester.scrollUntilVisible(
      find.text('Created'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Created'));
    await tester.pumpAndSettle();
    expect(find.text('lead l1'), findsOneWidget);
  });

  testWidgets('the mapping is shown and is not editable here', (tester) async {
    await pump(tester, start: detail);
    expect(find.text('user_column_data.EMAIL → email'), findsOneWidget);
    expect(find.text('The mapping is edited on the web.'), findsOneWidget);
    expect(find.byType(TextField), findsNothing);
  });
}

class _FakeIntakes extends LeadIntakesNotifier {
  _FakeIntakes({required this.offered});

  final bool offered;
  bool built = false;
  final List<String> replaced = [];
  final List<(String, bool)> switched = [];

  @override
  Future<List<LeadIntake>> build() async {
    built = true;
    if (!offered) throw const LeadIntakesNotOffered();
    return [_intake];
  }

  @override
  Future<IntakeKeyResult> replaceKey(String id) async {
    replaced.add(id);
    return (key: _key, error: null);
  }

  @override
  Future<String?> setActive(String id, bool active) async {
    switched.add((id, active));
    return null;
  }
}

class _FakeMailboxes extends MailboxesNotifier {
  _FakeMailboxes(this.given);

  final MailboxesState given;

  @override
  Future<MailboxesState> build() async => given;
}

class _FakeSources extends LeadSourcesNotifier {
  @override
  Future<LeadSourcesAnswer> build() async => const LeadSourcesAnswer(
    sources: [
      LeadSource(id: 's1', key: 'email', label: 'Email'),
      LeadSource(id: 's2', key: 'google ads', label: 'Google ads'),
    ],
  );
}
