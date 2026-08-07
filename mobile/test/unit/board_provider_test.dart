import 'dart:convert';
import 'dart:ui' show Color;

import 'package:bottle_crm/data/models/board.dart';
import 'package:bottle_crm/data/models/lead.dart' show Priority;
import 'package:bottle_crm/providers/board_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

/// The kanban board, the tenth module mobile has and the first one that is a
/// record type of its own rather than another view of one it already had.
///
/// Four things are worth pinning.
///
/// **A board takes two calls, and the second depends on the first.** The list
/// resolves which board is open; only then can its lanes be fetched. With no
/// boards there is nothing to fetch, and asking anyway would put a null id in
/// the URL.
///
/// **The cards are nested inside the lanes**, under `tasks`. Reading the lane
/// object as the card list is the same mistake that left the accounts screen
/// empty while the API was answering with ten rows.
///
/// **Priority is spelled differently here.** A card takes `high`, a task takes
/// `High`, and the two share one enum for display. The conversion has one home
/// and this file pins both ends of it.
///
/// **Order is not a position in a list.** Lane order starts wherever the board
/// was seeded, so counting lanes to place a new one puts it on top of an
/// existing lane, and a card created without an explicit order ties with
/// whatever is already at the top of its lane.
const _boardId = 'board-1';
const _otherBoardId = 'board-2';

const _twoBoards =
    '''
{
  "count": 2,
  "results": [
    {
      "id": "$_boardId",
      "name": "Product Launch",
      "description": "Q3 launch tracker",
      "is_archived": false,
      "task_count": 2,
      "my_role": "owner"
    },
    {
      "id": "$_otherBoardId",
      "name": "Support Rota",
      "description": "",
      "is_archived": false,
      "task_count": 0,
      "my_role": "member"
    }
  ]
}
''';

const _noBoards = '{"count": 0, "results": []}';

/// Deliberately out of order, and the first lane's cards are too: the server
/// orders by `order`, but nothing in the JSON promises the client that.
const _lanes = '''
[
  {
    "id": "lane-doing",
    "name": "In Progress",
    "order": 2,
    "color": "#F59E0B",
    "limit": 1,
    "tasks": []
  },
  {
    "id": "lane-todo",
    "name": "To Do",
    "order": 1,
    "color": "#EF4444",
    "limit": null,
    "tasks": [
      {
        "id": "card-second",
        "title": "Book the venue",
        "description": "",
        "order": 1,
        "priority": "low",
        "due_date": null,
        "is_overdue": false,
        "is_completed": false,
        "account": null,
        "assigned_to": []
      },
      {
        "id": "card-first",
        "title": "Draft press release",
        "description": "One-pager for the launch",
        "order": 0,
        "priority": "high",
        "due_date": "2026-08-09T00:00:00Z",
        "is_overdue": true,
        "is_completed": false,
        "account": {"id": "acc-1", "name": "Initech"},
        "assigned_to": [
          {"id": "profile-1", "user_details": {"name": "The Boss", "email": "boss@example.com"}},
          {"id": "profile-2", "user_details": {"name": "", "email": "new@example.com"}}
        ]
      }
    ]
  }
]
''';

const _otherBoardLanes = '''
[{"id": "lane-rota", "name": "This week", "order": 0, "color": "#6B7280", "limit": null, "tasks": []}]
''';

class _FakeClient extends http.BaseClient {
  String boards = _twoBoards;
  Map<String, String> lanes = const {
    _boardId: _lanes,
    _otherBoardId: _otherBoardLanes,
  };

  int readStatus = 200;

  /// Applied to every write.
  int writeStatus = 201;
  String writeBody = '{"id": "board-new"}';

  final List<http.BaseRequest> sent = [];
  final List<String> bodies = [];

  Iterable<http.BaseRequest> get gets => sent.where((r) => r.method == 'GET');

  String bodyOf(http.BaseRequest request) => bodies[sent.indexOf(request)];

  http.BaseRequest lastOf(String method) =>
      sent.lastWhere((r) => r.method == method);

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    bodies.add(utf8.decode(await request.finalize().toBytes()));

