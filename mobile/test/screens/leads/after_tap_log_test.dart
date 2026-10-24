import 'dart:convert';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/providers/interactions_provider.dart';
import 'package:bottle_crm/screens/leads/lead_detail_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _lead = {
  'id': 'l1',
  'first_name': 'Maria',
  'last_name': 'Lopez',
  'email': 'maria@example.com',
  'phone': '07700 900123',
  'phone_e164': '+447700900123',
  'company_name': 'Harbour Homes',
  'status': 'assigned',
  'created_at': '2026-10-20T09:00:00Z',
};

const _loggedCall = {
  'id': 'i1',
  'kind': 'call',
  'direction': 'outbound',
  'occurred_at': '2026-10-23T09:15:00Z',
  'duration_seconds': 240,
  'duration_estimated': true,
  'outcome': 'no_answer',
  'subject': '',
  'body': '',
  'logged_by': 'p1',
  'logged_by_details': {'id': 'p1', 'name': 'Asha Raman', 'email': 'a@x.io'},
  'home': 'lead',
  'origin': 'phone_tap',
  'can_edit': true,
};

const _enquiry = {
  'id': 'i2',
  'kind': 'enquiry',
  'direction': 'inbound',
  'occurred_at': '2026-10-22T08:00:00Z',
  'duration_seconds': null,
  'duration_estimated': false,
  'outcome': '',
  'subject': '',
  'body': 'Is the flat on Harbour Road still free?',
  'logged_by': null,
  'logged_by_details': null,
  'home': 'lead',
  'origin': 'webform',
  'can_edit': false,
};

