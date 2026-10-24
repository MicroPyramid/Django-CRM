import 'dart:convert';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/dashboard_data.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/dashboard_provider.dart';
import 'package:bottle_crm/providers/interactions_provider.dart';
import 'package:bottle_crm/routes/app_routes.dart';
import 'package:bottle_crm/screens/dashboard/dashboard_screen.dart';
import 'package:bottle_crm/screens/leads/leads_list_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

Map<String, dynamic> _row(String id, String first, {Duration? waiting}) => {
  'id': id,
  'first_name': first,
  'last_name': 'Lopez',
  'email': '$first@example.com'.toLowerCase(),
  'phone': '07700 900123',
  'status': 'assigned',
  'created_at': '2026-10-01T09:00:00Z',
  if (waiting != null) ...{
    'is_unanswered': true,
    'waiting_since': DateTime.now().toUtc().subtract(waiting).toIso8601String(),
  },
};

String _page(List<Map<String, dynamic>> rows) => jsonEncode({
  'open_leads': {'open_leads': rows, 'leads_count': rows.length},
  'close_leads': {'close_leads': [], 'leads_count': 0},
});

/// The Unanswered filter on the leads list: offered only by an API that marks
/// each lead answered or not, sent as `unanswered=true`, each card showing its
/// wait, one tap to call, and the home screen's count opening it.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late List<http.Request> sent;
  late Map<String, http.Response Function(http.Request)> routes;
  late DateTime now;

  final leadsPath = Uri.parse(ApiConfig.leads).path;
  final interactionsPath = Uri.parse(ApiConfig.interactions).path;
  const launcher = MethodChannel('plugins.flutter.io/url_launcher');

  setUp(() {
    sent = [];
    now = DateTime(2026, 10, 24, 10);
    routes = {
      'GET $interactionsPath': (_) =>
          http.Response(jsonEncode({'interactions': [], 'count': 0}), 200),
      'POST $interactionsPath': (_) => http.Response('{"id": "new"}', 201),
    };
    ApiService().setClientForTesting(
      MockClient((request) async {
        sent.add(request);
        final answer = routes['${request.method} ${request.url.path}'];
        return answer?.call(request) ?? http.Response('{}', 404);
      }),
    );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(launcher, (_) async => true);
  });

  tearDown(() {
    ApiService().setClientForTesting(http.Client());
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(launcher, null);
  });

  /// Answers the list from the release 2 API: every row says whether it is
  /// answered, and `unanswered=true` narrows to the two waiting leads.
  void serveNewApi() => routes['GET $leadsPath'] = (r) => http.Response(
    r.url.queryParameters['unanswered'] == 'true'
        ? _page([
            _row('l1', 'Maria', waiting: const Duration(hours: 2, minutes: 14)),
            _row('l2', 'Ravi', waiting: const Duration(minutes: 9)),
          ])
        : _page([
            {..._row('l3', 'Ana'), 'is_unanswered': false},
          ]),
    200,
  );

  Future<void> open(WidgetTester tester, {String? view}) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [clockProvider.overrideWithValue(() => now)],
        child: MaterialApp(home: LeadsListScreen(initialView: view)),
      ),
    );
    await tester.pumpAndSettle();
  }

  Iterable<Map<String, String>> leadQueries() => [
    for (final r in sent)
      if (r.method == 'GET' && r.url.path == leadsPath) r.url.queryParameters,
  ];

  testWidgets('an API older than response times gets no Unanswered chip', (
    tester,
  ) async {
    routes['GET $leadsPath'] = (_) =>
        http.Response(_page([_row('l1', 'Maria')]), 200);
    await open(tester);
    expect(find.text('Maria Lopez'), findsOneWidget);
    expect(find.text('Unanswered'), findsNothing);
  });

  testWidgets(
    'the chip asks for unanswered=true and each card shows its wait',
    (tester) async {
      serveNewApi();
      await open(tester);
      expect(find.text('Unanswered'), findsOneWidget);
      expect(find.textContaining('waiting'), findsNothing);

      await tester.tap(find.text('Unanswered'));
      await tester.pumpAndSettle();

      expect(leadQueries().last['unanswered'], 'true');
      expect(find.text('waiting 2 h 14 min'), findsOneWidget);
      expect(find.text('waiting 9 min'), findsOneWidget);
      // In the order the API sent them, which is oldest wait first.
      expect(
        tester.getTopLeft(find.text('Maria Lopez')).dy,
        lessThan(tester.getTopLeft(find.text('Ravi Lopez')).dy),
      );

      await tester.tap(find.text('Unanswered'));
      await tester.pumpAndSettle();
      expect(leadQueries().last.containsKey('unanswered'), isFalse);
      expect(find.text('Ana Lopez'), findsOneWidget);
    },
  );

  testWidgets('an empty Unanswered view says nobody is waiting', (
    tester,
  ) async {
    routes['GET $leadsPath'] = (r) => http.Response(
      r.url.queryParameters['unanswered'] == 'true'
          ? _page([])
          : _page([
              {..._row('l3', 'Ana'), 'is_unanswered': false},
            ]),
      200,
    );
    await open(tester);
    await tester.tap(find.text('Unanswered'));
    await tester.pumpAndSettle();
    expect(find.text('Nobody is waiting'), findsOneWidget);
    // The chip stays, so the filter can be turned off again.
    expect(find.text('Unanswered'), findsOneWidget);
  });

  testWidgets('one tap calls from the list, and the return offers the log', (
    tester,
  ) async {
    serveNewApi();
    await open(tester, view: AppRoutes.viewUnanswered);
    expect(leadQueries().last['unanswered'], 'true');

    await tester.tap(find.byIcon(LucideIcons.phone).first);
    await tester.pump();
    for (final s in [
      AppLifecycleState.inactive,
      AppLifecycleState.hidden,
      AppLifecycleState.paused,
    ]) {
      tester.binding.handleAppLifecycleStateChanged(s);
    }
    now = now.add(const Duration(minutes: 3));
    for (final s in [
      AppLifecycleState.hidden,
      AppLifecycleState.inactive,
      AppLifecycleState.resumed,
    ]) {
      tester.binding.handleAppLifecycleStateChanged(s);
    }
    await tester.pumpAndSettle();

    expect(find.text('Log this call to Maria?'), findsOneWidget);
    final before = leadQueries().length;
    await tester.tap(find.text('Log'));
    await tester.pumpAndSettle();

    final post = sent.lastWhere((r) => r.method == 'POST');
    expect(jsonDecode(post.body)['lead'], 'l1');
    expect(jsonDecode(post.body)['origin'], 'phone_tap');
    // The list is asked again, so an answered lead leaves it.
    expect(leadQueries().length, greaterThan(before));
    expect(leadQueries().last['unanswered'], 'true');
  });

  testWidgets('coming back from a lead refreshes the Unanswered list', (
    tester,
  ) async {
    serveNewApi();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [clockProvider.overrideWithValue(() => now)],
        child: MaterialApp.router(
          routerConfig: GoRouter(
            routes: [
              GoRoute(
                path: '/',
                builder: (_, _) => const LeadsListScreen(
                  initialView: AppRoutes.viewUnanswered,
                ),
              ),
              GoRoute(
                path: '/leads/:id',
                builder: (c, _) =>
                    TextButton(onPressed: c.pop, child: const Text('Back')),
              ),
            ],
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    final before = leadQueries().length;

    await tester.tap(find.text('Maria Lopez'));
    await tester.pumpAndSettle();
    expect(leadQueries().length, before);
    await tester.tap(find.text('Back'));
    await tester.pumpAndSettle();

    expect(leadQueries().length, greaterThan(before));
    expect(leadQueries().last['unanswered'], 'true');
  });

  group('the home screen', () {
    Future<void> openHome(WidgetTester tester, DashboardData data) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authProvider.overrideWith(_FakeAuth.new),
            dashboardProvider.overrideWith(() => _FakeDashboard(data)),
          ],
          child: MaterialApp.router(
            theme: AppTheme.light,
            routerConfig: GoRouter(
              routes: [
                GoRoute(path: '/', builder: (_, _) => const DashboardScreen()),
                GoRoute(
                  path: AppRoutes.leads,
                  builder: (_, s) =>
                      Text('leads view ${s.uri.queryParameters['view']}'),
                ),
              ],
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
    }

    testWidgets('shows the unanswered count, which opens the filtered list', (
      tester,
    ) async {
      await openHome(tester, const DashboardData(unansweredLeads: 3));
      expect(find.text('Unanswered'), findsOneWidget);
      expect(find.text('3'), findsOneWidget);
      await tester.ensureVisible(find.text('Unanswered'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Unanswered'));
      await tester.pumpAndSettle();
      expect(find.text('leads view unanswered'), findsOneWidget);
    });

    testWidgets('none waiting, or an older API, shows no count', (
      tester,
    ) async {
      await openHome(tester, const DashboardData(unansweredLeads: 0));
      expect(find.text('Unanswered'), findsNothing);
      await openHome(tester, const DashboardData());
      expect(find.text('Unanswered'), findsNothing);
    });
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