    final segments = request.url.pathSegments;
    if (request.method == 'GET') {
      final body = segments.contains('columns')
          ? (lanes[segments[2]] ?? '[]')
          : boards;
      return _reply(request, readStatus, body);
    }
    return _reply(request, writeStatus, writeBody);
  }

  http.StreamedResponse _reply(
    http.BaseRequest request,
    int status,
    String body,
  ) {
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

void main() {
  late ProviderContainer container;
  late _FakeClient client;

  setUp(() {
    client = _FakeClient();
    ApiService().setClientForTesting(client);
    container = ProviderContainer();
  });

  tearDown(() => container.dispose());

  group('reading a board', () {
    test(
      'the lanes come from a second call, keyed on the open board',
      () async {
        final data = await container.read(boardProvider.future);

        expect(data.boards, hasLength(2));
        expect(data.active?.id, _boardId);
        expect(client.gets, hasLength(2));
        expect(client.gets.last.url.path, '/api/boards/$_boardId/columns/');
      },
    );

    test(
      'with no boards there is nothing to fetch and it stops at one call',
      () async {
        client.boards = _noBoards;

        final data = await container.read(boardProvider.future);

        expect(data.hasNoBoards, isTrue);
        expect(data.active, isNull);
        // A second call here would put "null" in the URL where the board id goes.
        expect(client.gets, hasLength(1));
      },
    );

    test('lanes are ordered by order, not by the order they arrived', () async {
      final data = await container.read(boardProvider.future);

      expect(data.lanes.map((l) => l.name), ['To Do', 'In Progress']);
    });

    test(
      'the cards are read from inside the lane, in their own order',
      () async {
        final data = await container.read(boardProvider.future);
        final todo = data.lanes.first;

        expect(todo.cards.map((c) => c.title), [
          'Draft press release',
          'Book the venue',
        ]);
        expect(data.cardCount, 2);
      },
    );

    test('a failing load is a failure, not an empty board', () async {
      // Riverpod 3 retries a failed provider on a backoff, so the default
      // container's `.future` stays pending rather than completing with the
      // error. Turning retry off is what makes the failure observable here;
      // in the app the retries are welcome, and the screen shows Try again
      // either way.
      final noRetry = ProviderContainer(retry: (_, _) => null);
      addTearDown(noRetry.dispose);
      client.readStatus = 500;
      client.boards = '{}';

      await expectLater(
        noRetry.read(boardProvider.future),
        throwsA(isA<Exception>()),
      );
    });
  });

  group('reading one card', () {
    test('the parent account and both assignees ride along', () async {
      final data = await container.read(boardProvider.future);
      final card = data.lanes.first.cards.first;

      expect(card.accountName, 'Initech');
      // The second assignee has not signed in yet, so the email is the only
      // thing there is to call them.
      expect(card.assignees, ['The Boss', 'new@example.com']);
    });

    test('overdue is the server\'s answer, not the phone\'s', () async {
      final data = await container.read(boardProvider.future);

      expect(data.lanes.first.cards.first.isOverdue, isTrue);
      expect(data.lanes.first.cards.last.isOverdue, isFalse);
    });

    test('a lowercase priority parses into the shared enum', () async {
      final data = await container.read(boardProvider.future);

      expect(data.lanes.first.cards.first.priority, Priority.high);
      expect(data.lanes.first.cards.last.priority, Priority.low);
    });

    test('and goes back out lowercase, never the tasks spelling', () {
      // `Priority.label` is "High", which is what the tasks API takes and what
      // the boards API answers 400 to.
      expect(boardPriorityValue(Priority.high), 'high');
      expect(boardPriorityValue(Priority.urgent), 'urgent');
      expect(Priority.high.label, 'High');
    });
  });

  group('what the lane header shows', () {
    test('a lane over its own limit says so', () async {
      final data = await container.read(boardProvider.future);

      expect(data.lanes.first.isOverLimit, isFalse); // no limit set
      expect(data.laneById('lane-doing')!.isOverLimit, isFalse); // 0 of 1
    });

    test('a lane with more cards than its limit is over it', () {
      const lane = BoardLane(
        id: 'l',
        name: 'In Progress',
        order: 0,
        limit: 1,
        cards: [
          BoardCard(
            id: 'a',
            laneId: 'l',
            title: 'a',
            order: 0,
            priority: Priority.medium,
          ),
          BoardCard(
            id: 'b',
            laneId: 'l',
            title: 'b',
            order: 1,
            priority: Priority.medium,
          ),
        ],
      );

      expect(lane.isOverLimit, isTrue);
    });

    test('an unusable colour falls back rather than throwing', () {
      const lane = BoardLane(id: 'l', name: 'x', order: 0, color: 'blue');

      expect(lane.swatch, const Color(0xFF6B7280));
    });
  });

  group('who may reshape the board', () {
    test('the owner is offered the add-lane control', () async {
      final data = await container.read(boardProvider.future);

      expect(data.canManageLanes, isTrue);
    });

    test('a plain member is not, because the server would refuse', () async {
      final data = await container.read(boardProvider.future);
      await container.read(boardProvider.notifier).select(_otherBoardId);
      final switched = container.read(boardProvider).value!;

      expect(data.boards[1].myRole, 'member');
      expect(switched.canManageLanes, isFalse);
    });
  });

  group('switching boards', () {
    test('selecting another board fetches that board\'s lanes', () async {
      await container.read(boardProvider.future);

      await container.read(boardProvider.notifier).select(_otherBoardId);

      expect(client.gets.last.url.path, '/api/boards/$_otherBoardId/columns/');
      expect(
        container.read(boardProvider).value!.lanes.single.name,
        'This week',
      );
    });

    test('selecting the board already open changes nothing', () async {
      await container.read(boardProvider.future);
      final before = client.gets.length;

      await container.read(boardProvider.notifier).select(_boardId);

      expect(client.gets.length, before);
    });

    test('a board that has gone falls back to the most recent one', () async {
      await container.read(boardProvider.future);
      await container.read(boardProvider.notifier).select(_otherBoardId);

      // The chosen board disappears (deleted elsewhere, or archived).
      client.boards =
          '''
        {"count": 1, "results": [
          {"id": "$_boardId", "name": "Product Launch", "task_count": 2,
           "my_role": "owner"}
        ]}
      ''';
      await container.read(boardProvider.notifier).refresh();

      expect(container.read(boardProvider).value!.active?.id, _boardId);
    });
  });

  group('writing', () {
    test('a new lane goes past the last one, not at the lane count', () async {
      await container.read(boardProvider.future);

      await container.read(boardProvider.notifier).createLane(name: 'Blocked');

      final post = client.lastOf('POST');
      expect(post.url.path, '/api/boards/$_boardId/columns/');
      // Lanes are at 1 and 2, so counting them would collide with "To Do".
      expect(jsonDecode(client.bodyOf(post))['order'], 3);
    });

    test('a new card is appended to its lane', () async {
      await container.read(boardProvider.future);

      await container
          .read(boardProvider.notifier)
          .createCard(
            laneId: 'lane-todo',
            title: 'Print badges',
            priority: boardPriorityValue(Priority.urgent),
          );

      final post = client.lastOf('POST');
      expect(post.url.path, '/api/boards/columns/lane-todo/tasks/');
      final body = jsonDecode(client.bodyOf(post));
      // Two cards already there, so the third goes at index 2. Leaving this
      // out defaults to 0 and ties with the card already at the top.
      expect(body['order'], 2);
      expect(body['priority'], 'urgent');
      expect(body.containsKey('description'), isFalse);
    });

    test('a move names the target lane and the position in it', () async {
      await container.read(boardProvider.future);

      await container
          .read(boardProvider.notifier)
          .moveCard(cardId: 'card-first', laneId: 'lane-doing', index: 0);

      final put = client.lastOf('PUT');
      expect(put.url.path, '/api/boards/tasks/card-first/');
      // `column`, the field the move endpoint reads. `lane` would be dropped
      // silently and the card would stay where it was.
      expect(jsonDecode(client.bodyOf(put)), {
        'column': 'lane-doing',
        'order': 0,
      });
    });

    test('creating a board opens the one just created', () async {
      await container.read(boardProvider.future);
      client.writeBody = '{"id": "$_otherBoardId", "name": "Support Rota"}';

      await container.read(boardProvider.notifier).createBoard(name: 'Rota');

      expect(container.read(boardProvider).value!.active?.id, _otherBoardId);
    });

    test('deleting a card asks the card endpoint', () async {
      await container.read(boardProvider.future);
      client.writeStatus = 204;
      client.writeBody = '';

      final response = await container
          .read(boardProvider.notifier)
          .deleteCard('card-first');

      expect(response.success, isTrue);
      expect(client.lastOf('DELETE').url.path, '/api/boards/tasks/card-first/');
    });

    test('a refused write returns the server\'s own words', () async {
      await container.read(boardProvider.future);
      client.writeStatus = 400;
      client.writeBody =
          '{"error": true, "errors": {"name": "A column with this name '
          'already exists on this board."}}';

      final response = await container
          .read(boardProvider.notifier)
          .createLane(name: 'To Do');

      expect(response.success, isFalse);
      expect(response.message, contains('already exists'));
    });

    test('a refused write does not refetch the board', () async {
      await container.read(boardProvider.future);
      client.writeStatus = 403;
      client.writeBody = '{"error": "Permission denied"}';
      final before = client.gets.length;

      await container.read(boardProvider.notifier).createLane(name: 'Blocked');

      expect(client.gets.length, before);
    });

    test(
      'a write with no board open is refused before it reaches the wire',
      () async {
        client.boards = _noBoards;
        await container.read(boardProvider.future);
        final before = client.sent.length;

        final response = await container
            .read(boardProvider.notifier)
            .createLane(name: 'Blocked');

        expect(response.success, isFalse);
        expect(client.sent.length, before);
      },
    );
  });
}
