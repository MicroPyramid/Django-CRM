import 'dart:convert';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/data/models/contact.dart';
import 'package:bottle_crm/data/models/dashboard_data.dart';
import 'package:bottle_crm/data/models/interaction.dart';
import 'package:bottle_crm/data/models/lead.dart';
import 'package:bottle_crm/providers/interactions_provider.dart';
import 'package:bottle_crm/providers/leads_provider.dart';
import 'package:bottle_crm/services/after_tap.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _leadId = '3f2b8c1e-5a4d-4e8b-9c3a-1d2e3f4a5b6c';

/// An interaction exactly as the release 2 contract describes it.
const _call = {
  'id': 'i1',
  'kind': 'call',
  'direction': 'outbound',
  'occurred_at': '2026-10-24T09:15:00Z',
  'duration_seconds': 260,
  'duration_estimated': true,
  'outcome': 'no_answer',
  'subject': '',
  'body': 'Left no message.',
  'logged_by': 'p1',
  'logged_by_details': {'id': 'p1', 'name': 'Asha Raman', 'email': 'a@x.io'},
  'participants': [],
  'lead': _leadId,
  'contact': null,
  'account': null,
  'opportunity': null,
  'case': null,
  'home': 'lead',
  'origin': 'phone_tap',
  'external_id': '',
  'created_at': '2026-10-24T09:20:00Z',
  'can_edit': true,
};

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
        return answer?.call() ?? http.Response('{}', 404);
      }),
    );
  });

  tearDown(() => ApiService().setClientForTesting(http.Client()));

  final listPath = Uri.parse(ApiConfig.interactions).path;
  const lead = (home: InteractionHome.lead, id: _leadId);

  ProviderContainer container() {
    final c = ProviderContainer();
    addTearDown(c.dispose);
    return c;
  }

  group('parsing', () {
    test('reads every field the phone shows', () {
      final i = Interaction.fromJson(_call);
      expect(i.kind, InteractionKind.call);
      expect(i.inbound, isFalse);
      expect(i.occurredAt, DateTime.utc(2026, 10, 24, 9, 15));
      expect(i.durationSeconds, 260);
      expect(i.durationEstimated, isTrue);
      expect(CallOutcome.parse(i.outcome), CallOutcome.noAnswer);
      expect(i.body, 'Left no message.');
      expect(i.loggedByName, 'Asha Raman');
      expect(i.origin, 'phone_tap');
      expect(i.canEdit, isTrue);
    });

    test('an enquiry has no logger and is inbound', () {
      final i = Interaction.fromJson({
        ..._call,
        'kind': 'enquiry',
        'direction': 'inbound',
        'duration_seconds': null,
        'duration_estimated': false,
        'outcome': '',
        'logged_by': null,
        'logged_by_details': null,
        'origin': 'webform',
      });
      expect(i.kind, InteractionKind.enquiry);
      expect(i.inbound, isTrue);
      expect(i.loggedByName, isNull);
      expect(i.durationSeconds, isNull);
    });

    test('a kind added later is kept as sent, not dropped', () {
      final i = Interaction.fromJson({..._call, 'kind': 'video_call'});
      expect(i.kind, isNull);
      expect(i.kindValue, 'video_call');
      expect(i.title, 'Activity');
    });

    test('titles and lengths read as the web writes them', () {
      Interaction of(Map<String, dynamic> extra) =>
          Interaction.fromJson({..._call, ...extra});
      expect(of({}).title, 'Outgoing call');
      expect(of({'direction': 'inbound'}).title, 'Incoming call');
      expect(of({'kind': 'email'}).title, 'Email sent');
      expect(
        of({'kind': 'sms', 'direction': 'inbound'}).title,
        'Text received',
      );
      expect(of({'kind': 'whatsapp'}).title, 'WhatsApp sent');
      expect(of({'kind': 'meeting'}).title, 'Meeting');
      expect(
        of({'kind': 'enquiry', 'origin': 'webform'}).title,
        'Enquiry via web form',
      );
      expect(
        of({'kind': 'enquiry', 'origin': 'intake'}).title,
        'Enquiry via lead webhook',
      );
      expect(
        of({'kind': 'enquiry', 'origin': 'zapier'}).title,
        'Enquiry via zapier',
      );
      expect(of({}).durationText, 'about 4 min');
      expect(of({'duration_estimated': false}).durationText, '4 min');
      expect(of({'duration_seconds': null}).durationText, isNull);
    });
  });

  group('what a log sends', () {
    final tapped = DateTime.utc(2026, 10, 24, 9, 15);

    test('a call after a tap: phone_tap, outcome, estimated length', () {
      final body = InteractionDraft(
        target: lead,
        kind: InteractionKind.call,
        occurredAt: tapped,
        origin: 'phone_tap',
        durationSeconds: 240,
        durationEstimated: true,
        outcome: CallOutcome.connected,
        body: '  Wants a viewing on Friday. ',
      ).toJson();
      expect(body, {
        'kind': 'call',
        'direction': 'outbound',
        'occurred_at': '2026-10-24T09:15:00.000Z',
        'duration_seconds': 240,
        'duration_estimated': true,
        'outcome': 'connected',
        'body': 'Wants a viewing on Friday.',
        'origin': 'phone_tap',
        'lead': _leadId,
      });
    });

    test('a call with no outcome chosen sends none, leaving the default', () {
      final body = InteractionDraft(
        target: lead,
        kind: InteractionKind.call,
        occurredAt: tapped,
        origin: 'phone_tap',
      ).toJson();
      expect(body.containsKey('outcome'), isFalse);
      expect(body.containsKey('duration_seconds'), isFalse);
      expect(body.containsKey('body'), isFalse);
    });

    test('an email sends no outcome and no length', () {
      final body = InteractionDraft(
        target: (home: InteractionHome.contact, id: 'c1'),
        kind: InteractionKind.email,
        occurredAt: tapped,
        origin: 'phone_tap',
        outcome: CallOutcome.busy,
      ).toJson();
      expect(body.containsKey('outcome'), isFalse);
      expect(body.containsKey('duration_seconds'), isFalse);
      expect(body['contact'], 'c1');
      expect(body.containsKey('lead'), isFalse);
    });

    test('a ticket is sent as `case`, the API name', () {
      final body = InteractionDraft(
        target: (home: InteractionHome.ticket, id: 't1'),
        kind: InteractionKind.meeting,
        occurredAt: tapped,
        origin: 'manual',
        durationSeconds: 1800,
      ).toJson();
      expect(body['case'], 't1');
      expect(body['duration_estimated'], isFalse);
    });

    test('a local time goes out as UTC', () {
      final local = DateTime(2026, 10, 24, 14, 45);
      final body = InteractionDraft(
        target: lead,
        kind: InteractionKind.sms,
        occurredAt: local,
        origin: 'phone_tap',
      ).toJson();
      expect(body['occurred_at'], local.toUtc().toIso8601String());
      expect((body['occurred_at'] as String).endsWith('Z'), isTrue);
    });
  });

  group('the API', () {
    test('lists one record\'s interactions by its filter', () async {
      routes['GET $listPath'] = () => http.Response(
        jsonEncode({
          'interactions': [_call],
          'count': 73,
        }),
        200,
      );
      final answer = await container().read(
        recordInteractionsProvider(lead).future,
      );
      expect(answer.offered, isTrue);
      expect(answer.items.single.id, 'i1');
      expect(answer.count, 73);
      expect(sent.single.url.queryParameters, {'lead': _leadId});
    });

    test('a 404 reads as not offered, not as an error', () async {
      routes['GET $listPath'] = () => http.Response('<h1>Not Found</h1>', 404);
      final answer = await container().read(
        recordInteractionsProvider(lead).future,
      );
      expect(answer.offered, isFalse);
      expect(answer.items, isEmpty);
    });

    test('any other failure is an error', () async {
      routes['GET $listPath'] = () => http.Response('{"detail": "x"}', 500);
      final c = container();
      c.listen(recordInteractionsProvider(lead), (_, _) {});
      await expectLater(
        c.read(recordInteractionsProvider(lead).future),
        throwsException,
      );
    });

    test('a log posts the draft and answers null', () async {
      routes['POST $listPath'] = () => http.Response(jsonEncode(_call), 201);
      final error = await InteractionsApi().log(
        InteractionDraft(
          target: lead,
          kind: InteractionKind.call,
          occurredAt: DateTime.utc(2026, 10, 24, 9, 15),
          origin: 'phone_tap',
        ),
      );
      expect(error, isNull);
      final post = sent.single;
      expect(post.method, 'POST');
      expect(post.url.toString(), ApiConfig.interactions);
      expect(jsonDecode(post.body)['lead'], _leadId);
    });

    test('a refused log says why', () async {
      routes['POST $listPath'] = () => http.Response(
        jsonEncode({
          'occurred_at': ['Cannot be more than 5 minutes in the future.'],
        }),
        400,
      );
      final error = await InteractionsApi().log(
        InteractionDraft(
          target: lead,
          kind: InteractionKind.call,
          occurredAt: DateTime.utc(2026, 10, 24, 9, 15),
          origin: 'phone_tap',
        ),
      );
      expect(error, contains('5 minutes in the future'));
    });

    test('a log offline says so', () async {
      ApiService().setClientForTesting(
        MockClient((_) async => throw http.ClientException('no route')),
      );
      final error = await InteractionsApi().log(
        InteractionDraft(
          target: lead,
          kind: InteractionKind.sms,
          occurredAt: DateTime.utc(2026, 10, 24, 9, 15),
          origin: 'phone_tap',
        ),
      );
      expect(error, isNotNull);
      expect(error, isNotEmpty);
    });
  });

  group('the tap tracker', () {
    final tappedAt = DateTime(2026, 10, 24, 10);
    PendingTap tap() => PendingTap(
      kind: InteractionKind.call,
      target: lead,
      personName: 'Maria',
      tappedAt: tappedAt,
    );
    final screen = Object();

    /// Leaves the app, then comes back [after] the tap.
    PendingTap? leaveAndReturn(
      TapLogTracker t,
      Duration after, {
      Object? owner,
    }) {
      final now = tappedAt.add(after);
      for (final s in [
        AppLifecycleState.inactive,
        AppLifecycleState.hidden,
        AppLifecycleState.paused,
        AppLifecycleState.hidden,
        AppLifecycleState.inactive,
      ]) {
        expect(t.onState(s, now, owner: owner ?? screen), isNull);
      }
      return t.onState(AppLifecycleState.resumed, now, owner: owner ?? screen);
    }

    test('offers the tap on the first return', () {
      final t = TapLogTracker()..arm(tap(), owner: screen);
      expect(
        leaveAndReturn(t, const Duration(minutes: 4))?.kind,
        InteractionKind.call,
      );
    });

    test('offers it once, never on a later return', () {
      final t = TapLogTracker()..arm(tap(), owner: screen);
      expect(leaveAndReturn(t, const Duration(minutes: 4)), isNotNull);
      expect(leaveAndReturn(t, const Duration(minutes: 9)), isNull);
      expect(t.pending, isNull);
    });

    test('a return after two hours drops it for good', () {
      final t = TapLogTracker()..arm(tap(), owner: screen);
      expect(leaveAndReturn(t, const Duration(hours: 2, seconds: 1)), isNull);
      expect(t.pending, isNull);
      expect(leaveAndReturn(t, const Duration(hours: 2, minutes: 5)), isNull);
    });

    test('exactly two hours is still inside the window', () {
      final t = TapLogTracker()..arm(tap(), owner: screen);
      expect(leaveAndReturn(t, const Duration(hours: 2)), isNotNull);
    });

    test('a resume without leaving keeps it waiting', () {
      final t = TapLogTracker()..arm(tap(), owner: screen);
      final now = tappedAt.add(const Duration(seconds: 3));
      expect(t.onState(AppLifecycleState.inactive, now, owner: screen), isNull);
      expect(t.onState(AppLifecycleState.resumed, now, owner: screen), isNull);
      expect(t.pending, isNotNull);
      expect(leaveAndReturn(t, const Duration(minutes: 3)), isNotNull);
    });

    test('a resume without leaving after the grace drops it', () {
      final t = TapLogTracker()..arm(tap(), owner: screen);
      final late = tappedAt.add(const Duration(seconds: 4));
      expect(t.onState(AppLifecycleState.resumed, late, owner: screen), isNull);
      expect(t.pending, isNull);
      expect(leaveAndReturn(t, const Duration(minutes: 3)), isNull);
    });

    test('only the screen that armed it is offered it', () {
      final other = Object();
      final t = TapLogTracker()..arm(tap(), owner: screen);
      expect(
        leaveAndReturn(t, const Duration(minutes: 2), owner: other),
        isNull,
      );
      expect(
        t.onState(
          AppLifecycleState.resumed,
          tappedAt.add(const Duration(minutes: 2)),
          owner: screen,
        ),
        isNotNull,
      );
    });

    test('a newer tap replaces the older one', () {
      final other = Object();
      final t = TapLogTracker()
        ..arm(tap(), owner: screen)
        ..arm(
          PendingTap(
            kind: InteractionKind.email,
            target: lead,
            personName: 'Maria',
            tappedAt: tappedAt,
          ),
          owner: other,
        );
      expect(leaveAndReturn(t, const Duration(minutes: 1)), isNull);
      expect(t.pending?.kind, InteractionKind.email);
    });

    test('a screen drops only its own tap', () {
      final t = TapLogTracker()..arm(tap(), owner: screen);
      t.disarm(owner: Object());
      expect(t.pending, isNotNull);
      t.disarm(owner: screen);
      expect(t.pending, isNull);
    });

    test('a clock set back before the tap offers nothing', () {
      final t = TapLogTracker()..arm(tap(), owner: screen);
      expect(leaveAndReturn(t, const Duration(minutes: -30)), isNull);
    });
  });

  group('WhatsApp', () {
    test('the link is the E.164 digits with the greeting', () {
      expect(
        whatsAppUri('+447700900123', 'Maria').toString(),
        'https://wa.me/447700900123?text=Hi%20Maria%2C',
      );
    });

    test('a name outside ASCII is percent-encoded', () {
      expect(
        whatsAppUri('+34600111222', 'José').toString(),
        'https://wa.me/34600111222?text=Hi%20Jos%C3%A9%2C',
      );
    });

    test('no first name still greets', () {
      expect(
        whatsAppUri('+447700900123', ' ').toString(),
        'https://wa.me/447700900123?text=Hi%2C',
      );
    });

    test('no E.164 number, no link', () {
      expect(whatsAppUri('', 'Maria'), isNull);
      expect(whatsAppUri(null, 'Maria'), isNull);
      expect(whatsAppUri('447700900123', 'Maria'), isNull);
      expect(whatsAppUri('+0447700900', 'Maria'), isNull);
      expect(whatsAppUri('+44 7700 900123', 'Maria'), isNull);
    });
  });

  group('records', () {
    test('a lead carries phone_e164 and its wait', () {
      final l = Lead.fromJson({
        'id': 'l1',
        'phone': '07700 900123',
        'phone_e164': '+447700900123',
        'is_unanswered': true,
        'waiting_since': '2026-10-24T07:00:00Z',
      });
      expect(l.phoneE164, '+447700900123');
      expect(l.isUnanswered, isTrue);
      expect(l.waitingSince, DateTime.utc(2026, 10, 24, 7));
      final copy = l.copyWith(comments: const []);
      expect(copy.phoneE164, '+447700900123');
      expect(copy.isUnanswered, isTrue);
      expect(copy.waitingSince, l.waitingSince);
    });

    test('an older API leaves the lead\'s answer unknown', () {
      final l = Lead.fromJson({'id': 'l1'});
      expect(l.phoneE164, '');
      expect(l.isUnanswered, isNull);
      expect(l.waitingSince, isNull);
    });

    test('a contact carries phone_e164 and never sends it', () {
      final c = Contact.fromJson({
        'id': 'c1',
        'first_name': 'Maria',
        'phone_e164': '+447700900123',
      });
      expect(c.phoneE164, '+447700900123');
      expect(c.copyWith(title: 'CEO').phoneE164, '+447700900123');
      expect(c.toPayload().containsKey('phone_e164'), isFalse);
    });

    test('the home screen reads the unanswered count', () {
      final d = DashboardData.fromJson({
        'unanswered_leads': {'count': 3, 'oldest_since': '2026-10-24T07:00Z'},
      });
      expect(d.unansweredLeads, 3);
      expect(DashboardData.fromJson(const {}).unansweredLeads, isNull);
    });
  });

  group('the unanswered filter', () {
    test('is sent as unanswered=true and combines with the others', () async {
      routes['GET ${Uri.parse(ApiConfig.leads).path}'] = () => http.Response(
        jsonEncode({
          'open_leads': {'open_leads': [], 'leads_count': 0},
          'close_leads': {'close_leads': []},
        }),
        200,
      );
      final c = container();
      await c.read(leadsProvider.future);
      await c
          .read(leadsProvider.notifier)
          .setFilters(
            const LeadFilters(assignedToId: 'p1').withUnanswered(true),
          );
      final query = sent.last.url.queryParameters;
      expect(query['unanswered'], 'true');
      expect(query['assigned_to'], 'p1');
    });

    test('every other filter change keeps it', () {
      final f = LeadFilters.unansweredOnly();
      expect(f.isActive, isTrue);
      expect(f.withSearch('x').unanswered, isTrue);
      expect(f.withStatus(LeadStatus.assigned).unanswered, isTrue);
      expect(f.withSource('email').unanswered, isTrue);
      expect(f.withRating(LeadRating.hot).unanswered, isTrue);
      expect(f.withAssignee(id: 'p1').unanswered, isTrue);
      expect(f.withTag(id: 't1').unanswered, isTrue);
      expect(f.withNextFollowUp('2026-10-24').unanswered, isTrue);
      expect(f.cleared(tag: true).unanswered, isTrue);
      expect(f.cleared(unanswered: true).unanswered, isFalse);
      expect(f.cleared(unanswered: true).isEmpty, isTrue);
    });

    test('a list is offered the filter only when rows say answered or not', () {
      Lead row(Map<String, dynamic> extra) =>
          Lead.fromJson({'id': 'l1', ...extra});
      expect(LeadsListData(leads: [row({})]).offersUnanswered, isFalse);
      expect(
        LeadsListData(
          leads: [
            row({'is_unanswered': false}),
          ],
        ).offersUnanswered,
        isTrue,
      );
    });
  });

  test('shortElapsed names a length or a wait to the unit that matters', () {
    expect(shortElapsed(const Duration(seconds: 45)), 'under a minute');
    expect(shortElapsed(const Duration(minutes: 14, seconds: 59)), '14 min');
    expect(shortElapsed(const Duration(hours: 2, minutes: 14)), '2 h 14 min');
    expect(shortElapsed(const Duration(hours: 3)), '3 h');
    expect(shortElapsed(const Duration(days: 3, hours: 4)), '3 d 4 h');
    expect(shortElapsed(const Duration(days: 2)), '2 d');
    expect(shortElapsed(const Duration(minutes: -5)), 'under a minute');
  });
}
