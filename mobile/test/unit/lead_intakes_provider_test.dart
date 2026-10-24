import 'dart:convert';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/data/models/lead_intake.dart';
import 'package:bottle_crm/data/models/mailbox.dart';
import 'package:bottle_crm/providers/lead_intakes_provider.dart';
import 'package:bottle_crm/providers/settings_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _id = '3f2b8c1e-5a4d-4e8b-9c3a-1d2e3f4a5b6c';

const _intake = {
  'id': _id,
  'name': 'Google Ads',
  'preset': 'google_ads',
  'url': 'https://api.example.com/api/public/leads/$_id/',
  'key_hint': 'a1b2',
  'mapping': [
    {'from': 'user_column_data.email', 'to': 'email'},
  ],
  'default_source': 'google ads',
  'source_detail': '',
  'tags': [],
  'assignee': null,
  'is_active': true,
  'last_received_at': '2026-10-20T09:00:00Z',
  'last_error': '',
  'created_at': '2026-10-01T09:00:00Z',
};

/// Lead webhooks and lead addresses on the phone, faked at the HTTP client the
/// way the rest of the suite does. Each answer an older API gives (404, no
/// `generated_domain`) has to read as "not offered", never as an error.
void main() {
  late List<http.Request> sent;
  late Map<String, http.Response Function()> routes;

  setUp(() {
    sent = [];
    routes = {};
    ApiService().setClientForTesting(
      MockClient((request) async {
        sent.add(request);
        final answer = routes['${request.method} ${request.url.path}'];
        return answer?.call() ?? http.Response('{}', 200);
      }),
    );
  });

  tearDown(() => ApiService().setClientForTesting(http.Client()));

  String path(String url) => Uri.parse(url).path;

  ProviderContainer container() {
    final c = ProviderContainer();
    addTearDown(c.dispose);
    return c;
  }

  group('webhooks', () {
    test('reads the list', () async {
      routes['GET ${path(ApiConfig.leadIntakes)}'] = () => http.Response(
        jsonEncode({
          'intakes': [_intake],
        }),
        200,
      );
      final intakes = await container().read(leadIntakesProvider.future);
      final intake = intakes.single;
      expect(intake.name, 'Google Ads');
      expect(intake.presetLabel, 'Google Ads lead form');
      expect(intake.keyHint, 'a1b2');
      expect(intake.mapping.single.to, 'email');
      expect(intake.stateLabel, 'Receiving');
    });

    test('a 404 reads as not offered', () async {
      routes['GET ${path(ApiConfig.leadIntakes)}'] = () =>
          http.Response('<h1>Not Found</h1>', 404);
      final c = container();
      c.listen(leadIntakesProvider, (_, _) {});
      await expectLater(
        c.read(leadIntakesProvider.future),
        throwsA(isA<LeadIntakesNotOffered>()),
      );
      expect(leadIntakesNotOffered(c.read(leadIntakesProvider)), isTrue);
    });

    test('any other failure is an error, not "not offered"', () async {
      routes['GET ${path(ApiConfig.leadIntakes)}'] = () =>
          http.Response('{"detail": "boom"}', 500);
      final c = container();
      c.listen(leadIntakesProvider, (_, _) {});
      await expectLater(c.read(leadIntakesProvider.future), throwsException);
      expect(leadIntakesNotOffered(c.read(leadIntakesProvider)), isFalse);
    });

    test('switching off sends is_active alone', () async {
      routes['GET ${path(ApiConfig.leadIntakes)}'] = () => http.Response(
        jsonEncode({
          'intakes': [_intake],
        }),
        200,
      );
      final c = container();
      await c.read(leadIntakesProvider.future);
      final error = await c
          .read(leadIntakesProvider.notifier)
          .setActive(_id, false);
      expect(error, isNull);
      final patch = sent.singleWhere((r) => r.method == 'PATCH');
      expect(patch.url.toString(), ApiConfig.leadIntake(_id));
      expect(jsonDecode(patch.body), {'is_active': false});
    });

    test('a key replace hands back the new key once', () async {
      routes['GET ${path(ApiConfig.leadIntakes)}'] = () => http.Response(
        jsonEncode({
          'intakes': [_intake],
        }),
        200,
      );
      routes['POST ${path(ApiConfig.leadIntakeKey(_id))}'] = () =>
          http.Response(jsonEncode({..._intake, 'key': 'new-full-key'}), 200);
      final c = container();
      await c.read(leadIntakesProvider.future);
      final result = await c.read(leadIntakesProvider.notifier).replaceKey(_id);
      expect(result.key, 'new-full-key');
      expect(result.error, isNull);
      // Nothing the list holds afterwards carries the key.
      final after = await c.read(leadIntakesProvider.future);
      expect(after.single.keyHint, 'a1b2');
    });

    test('a refused replace is an error with no key', () async {
      routes['POST ${path(ApiConfig.leadIntakeKey(_id))}'] = () =>
          http.Response('{"detail": "You do not have permission."}', 403);
      final result = await container()
          .read(leadIntakesProvider.notifier)
          .replaceKey(_id);
      expect(result.key, isNull);
      expect(result.error, 'You do not have permission.');
    });

    test('deliveries parse, a nested lead included', () async {
      routes['GET ${path(ApiConfig.leadIntakeDeliveries(_id))}'] = () =>
          http.Response(
            jsonEncode({
              'deliveries': [
                {
                  'id': 'e1',
                  'received_at': '2026-10-20T09:00:00Z',
                  'result': 'created',
                  'lead': 'l1',
                  'external_id': 'g-1',
                  'error': '',
                },
                {
                  'id': 'e2',
                  'received_at': '2026-10-19T09:00:00Z',
                  'result': 'rejected',
                  'lead': null,
                  'external_id': '',
                  'error': 'No email or phone.',
                },
                {
                  'id': 'e3',
                  'result': 'merged',
                  'lead': {'id': 'l2'},
                },
              ],
            }),
            200,
          );
      final c = container();
      final rows = await c.read(leadIntakeDeliveriesProvider(_id).future);
      expect(rows.map((d) => d.resultLabel), ['Created', 'Rejected', 'Merged']);
      expect(rows.map((d) => d.leadId), ['l1', null, 'l2']);
      expect(rows[1].error, 'No email or phone.');
    });
  });

  group('lead addresses', () {
    Map<String, dynamic> row(String address, {Map<String, dynamic>? extra}) => {
      'id': address,
      'address': address,
      'provider': 'ses',
      'is_active': true,
      'has_topic_arn': false,
      ...?extra,
    };

    test('an API with lead addresses says so, and names its domain', () async {
      routes['GET ${path(ApiConfig.mailboxes)}'] = () => http.Response(
        jsonEncode({
          'mailboxes': [
            row(
              'acme-x1y2z3@in.example.com',
              extra: {'creates': 'leads', 'lead_source': 'email'},
            ),
            row('help@acme.com', extra: {'creates': 'tickets'}),
          ],
          'totals': {'count': 2},
          'generated_domain': 'in.example.com',
        }),
        200,
      );
      final state = await container().read(mailboxesProvider.future);
      expect(state.leadsOffered, isTrue);
      expect(state.generatedDomain, 'in.example.com');
      final made = state.mailboxes.firstWhere((m) => m.createsLeads);
      // No topic pin of its own, and still delivering: the server routes it.
      expect(made.isGenerated, isTrue);
      expect(made.deliveryLabel, 'Creating leads');
      expect(state.deliveringLeads, 1);
      expect(state.delivering, 0);
    });

    test('an older API offers no lead addresses', () async {
      routes['GET ${path(ApiConfig.mailboxes)}'] = () => http.Response(
        jsonEncode({
          'mailboxes': [row('help@acme.com')],
          'totals': {'count': 1},
        }),
        200,
      );
      final state = await container().read(mailboxesProvider.future);
      expect(state.leadsOffered, isFalse);
      expect(state.generatedDomain, isNull);
      expect(state.mailboxes.single.createsLeads, isFalse);
    });
  });

  group('mailboxPayload', () {
    test('a generated address sends no address and no topic', () {
      final body = mailboxPayload(
        address: null,
        provider: 'mailgun',
        defaultPriority: 'Normal',
        topicArn: 'arn:aws:sns:us-east-1:123456789012:x',
        generateAddress: true,
        creates: 'leads',
        leadSource: 'email',
        leadSourceDetail: ' Zillow ',
      );
      expect(body['generate_address'], isTrue);
      expect(body['provider'], 'ses');
      expect(body.containsKey('address'), isFalse);
      expect(body.containsKey('topic_arn'), isFalse);
      expect(body['creates'], 'leads');
      expect(body['lead_source'], 'email');
      expect(body['lead_source_detail'], 'Zillow');
    });

    test('a ticket address carries none of the lead keys', () {
      final body = mailboxPayload(
        address: 'Help@Acme.com',
        provider: 'ses',
        defaultPriority: 'Normal',
      );
      expect(body['address'], 'help@acme.com');
      for (final key in [
        'creates',
        'lead_source',
        'lead_source_detail',
        'generate_address',
      ]) {
        expect(body.containsKey(key), isFalse, reason: key);
      }
    });
  });

  test('preset labels name every preset the API offers', () {
    for (final preset in ['generic', 'google_ads', 'tally', 'gravity_forms']) {
      expect(LeadIntake(id: 'x', preset: preset).presetLabel, isNotEmpty);
    }
  });
}