/// The after-tap sheet on a lead (Review Focus 5): it appears on the return
/// from Call, WhatsApp, SMS or Email, once per tap, never after two hours, and
/// stays open with a retry when the save fails. The API and the platform's
/// URL launcher are faked; the app's lifecycle is driven through the binding.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late List<http.Request> sent;
  late List<String> launched;
  late bool launchSucceeds;
  late Map<String, http.Response Function()> routes;
  late DateTime now;

  final interactionsPath = Uri.parse(ApiConfig.interactions).path;
  final leadPath = Uri.parse('${ApiConfig.leads}l1/').path;
  const launcher = MethodChannel('plugins.flutter.io/url_launcher');

  setUp(() {
    sent = [];
    launched = [];
    launchSucceeds = true;
    now = DateTime(2026, 10, 24, 10);
    routes = {
      'GET $leadPath': () =>
          http.Response(jsonEncode({'lead_obj': _lead}), 200),
      'GET $interactionsPath': () =>
          http.Response(jsonEncode({'interactions': [], 'count': 0}), 200),
      'POST $interactionsPath': () => http.Response('{"id": "new"}', 201),
    };
    ApiService().setClientForTesting(
      MockClient((request) async {
        sent.add(request);
        final answer = routes['${request.method} ${request.url.path}'];
        return answer?.call() ?? http.Response('{}', 404);
      }),
    );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(launcher, (call) async {
          launched.add((call.arguments as Map)['url'] as String);
          return launchSucceeds;
        });
  });

  tearDown(() {
    ApiService().setClientForTesting(http.Client());
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(launcher, null);
  });

  Future<void> open(WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [clockProvider.overrideWithValue(() => now)],
        child: const MaterialApp(home: LeadDetailScreen(leadId: 'l1')),
      ),
    );
    await tester.pumpAndSettle();
  }

  /// The app goes to the background, [away] passes, and it comes back.
  Future<void> leaveAndReturn(WidgetTester tester, Duration away) async {
    for (final s in [
      AppLifecycleState.inactive,
      AppLifecycleState.hidden,
      AppLifecycleState.paused,
    ]) {
      tester.binding.handleAppLifecycleStateChanged(s);
    }
    now = now.add(away);
    for (final s in [
      AppLifecycleState.hidden,
      AppLifecycleState.inactive,
      AppLifecycleState.resumed,
    ]) {
      tester.binding.handleAppLifecycleStateChanged(s);
    }
    await tester.pumpAndSettle();
  }

  List<Map<String, dynamic>> posts() => [
    for (final r in sent)
      if (r.method == 'POST' && r.url.path == interactionsPath)
        jsonDecode(r.body) as Map<String, dynamic>,
  ];

  testWidgets('after Call and a return it offers to log the call, with the '
      'time away as an estimated length', (tester) async {
    await open(tester);
    final tappedAt = now;
    await tester.tap(find.text('Call'));
    await tester.pump();
    expect(launched.single, startsWith('tel:'));

    await leaveAndReturn(tester, const Duration(minutes: 4, seconds: 10));

    expect(find.text('Log this call to Maria?'), findsOneWidget);
    expect(find.text('Estimated from your time away'), findsOneWidget);
    expect(
      tester
          .widget<TextField>(find.widgetWithText(TextField, 'Duration'))
          .controller!
          .text,
      '4',
    );

    await tester.tap(find.text('Connected'));
    await tester.enterText(
      find.widgetWithText(TextField, 'Note'),
      'Wants a viewing on Friday',
    );
    await tester.tap(find.text('Log'));
    await tester.pumpAndSettle();

    expect(find.text('Log this call to Maria?'), findsNothing);
    expect(posts().single, {
      'kind': 'call',
      'direction': 'outbound',
      'occurred_at': tappedAt.toUtc().toIso8601String(),
      'duration_seconds': 250,
      'duration_estimated': true,
      'outcome': 'connected',
      'body': 'Wants a viewing on Friday',
      'origin': 'phone_tap',
      'lead': 'l1',
    });
  });

  testWidgets('it appears once per tap: the next return shows nothing', (
    tester,
  ) async {
    await open(tester);
    await tester.tap(find.text('Call'));
    await tester.pump();
    await leaveAndReturn(tester, const Duration(minutes: 2));
    expect(find.text('Log this call to Maria?'), findsOneWidget);

    await tester.tap(find.text('Skip'));
    await tester.pumpAndSettle();
    expect(find.text('Log this call to Maria?'), findsNothing);

    await leaveAndReturn(tester, const Duration(minutes: 5));
    expect(find.text('Log this call to Maria?'), findsNothing);
    expect(posts(), isEmpty);
  });

  testWidgets('a return more than two hours after the tap shows nothing, '
      'then or later', (tester) async {
    await open(tester);
    await tester.tap(find.text('Call'));
    await tester.pump();

    await leaveAndReturn(tester, const Duration(hours: 2, minutes: 1));
    expect(find.textContaining('Log this'), findsNothing);

    await leaveAndReturn(tester, const Duration(minutes: 1));
    expect(find.textContaining('Log this'), findsNothing);
  });

  testWidgets('a resume without leaving (a dismissed chooser) shows nothing '
      'yet; the real return does', (tester) async {
    await open(tester);
    await tester.tap(find.text('Email'));
    await tester.pump();
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.inactive);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pumpAndSettle();
    expect(find.textContaining('Log this'), findsNothing);

    await leaveAndReturn(tester, const Duration(minutes: 3));
    expect(find.text('Log this email to Maria?'), findsOneWidget);
    // An email has no length and no call outcome.
    expect(find.widgetWithText(TextField, 'Duration'), findsNothing);
    expect(find.text('Connected'), findsNothing);
  });

  testWidgets('a failed save keeps the sheet open with a retry', (
    tester,
  ) async {
    var attempts = 0;
    routes['POST $interactionsPath'] = () => ++attempts == 1
        ? http.Response('{"detail": "Server busy, try again."}', 503)
        : http.Response('{"id": "new"}', 201);
    await open(tester);
    await tester.tap(find.text('Message'));
    await tester.pump();
    await leaveAndReturn(tester, const Duration(minutes: 1));
    expect(find.text('Log this text message to Maria?'), findsOneWidget);

    await tester.tap(find.text('Log'));
    await tester.pumpAndSettle();
    expect(find.text('Log this text message to Maria?'), findsOneWidget);
    expect(find.text('Server busy, try again.'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);

    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(find.text('Log this text message to Maria?'), findsNothing);
    expect(posts(), hasLength(2));
    expect(posts().last['kind'], 'sms');
  });

  testWidgets('WhatsApp opens wa.me with the greeting and offers its log', (
    tester,
  ) async {
    await open(tester);
    await tester.tap(find.text('WhatsApp'));
    await tester.pump();
    expect(launched.single, 'https://wa.me/447700900123?text=Hi%20Maria%2C');

    await leaveAndReturn(tester, const Duration(minutes: 6));
    expect(find.text('Log this WhatsApp message to Maria?'), findsOneWidget);
    await tester.tap(find.text('Log'));
    await tester.pumpAndSettle();
    expect(posts().single['kind'], 'whatsapp');
    expect(posts().single.containsKey('duration_seconds'), isFalse);
  });

  testWidgets('a lead covered by another screen on the return is not asked '
      'about, and the tap is spent', (tester) async {
    await open(tester);
    await tester.tap(find.text('Call'));
    await tester.pump();
    tester
        .state<NavigatorState>(find.byType(Navigator))
        .push(MaterialPageRoute<void>(builder: (_) => const Text('covering')));
    await tester.pumpAndSettle();

    await leaveAndReturn(tester, const Duration(minutes: 2));
    expect(find.textContaining('Log this'), findsNothing);

    tester.state<NavigatorState>(find.byType(Navigator)).pop();
    await tester.pumpAndSettle();
    await leaveAndReturn(tester, const Duration(minutes: 1));
    expect(find.textContaining('Log this'), findsNothing);
  });

  testWidgets('no phone_e164, no WhatsApp button', (tester) async {
    routes['GET $leadPath'] = () => http.Response(
      jsonEncode({
        'lead_obj': {..._lead, 'phone_e164': ''},
      }),
      200,
    );
    await open(tester);
    expect(find.text('Call'), findsOneWidget);
    expect(find.text('WhatsApp'), findsNothing);
  });

  testWidgets('a launch that fails arms nothing', (tester) async {
    launchSucceeds = false;
    await open(tester);
    await tester.tap(find.text('Call'));
    await tester.pumpAndSettle();
    expect(find.text('Could not open tel'), findsOneWidget);

    await leaveAndReturn(tester, const Duration(minutes: 2));
    expect(find.textContaining('Log this'), findsNothing);
  });

  testWidgets('an API without interactions (404) offers no sheet and no '
      'Log activity', (tester) async {
    routes['GET $interactionsPath'] = () => http.Response('Not found', 404);
    await open(tester);
    await tester.tap(find.text('Call'));
    await tester.pump();
    await leaveAndReturn(tester, const Duration(minutes: 3));
    expect(find.textContaining('Log this'), findsNothing);

    await tester.tap(find.text('Timeline'));
    await tester.pumpAndSettle();
    expect(find.text('Log activity'), findsNothing);
    expect(find.text('Lead created'), findsOneWidget);
    expect(posts(), isEmpty);
  });

  testWidgets('the timeline merges logged calls and enquiries', (tester) async {
    routes['GET $interactionsPath'] = () => http.Response(
      jsonEncode({
        'interactions': [_loggedCall, _enquiry],
        'count': 2,
      }),
      200,
    );
    await open(tester);
    await tester.tap(find.text('Timeline'));
    await tester.pumpAndSettle();

    expect(find.text('Log activity'), findsOneWidget);
    expect(find.text('Outgoing call'), findsOneWidget);
    expect(find.text('Asha Raman · No answer · about 4 min'), findsOneWidget);
    expect(find.text('Enquiry via web form'), findsOneWidget);
    expect(
      find.text('Is the flat on Harbour Road still free?'),
      findsOneWidget,
    );
    final query = sent
        .firstWhere((r) => r.url.path == interactionsPath)
        .url
        .queryParameters;
    expect(query, {'lead': 'l1'});
  });

  testWidgets('Log activity logs a meeting typed in by hand', (tester) async {
    await open(tester);
    await tester.tap(find.text('Timeline'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Log activity'));
    await tester.pumpAndSettle();

    expect(find.text('Log activity'), findsWidgets);
    await tester.tap(find.text('Meeting'));
    await tester.pumpAndSettle();
    expect(find.text('Connected'), findsNothing);
    await tester.enterText(find.widgetWithText(TextField, 'Duration'), '30');
    await tester.tap(find.text('Log'));
    await tester.pumpAndSettle();

    expect(posts().single, {
      'kind': 'meeting',
      'direction': 'outbound',
      'occurred_at': now.toUtc().toIso8601String(),
      'duration_seconds': 1800,
      'duration_estimated': false,
      'origin': 'manual',
      'lead': 'l1',
    });
  });

  testWidgets('editing the estimate sends the typed length, not estimated', (
    tester,
  ) async {
    await open(tester);
    await tester.tap(find.text('Call'));
    await tester.pump();
    await leaveAndReturn(tester, const Duration(minutes: 9));
    await tester.enterText(find.widgetWithText(TextField, 'Duration'), '6');
    await tester.pump();
    expect(find.text('Estimated from your time away'), findsNothing);
    await tester.tap(find.text('Log'));
    await tester.pumpAndSettle();
    expect(posts().single['duration_seconds'], 360);
    expect(posts().single['duration_estimated'], isFalse);
  });
}
