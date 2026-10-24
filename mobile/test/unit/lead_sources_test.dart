import 'dart:convert';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/data/models/contact.dart';
import 'package:bottle_crm/data/models/deal.dart';
import 'package:bottle_crm/data/models/lead.dart';
import 'package:bottle_crm/data/models/lead_source.dart';
import 'package:bottle_crm/data/models/web_form.dart';
import 'package:bottle_crm/providers/lead_sources_provider.dart';
import 'package:bottle_crm/providers/org_modules_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// Lead sources became the org's own list. A record keeps whatever key the
/// server sent, known or not, and the fixed seven are only what an older API
/// answers with (404), misspelt `compaign` included because that API stores it.
void main() {
  const listBody = {
    'sources': [
      {
        'id': 's2',
        'key': 'google ads',
        'label': 'Google ads',
        'is_active': true,
        'order': 2,
      },
      {
        'id': 's1',
        'key': 'call',
        'label': 'Call',
        'is_active': true,
        'order': 1,
      },
      {
        'id': 's3',
        'key': 'fax',
        'label': 'Fax',
        'is_active': false,
        'order': 3,
      },
    ],
  };

  group('records keep the key as sent', () {
    test('a lead keeps a source this build never knew', () {
      final lead = Lead.fromJson({
        'id': 'l1',
        'source': 'google ads',
        'source_detail': 'Spring open day',
        'source_ref': 'ad-42',
      });
      expect(lead.source, 'google ads');
      expect(lead.sourceDetail, 'Spring open day');
      expect(lead.sourceRef, 'ad-42');
    });

    test('a lead with no source reads as empty, and compaign stays', () {
      expect(Lead.fromJson({'id': 'l1', 'source': null}).source, '');
      expect(
        Lead.fromJson({'id': 'l1', 'source': 'compaign'}).source,
        'compaign',
      );
    });

    test('a deal keeps its key, and an old API NONE reads as none', () {
      expect(
        Deal.fromJson({'id': 'd1', 'lead_source': 'web form'}).leadSource,
        'web form',
      );
      expect(Deal.fromJson({'id': 'd1', 'lead_source': 'NONE'}).leadSource, '');
      expect(
        Deal.fromJson({'id': 'd1', 'lead_source': 'WEBSITE'}).leadSource,
        'WEBSITE',
      );
    });

    test('a deal sends lead_source only when asked to', () {
      final deal = Deal.fromJson({'id': 'd1', 'lead_source': 'google ads'});
      expect(deal.toJson().containsKey('lead_source'), isFalse);
      expect(deal.toJson(withLeadSource: true)['lead_source'], 'google ads');
    });

    test('a contact reads the three fields and never sends them', () {
      final contact = Contact.fromJson({
        'id': 'c1',
        'source': 'referral',
        'source_detail': 'Ana',
        'source_ref': 'r-1',
      });
      expect(contact.source, 'referral');
      expect(contact.sourceDetail, 'Ana');
      expect(contact.sourceRef, 'r-1');
      final payload = contact.toPayload();
      expect(payload.keys, isNot(contains('source')));
      expect(payload.keys, isNot(contains('source_detail')));
      expect(payload.keys, isNot(contains('source_ref')));
      expect(contact.copyWith(city: 'Pune').source, 'referral');
    });

    test('a web form save never sends its lead source', () {
      final form = WebForm.fromJson({'id': 'f1', 'lead_source': 'web form'});
      expect(form.leadSource, 'web form');
      expect(form.toJson().containsKey('lead_source'), isFalse);
    });
  });

  group('labels and pickers', () {
    final sources = [
      for (final row in listBody['sources']!) LeadSource.fromJson(row),
    ];

    test('a label comes from the list, then the fixed lists, else the key', () {
      expect(leadSourceLabel('google ads', sources), 'Google ads');
      expect(leadSourceLabel('compaign'), 'Campaign');
      expect(leadSourceLabel('EXISTING CUSTOMER'), 'Existing customer');
      expect(leadSourceLabel('WEBSITE'), 'Website');
      expect(leadSourceLabel('trade show', sources), 'trade show');
      expect(leadSourceLabel(''), '');
    });

    test('a picker offers the active ones and keeps the current value', () {
      expect(pickableSources(sources, '').map((s) => s.key), [
        'google ads',
        'call',
      ]);
      final retired = pickableSources(sources, 'fax');
      expect(retired.last.key, 'fax');
      expect(retired.last.pickerLabel, 'Fax (retired)');
      final unknown = pickableSources(sources, 'trade show');
      expect(unknown.last.key, 'trade show');
      expect(unknown.last.pickerLabel, 'trade show');
    });

    test('an older API keeps deals on their uppercase list', () {
      const legacy = LeadSourcesAnswer.legacy();
      expect(legacy.offered, isFalse);
      expect(legacy.pickable('').map((s) => s.key), contains('compaign'));
      expect(legacy.pickableForDeal('').map((s) => s.key), contains('WEBSITE'));
      expect(legacy.dealLabelFor('CALL'), 'Call');
    });
  });

  group('the provider', () {
    late List<http.Request> sent;
    late int status;
    late Object body;

    setUp(() {
      sent = [];
      status = 200;
      body = listBody;
      ApiService().setClientForTesting(
        MockClient((request) async {
          sent.add(request);
          if (request.url.path == Uri.parse(ApiConfig.orgModules).path) {
            return http.Response('', 404);
          }
          if (request.method != 'GET') return http.Response('{}', status);
          return http.Response(jsonEncode(body), status);
        }),
      );
    });

    tearDown(() => ApiService().setClientForTesting(http.Client()));

    ProviderContainer container({bool leadsOn = true}) {
      final c = ProviderContainer(
        overrides: [moduleOnProvider('leads').overrideWithValue(leadsOn)],
      );
      addTearDown(c.dispose);
      return c;
    }

    test('reads the list in the server order', () async {
      final answer = await container().read(leadSourcesProvider.future);
      expect(answer.offered, isTrue);
      expect(answer.sources.map((s) => s.key), ['call', 'google ads', 'fax']);
    });

    test('a 404 falls back to the fixed seven', () async {
      status = 404;
      body = {'detail': 'Not found.'};
      final answer = await container().read(leadSourcesProvider.future);
      expect(answer.offered, isFalse);
      expect(answer.sources.map((s) => s.key), [
        'call',
        'email',
        'existing customer',
        'partner',
        'public relations',
        'compaign',
        'other',
      ]);
    });

    test('a 404 with Leads switched off is still an older server', () async {
      // The list is not tied to Leads, so only a server without it says 404.
      status = 404;
      body = {'detail': 'Not found.'};
      final answer = await container(
        leadsOn: false,
      ).read(leadSourcesProvider.future);
      expect(answer.offered, isFalse);
      expect(answer.sources.map((s) => s.key), contains('compaign'));
    });

    test('a failure is an error, not the fixed list', () async {
      status = 500;
      body = {'detail': 'boom'};
      final c = container();
      await expectLater(c.read(leadSourcesProvider.future), throwsException);
    });

    test('adding posts the label alone', () async {
      final c = container();
      await c.read(leadSourcesProvider.future);
      final error = await c
          .read(leadSourcesProvider.notifier)
          .add('  Spring fair ');
      expect(error, isNull);
      final post = sent.firstWhere((r) => r.method == 'POST');
      expect(post.url.toString(), ApiConfig.leadSources);
      expect(jsonDecode(post.body), {'label': 'Spring fair'});
    });

    test('retiring patches is_active alone', () async {
      final c = container();
      await c.read(leadSourcesProvider.future);
      await c.read(leadSourcesProvider.notifier).setActive('s2', false);
      final patch = sent.firstWhere((r) => r.method == 'PATCH');
      expect(patch.url.toString(), ApiConfig.leadSource('s2'));
      expect(jsonDecode(patch.body), {'is_active': false});
    });

    test('a move posts every key in the new order', () async {
      final c = container();
      await c.read(leadSourcesProvider.future);
      await c.read(leadSourcesProvider.notifier).move('google ads', -1);
      final post = sent.firstWhere((r) => r.method == 'POST');
      expect(post.url.toString(), ApiConfig.leadSourcesOrder);
      expect(jsonDecode(post.body), {
        'keys': ['google ads', 'call', 'fax'],
      });
      expect(
        await c.read(leadSourcesProvider.notifier).move('call', 5),
        'That source cannot move further.',
      );
    });

    test('a member refused says who may change them', () async {
      final c = container();
      await c.read(leadSourcesProvider.future);
      status = 403;
      expect(
        await c.read(leadSourcesProvider.notifier).add('Fair'),
        'Only an admin can change lead sources.',
      );
    });
  });
}
