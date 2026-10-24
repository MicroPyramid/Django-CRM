import 'dart:convert';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/providers/interactions_provider.dart';
import 'package:bottle_crm/screens/contacts/contact_detail_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:bottle_crm/widgets/common/round_action_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _contact = {
  'id': 'c1',
  'first_name': 'Maria',
  'last_name': 'Lopez',
  'email': 'maria@example.com',
  'phone': '07700 900123',
  'phone_e164': '+447700900123',
  'do_not_call': false,
};

const _enquiry = {
  'id': 'i2',
  'kind': 'enquiry',
  'direction': 'inbound',
  'occurred_at': '2026-10-22T08:00:00Z',
  'body': 'Enquired again about the flat.',
  'logged_by': null,
  'logged_by_details': null,
  'home': 'contact',
  'origin': 'intake',
};

/// The contact screen gains Call, Email, Message and WhatsApp, each offering
/// to log what was done on the return, and its activity. A converted lead's
/// repeat enquiries land here.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late List<http.Request> sent;
  late List<String> launched;
  late Map<String, http.Response Function()> routes;
  late DateTime now;

  final interactionsPath = Uri.parse(ApiConfig.interactions).path;
  final contactPath = Uri.parse('${ApiConfig.contacts}c1/').path;
  const launcher = MethodChannel('plugins.flutter.io/url_launcher');

  void serveContact(Map<String, dynamic> contact) =>
      routes['GET $contactPath'] = () =>
          http.Response(jsonEncode({'contact_obj': contact}), 200);

  setUp(() {
    sent = [];
    launched = [];
    now = DateTime(2026, 10, 24, 10);
    routes = {
      'GET $interactionsPath': () => http.Response(
        jsonEncode({
          'interactions': [_enquiry],
          'count': 1,
        }),
        200,
      ),
      'POST $interactionsPath': () => http.Response('{"id": "new"}', 201),
    };
    serveContact(_contact);
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
          return true;
        });
  });

  tearDown(() {
    ApiService().setClientForTesting(http.Client());
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(launcher, null);
  });

  Finder action(String label) => find.widgetWithText(RoundActionButton, label);

  Future<void> open(WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [clockProvider.overrideWithValue(() => now)],
        child: const MaterialApp(home: ContactDetailScreen(contactId: 'c1')),
      ),
    );
    await tester.pumpAndSettle();
  }

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

  testWidgets('offers the four ways to reach them and the activity', (
    tester,
  ) async {
    await open(tester);
    for (final label in ['Call', 'Email', 'Message', 'WhatsApp']) {
      expect(action(label), findsOneWidget, reason: label);
    }
    expect(find.text('Activity'), findsOneWidget);
    expect(find.text('Log activity'), findsOneWidget);
    expect(find.text('Enquiry via lead webhook'), findsOneWidget);
    final query = sent
        .firstWhere((r) => r.url.path == interactionsPath)
        .url
        .queryParameters;
    expect(query, {'contact': 'c1'});
  });

  testWidgets('an email tap and a return logs an email on the contact', (
    tester,
  ) async {
    await open(tester);
    await tester.tap(action('Email'));
    await tester.pump();
    expect(launched.single, 'mailto:maria@example.com');

    await leaveAndReturn(tester, const Duration(minutes: 5));
    expect(find.text('Log this email to Maria?'), findsOneWidget);
    await tester.tap(find.text('Log'));
    await tester.pumpAndSettle();

    final post = sent.lastWhere((r) => r.method == 'POST');
    final body = jsonDecode(post.body) as Map<String, dynamic>;
    expect(body['kind'], 'email');
    expect(body['contact'], 'c1');
    expect(body['origin'], 'phone_tap');
    expect(body.containsKey('lead'), isFalse);
  });

  testWidgets('WhatsApp greets them by first name', (tester) async {
    await open(tester);
    await tester.tap(action('WhatsApp'));
    await tester.pump();
    expect(launched.single, 'https://wa.me/447700900123?text=Hi%20Maria%2C');
  });

  testWidgets('someone who asked not to be called: Call is off, and says why', (
    tester,
  ) async {
    serveContact({..._contact, 'do_not_call': true});
    await open(tester);
    expect(action('Call'), findsNothing);
    await tester.tap(action('Do not call'));
    await tester.pumpAndSettle();
    expect(launched, isEmpty);
    expect(action('Message'), findsOneWidget);
  });

  testWidgets('no phone_e164, no WhatsApp', (tester) async {
    serveContact({..._contact, 'phone_e164': ''});
    await open(tester);
    expect(action('WhatsApp'), findsNothing);
  });

  testWidgets('an API without interactions (404) shows no activity and '
      'offers no log after a tap', (tester) async {
    routes['GET $interactionsPath'] = () => http.Response('Not found', 404);
    await open(tester);
    expect(find.text('Activity'), findsNothing);
    expect(find.text('Log activity'), findsNothing);

    await tester.tap(action('Call'));
    await tester.pump();
    await leaveAndReturn(tester, const Duration(minutes: 2));
    expect(find.textContaining('Log this'), findsNothing);
  });
}
