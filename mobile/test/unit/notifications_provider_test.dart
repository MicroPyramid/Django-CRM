import 'dart:convert';

import 'package:bottle_crm/data/models/app_notification.dart';
import 'package:bottle_crm/providers/notifications_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

/// The notification feed, module 14.
///
/// Three things are worth pinning.
///
/// **The stored link is data, not a destination.** `Notification.link` is a
/// column, and a column can hold anything that was ever written to it. It is
/// matched against the two ticket shapes and otherwise ignored, so no row can
/// send the app somewhere of its own choosing. Rows written before the
/// producer was fixed carry `/cases/<id>`, which no client has ever served,
/// which is why both spellings resolve.
///
/// **The badge is the server's count, not the page's.** `unread_count` is
/// computed over the whole feed while `results` is capped at the limit, so
/// counting rows would under-report exactly when there is most to report.
///
/// **Optimism has to be reversible.** Marking read clears the dot before the
/// server answers, so a refusal has to put it back or the screen settles on a
/// state the server never accepted.
class _FakeClient extends http.BaseClient {
  _FakeClient({this.body = '{}'});

  int status = 200;
  String body;
  final List<http.BaseRequest> sent = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    await request.finalize().toBytes();
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

/// Two unread and one read, with `unread_count` deliberately larger than the
/// unread rows present: the feed is capped, the count is not.
const _feed = '''
{
  "count": 3,
  "unread_count": 7,
  "results": [
    {
      "id": "n-mention",
      "verb": "case.mentioned",
      "actor": {"id": "u-1", "name": "Ada Lovelace", "email": "ada@example.com"},
      "entity_type": "Case",
      "entity_id": "case-9",
      "entity_name": "Printer on fire",
      "data": {"comment_excerpt": "can you take a look?"},
      "link": "/tickets/case-9",
      "read_at": null,
      "created_at": "2026-08-07T09:00:00Z"
    },
    {
      "id": "n-legacy",
      "verb": "case.commented",
      "actor": null,
      "entity_type": "Case",
      "entity_id": "case-4",
      "entity_name": "Old ticket",
      "data": {},
      "link": "/cases/case-4",
      "read_at": null,
      "created_at": "2026-08-06T09:00:00Z"
    },
    {
      "id": "n-read",
      "verb": "case.sla_breached",
      "actor": {"id": "u-2", "name": "Grace", "email": "grace@example.com"},
      "entity_type": "Case",
      "entity_id": "case-1",
      "entity_name": "Handled",
      "data": {},
      "link": "/tickets/case-1",
      "read_at": "2026-08-06T10:00:00Z",
      "created_at": "2026-08-05T09:00:00Z"
    }
  ]
}
''';

void main() {
  late ProviderContainer container;
  late _FakeClient client;

  setUp(() {
    client = _FakeClient(body: _feed);
    ApiService().setClientForTesting(client);
    container = ProviderContainer();
  });

  tearDown(() => container.dispose());

  group('the link is parsed, never followed', () {
    test('a current /tickets/ link resolves', () {
      expect(_withLink('/tickets/case-9').ticketId, 'case-9');
    });

    test('product support resolves without becoming a CRM ticket', () {
      final notification = _withLink('/help/support-9');
      expect(notification.ticketId, isNull);
      expect(notification.destinationPath, '/help/support-9');
    });

    test('a legacy /support/ link resolves to the renamed help page', () {
      // Written before the page was renamed from support to help.
      final notification = _withLink('/support/support-9');
      expect(notification.ticketId, isNull);
      expect(notification.destinationPath, '/help/support-9');
    });

    test('a legacy /cases/ link resolves to the same ticket', () {
      // Written before the producer was fixed. No client serves `/cases`, so
      // leaving these unresolved would mean every old row opens nothing.
      expect(_withLink('/cases/case-9').ticketId, 'case-9');
    });

    test('a trailing slash is accepted', () {
      expect(_withLink('/tickets/case-9/').ticketId, 'case-9');
    });

    test('an absolute URL does not resolve', () {
      expect(_withLink('https://evil.example/tickets/case-9').ticketId, isNull);
    });

    test('a javascript: URL does not resolve', () {
      expect(_withLink('javascript:alert(1)').ticketId, isNull);
    });

    test('a deeper path does not resolve', () {
      // `/tickets/case-9/edit` is a different screen with different rules, and
      // a notification is not the thing that decides you may edit.
      expect(_withLink('/tickets/case-9/edit').ticketId, isNull);
    });

    test('a missing link does not resolve', () {
      expect(_withLink(null).ticketId, isNull);
    });
  });

  group('reading the feed', () {
    test('the badge is the server\'s count, not the rows fetched', () async {
      final feed = await container.read(notificationsProvider.future);

      expect(feed.items, hasLength(3));
      expect(feed.unread, hasLength(2));
      // 7, not 2. The feed is capped at the limit; the count is not.
      expect(feed.unreadCount, 7);
      expect(container.read(unreadNotificationCountProvider), 7);
    });

    test(
      'a notification with no actor keeps a null name for the system copy',
      () async {
        final feed = await container.read(notificationsProvider.future);

        expect(feed.items[0].actorName, 'Ada Lovelace');
        expect(feed.items[1].actorName, isNull);
      },
    );

    test('the comment excerpt is carried through as text', () async {
      final feed = await container.read(notificationsProvider.future);

      expect(feed.items[0].commentExcerpt, 'can you take a look?');
      expect(feed.items[1].commentExcerpt, isNull);
    });

    test(
      'rows with the dead prefix are counted once, not flagged per row',
      () async {
        final feed = await container.read(notificationsProvider.future);

        expect(feed.legacyLinkCount, 1);
      },
    );

    test('the badge is zero while nothing has loaded', () {
      expect(container.read(unreadNotificationCountProvider), 0);
    });

    test('a failure is a failure, not an empty feed', () async {
      final noRetry = ProviderContainer(retry: (_, _) => null);
      addTearDown(noRetry.dispose);
      client.status = 500;
      client.body = '{}';

      await expectLater(
        noRetry.read(notificationsProvider.future),
        throwsA(isA<Exception>()),
      );
    });
  });

  group('verbs', () {
    test('the two the backend produces get their own copy', () async {
      final feed = await container.read(notificationsProvider.future);

      expect(feed.items[0].verbPhrase, 'mentioned you on');
      expect(feed.items[0].isKnownVerb, isTrue);
      expect(feed.items[1].verbPhrase, 'commented on');
    });

    test(
      'one nothing dispatches reads as a sentence, not an identifier',
      () async {
        final feed = await container.read(notificationsProvider.future);

        // `case.sla_breached` has no producer. It renders rather than being
        // dropped, because a new producer ships before its copy does.
        expect(feed.items[2].verbPhrase, 'sla breached');
        expect(feed.items[2].isKnownVerb, isFalse);
      },
    );

    test('only verbs with active producers are declared', () {
      expect(producedVerbs, [
        'case.mentioned',
        'case.commented',
        'support.replied',
        'support.status_changed',
      ]);
    });

    test('support updates are attributed to BottleCRM Support', () {
      final notification = AppNotification(
        id: 'support-1',
        verb: 'support.replied',
        createdAt: DateTime.utc(2026, 8, 8),
      );

      expect(notification.displayActorName, 'BottleCRM Support');
    });
  });

  group('marking read', () {
    test(
      'the dot clears before the server answers, and the badge drops',
      () async {
        await container.read(notificationsProvider.future);

        await container
            .read(notificationsProvider.notifier)
            .markRead('n-mention');

        final feed = container.read(notificationsProvider).value!;
        expect(feed.items[0].isUnread, isFalse);
        expect(feed.unreadCount, 6);
        final post = client.sent.firstWhere((r) => r.method == 'POST');
        expect(post.url.path, endsWith('/notifications/n-mention/read/'));
      },
    );

    test('a refusal puts the dot back', () async {
      await container.read(notificationsProvider.future);
      client.status = 404;
      client.body = '{"detail": "Not found."}';

      final response = await container
          .read(notificationsProvider.notifier)
          .markRead('n-mention');

      expect(response.success, isFalse);
      final feed = container.read(notificationsProvider).value!;
      expect(feed.items[0].isUnread, isTrue);
      expect(feed.unreadCount, 7);
    });

    test('marking an already-read row sends nothing', () async {
      await container.read(notificationsProvider.future);
      final before = client.sent.length;

      final response = await container
          .read(notificationsProvider.notifier)
          .markRead('n-read');

      expect(response.success, isTrue);
      expect(client.sent, hasLength(before));
    });

    test('a repeat does not drive the badge below what it counted', () async {
      await container.read(notificationsProvider.future);

      await container
          .read(notificationsProvider.notifier)
          .markRead('n-mention');
      await container
          .read(notificationsProvider.notifier)
          .markRead('n-mention');

      // 6, not 5: the second call found nothing left to clear. Counting the
      // ids rather than the rows actually cleared is how a badge goes negative.
      expect(container.read(notificationsProvider).value!.unreadCount, 6);
    });

    test('an id not in this feed sends nothing', () async {
      await container.read(notificationsProvider.future);
      final before = client.sent.length;

      await container
          .read(notificationsProvider.notifier)
          .markRead('someone-elses-id');

      expect(client.sent, hasLength(before));
    });
  });

  group('marking everything read', () {
    test('every unread row clears and the badge follows', () async {
      await container.read(notificationsProvider.future);

      await container.read(notificationsProvider.notifier).markAllRead();

      final feed = container.read(notificationsProvider).value!;
      expect(feed.unread, isEmpty);
      // Two rows cleared out of a counted seven. The other five are beyond the
      // page, and the server marks those too; the number is corrected on the
      // next load rather than guessed at here.
      expect(feed.unreadCount, 5);
      final post = client.sent.firstWhere((r) => r.method == 'POST');
      expect(post.url.path, endsWith('/notifications/read-all/'));
    });

    test('a refusal restores every dot', () async {
      await container.read(notificationsProvider.future);
      client.status = 500;
      client.body = '{}';

      final response = await container
          .read(notificationsProvider.notifier)
          .markAllRead();

      expect(response.success, isFalse);
      final feed = container.read(notificationsProvider).value!;
      expect(feed.unread, hasLength(2));
      expect(feed.unreadCount, 7);
    });

    test('with nothing unread it sends nothing', () async {
      client.body = '{"count": 0, "unread_count": 0, "results": []}';
      await container.read(notificationsProvider.future);
      final before = client.sent.length;

      final response = await container
          .read(notificationsProvider.notifier)
          .markAllRead();

      expect(response.success, isTrue);
      expect(client.sent, hasLength(before));
    });
  });
}

AppNotification _withLink(String? link) => AppNotification.fromJson({
  'id': 'n-1',
  'verb': 'case.mentioned',
  'link': link,
  'created_at': '2026-08-07T09:00:00Z',
});
