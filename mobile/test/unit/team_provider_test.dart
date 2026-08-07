import 'dart:convert';

import 'package:bottle_crm/data/models/team_member.dart';
import 'package:bottle_crm/providers/team_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

/// Team and access, the ninth module mobile has and the first one where the UI
/// shows a role.
///
/// Three things are worth pinning here.
///
/// **403 is a state, not a failure.** `/api/users/` is admin-only, and More
/// offers this screen to everyone. A member has to land on "admins only", not
/// on an error with a Retry button that can never succeed.
///
/// **Two ids, and only one of them works.** `id` is the Profile row; the role
/// and status endpoints take the User id out of `user_details`. Sending the
/// wrong one addresses a different table, which is a class of mistake that has
/// silently disabled permission checks in this codebase before.
///
/// **The rows are nested.** They live at `active_users.active_users`, and
/// reading the outer object as the list is exactly what left the accounts
/// screen showing nothing while the API was answering with ten rows.
class _FakeClient extends http.BaseClient {
  _FakeClient({this.body = '{}'});

  int status = 200;
  String body;
  final List<http.BaseRequest> sent = [];
  final List<String> bodies = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    bodies.add(utf8.decode(await request.finalize().toBytes()));
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

const _twoPeople = '''
{
  "active_users": {
    "active_users_count": 2,
    "active_users": [
      {
        "id": "profile-admin",
        "role": "ADMIN",
        "is_active": true,
        "active_token_count": 0,
        "user_details": {
          "id": "user-admin",
          "email": "boss@example.com",
          "name": "The Boss",
          "last_login": "2026-08-07T06:37:40.749049Z"
        }
      },
      {
        "id": "profile-member",
        "role": "USER",
        "is_active": true,
        "active_token_count": 0,
        "user_details": {
          "id": "user-member",
          "email": "new@example.com",
          "name": "",
          "last_login": null
        }
      }
    ]
  },
  "inactive_users": {
    "inactive_users": [
      {
        "id": "profile-gone",
        "role": "USER",
        "is_active": false,
        "active_token_count": 2,
        "user_details": {
          "id": "user-gone",
          "email": "left@example.com",
          "name": "Departed",
          "last_login": "2026-01-02T00:00:00Z"
        }
      }
    ]
  }
}
''';

void main() {
  late ProviderContainer container;
  late _FakeClient client;

  setUp(() {
    client = _FakeClient(body: _twoPeople);
    ApiService().setClientForTesting(client);
    container = ProviderContainer();
  });

  tearDown(() => container.dispose());

  group('reading the org', () {
    test('the rows come from one level down, not from the wrapper', () async {
      final data = await container.read(teamProvider.future);

      expect(data.active, hasLength(2));
      expect(data.inactive, hasLength(1));
      expect(data.forbidden, isFalse);
    });

    test('a member gets the admins-only state, not an error', () async {
      client.status = 403;
      client.body = '{"detail": "You do not have permission."}';

      final data = await container.read(teamProvider.future);

      expect(data.forbidden, isTrue);
      expect(data.active, isEmpty);
    });

    test('a real failure is still a failure', () async {
      // Riverpod 3 retries a failed provider on a backoff, so the default
      // container's `.future` stays pending rather than completing with the
      // error. Turning retry off is what makes the failure observable here;
      // in the app the retries are welcome, and the screen shows Try again
      // either way.
      final noRetry = ProviderContainer(retry: (_, _) => null);
      addTearDown(noRetry.dispose);
      client.status = 500;
      client.body = '{}';

      await expectLater(
        noRetry.read(teamProvider.future),
        throwsA(isA<Exception>()),
      );
    });
  });

  group('reading one person', () {
    test('the profile id and the user id are both kept', () async {
      final data = await container.read(teamProvider.future);
      final boss = data.active.first;

      expect(boss.id, 'profile-admin');
      expect(boss.userId, 'user-admin');
    });

    test('someone invited but not yet signed in reads as their email', () async {
      final data = await container.read(teamProvider.future);
      final invited = data.active[1];

      // `name` is empty until they sign in, and a row labelled "Unnamed" tells
      // an admin nothing about who they invited.
      expect(invited.name, 'new@example.com');
      expect(invited.hasNeverSignedIn, isTrue);
    });

    test('a signed-in person is not counted as never signed in', () async {
      final data = await container.read(teamProvider.future);

      expect(data.active.first.hasNeverSignedIn, isFalse);
      expect(data.neverSignedInCount, 1);
    });
  });

  group('the numbers the screen leads with', () {
    test('tokens outliving a deactivated account are totalled', () async {
      final data = await container.read(teamProvider.future);

      expect(data.tokensOnDeactivated, 2);
    });

    test(
      'the only admin is identified so the controls can be withheld',
      () async {
        final data = await container.read(teamProvider.future);

        expect(data.adminCount, 1);
        expect(data.lastAdmin?.userId, 'user-admin');
      },
    );

    test('with two admins there is no last admin to protect', () {
      final data = TeamListData(
        active: [_member('a', 'ADMIN'), _member('b', 'ADMIN')],
      );

      expect(data.lastAdmin, isNull);
    });

    test('a deactivated admin does not count towards keeping one', () {
      // `lastAdmin` reads the active list only. An admin who has been
      // deactivated cannot sign in, so they are not the admin the org has.
      final data = TeamListData(
        active: [_member('a', 'ADMIN')],
        inactive: [_member('b', 'ADMIN')],
      );

      expect(data.lastAdmin?.userId, 'user-a');
      expect(data.adminCount, 1);
    });
  });

  group('writing', () {
    test('a role change PATCHes the user id, never the profile id', () async {
      await container.read(teamProvider.future);
      await container
          .read(teamProvider.notifier)
          .setRole(userId: 'user-member', role: 'ADMIN');

      final patch = client.sent.firstWhere((r) => r.method == 'PATCH');
      expect(patch.url.path, endsWith('/user/user-member/'));
      expect(patch.url.path, isNot(contains('profile-')));
      expect(client.bodies[client.sent.indexOf(patch)], contains('"ADMIN"'));
    });

    test('deactivating posts the word the server expects', () async {
      await container.read(teamProvider.future);
      await container
          .read(teamProvider.notifier)
          .setActive(userId: 'user-member', isActive: false);

      final post = client.sent.firstWhere((r) => r.method == 'POST');
      expect(post.url.path, endsWith('/user/user-member/status/'));
      // "Inactive", not false and not "inactive": the serializer takes a
      // choice value and anything else is a 400.
      expect(client.bodies[client.sent.indexOf(post)], contains('"Inactive"'));
    });

    test('reactivating sends the other one', () async {
      await container.read(teamProvider.future);
      await container
          .read(teamProvider.notifier)
          .setActive(userId: 'user-gone', isActive: true);

      final post = client.sent.firstWhere((r) => r.method == 'POST');
      expect(client.bodies[client.sent.indexOf(post)], contains('"Active"'));
    });

    test('an invite carries the email and the chosen role', () async {
      await container.read(teamProvider.future);
      await container
          .read(teamProvider.notifier)
          .invite(email: 'them@company.com', role: 'USER');

      final post = client.sent.firstWhere((r) => r.method == 'POST');
      expect(post.url.path, endsWith('/users/'));
      final body = client.bodies[client.sent.indexOf(post)];
      expect(body, contains('them@company.com'));
      expect(body, contains('"USER"'));
    });

    test('a refused write returns the server\'s own message', () async {
      await container.read(teamProvider.future);
      client.status = 400;
      client.body = '{"error": true, "errors": "User already in this org."}';

      final response = await container
          .read(teamProvider.notifier)
          .invite(email: 'boss@example.com', role: 'USER');

      expect(response.success, isFalse);
      expect(response.message, contains('already in this org'));
    });

    test('a refused write does not refetch the list', () async {
      await container.read(teamProvider.future);
      client.status = 403;
      final getsBefore = client.sent.where((r) => r.method == 'GET').length;

      await container
          .read(teamProvider.notifier)
          .setRole(userId: 'user-admin', role: 'USER');

      expect(client.sent.where((r) => r.method == 'GET').length, getsBefore);
    });
  });

  test('only the two roles the backend recognises are offered', () {
    // ApprovalRule has a MANAGER value; Profile.role does not. Offering it
    // would be offering a choice the server answers 400 to.
    expect(teamRoles, ['ADMIN', 'USER']);
  });
}

TeamMember _member(String suffix, String role) => TeamMember(
  id: 'profile-$suffix',
  userId: 'user-$suffix',
  name: suffix,
  email: '$suffix@example.com',
  role: role,
  isActive: true,
);
