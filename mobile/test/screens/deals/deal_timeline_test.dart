import 'dart:convert';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/screens/deals/deal_detail_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _deal = {
  'id': 'd1',
  'name': 'Harbour Road flat',
  'stage': 'QUALIFICATION',
  'amount': '250000',
  'currency': 'GBP',
  'created_at': '2026-10-01T09:00:00Z',
};

const _meeting = {
  'id': 'i1',
  'kind': 'meeting',
  'direction': 'outbound',
  'occurred_at': '2026-10-23T15:00:00Z',
  'duration_seconds': 1800,
  'duration_estimated': false,
  'outcome': '',
  'subject': 'Viewing',
  'body': 'Liked the balcony.',
  'logged_by': 'p1',
  'logged_by_details': {'id': 'p1', 'name': 'Asha Raman', 'email': 'a@x.io'},
  'home': 'contact',
  'origin': 'manual',
};

/// A deal's Activity tab lists the interactions linked to it, which a
/// converted lead's history reaches through the new deal link.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late List<http.Request> sent;
  late http.Response Function() interactions;

  final interactionsPath = Uri.parse(ApiConfig.interactions).path;
  final dealPath = Uri.parse('${ApiConfig.opportunities}d1/').path;

  setUp(() {
    sent = [];
    interactions = () => http.Response(
      jsonEncode({
        'interactions': [_meeting],
        'count': 1,
      }),
      200,
    );
    ApiService().setClientForTesting(
      MockClient((request) async {
        sent.add(request);
        if (request.url.path == dealPath) {
          return http.Response(jsonEncode({'opportunity_obj': _deal}), 200);
        }
        if (request.url.path == interactionsPath) return interactions();
        return http.Response('{}', 404);
      }),
    );
  });

  tearDown(() => ApiService().setClientForTesting(http.Client()));

  Future<void> openActivity(WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: DealDetailScreen(dealId: 'd1')),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Activity'));
    await tester.pumpAndSettle();
  }

  testWidgets('merges the deal\'s interactions into its timeline', (
    tester,
  ) async {
    await openActivity(tester);
    expect(find.text('Meeting'), findsOneWidget);
    expect(find.text('Asha Raman · 30 min · Viewing'), findsOneWidget);
    expect(find.text('Liked the balcony.'), findsOneWidget);
    expect(find.text('Log activity'), findsOneWidget);
    final query = sent
        .firstWhere((r) => r.url.path == interactionsPath)
        .url
        .queryParameters;
    expect(query, {'opportunity': 'd1'});
  });

  testWidgets('an API without interactions (404) keeps the old timeline', (
    tester,
  ) async {
    interactions = () => http.Response('Not found', 404);
    await openActivity(tester);
    expect(find.text('Log activity'), findsNothing);
    expect(find.text('Meeting'), findsNothing);
    expect(find.text('Deal created'), findsOneWidget);
  });
}
