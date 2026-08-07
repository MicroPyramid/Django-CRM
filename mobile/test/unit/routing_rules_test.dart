import 'dart:convert';

import 'package:bottle_crm/data/models/routing_rule.dart';
import 'package:bottle_crm/providers/settings_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

/// Routing rules, where the order is the program.
///
/// The things worth pinning:
///
/// - The `in` operator needs a LIST. A string saves cleanly and then matches
///   nothing, forever, with nothing anywhere pointing at why.
/// - Only the half of the target in play is sent, or a later strategy switch
///   resurrects a stale target nobody chose.
/// - An empty assignee list is OMITTED on create so the serializer's own guard
///   fires, and REFUSED on edit because that guard is create-only.
/// - `last_assigned_index` is the next index, not the last, and it indexes the
///   active pool ordered by id, not the serializer's list.
class _FakeClient extends http.BaseClient {
  int status = 200;
  String body = '{}';
  final List<({int status, String body})> queue = [];
  final List<http.BaseRequest> sent = [];
  final List<String> bodies = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    final bytes = await request.finalize().toBytes();
    bodies.add(utf8.decode(bytes));
    final next = queue.isNotEmpty
        ? queue.removeAt(0)
        : (status: status, body: body);
    return http.StreamedResponse(
      Stream.value(utf8.encode(next.body)),
      next.status,
      request: request,
    );
  }
}

RoutingTarget _person(String id, String name, {bool active = true}) =>
    RoutingTarget(id: id, name: name, isActive: active);

RoutingRule _rule({
  String strategy = RoutingRule.strategyRoundRobin,
  List<RoutingTarget> assignees = const [],
  RoutingTarget? team,
  int? cursor,
  bool isActive = true,
  bool stopProcessing = false,
  List<RoutingCondition> conditions = const [],
}) {
  return RoutingRule(
    id: 'r1',
    name: 'Billing to the billing crew',
    strategy: strategy,
    targetAssignees: assignees,
    targetTeam: team,
    lastAssignedIndex: cursor,
    isActive: isActive,
    stopProcessing: stopProcessing,
    conditions: conditions,
  );
}

void main() {
  group('the round-robin cursor', () {
    // `_round_robin` reads `pool[state.last_assigned_index % len(pool)]` and
    // only THEN stores `idx + 1`. The stored value is already the next index.
    test('names the agent at the stored index, not the one after', () {
      final rule = _rule(
        assignees: [
          _person('a', 'Ada'),
          _person('b', 'Brin'),
          _person('c', 'Cai'),
        ],
        cursor: 1,
      );
      expect(rule.nextInRotation?.name, 'Brin');
    });

    test('a rotation that has never run starts at the first agent', () {
      // The engine's own dry run is `state.last_assigned_index if state else 0`.
      final rule = _rule(
        assignees: [_person('a', 'Ada'), _person('b', 'Brin')],
        cursor: null,
      );
      expect(rule.nextInRotation?.name, 'Ada');
    });

    test('wraps rather than running off the end', () {
      final rule = _rule(
        assignees: [_person('a', 'Ada'), _person('b', 'Brin')],
        cursor: 7,
      );
      expect(rule.nextInRotation?.name, 'Brin');
    });

    test('never names a deactivated agent', () {
      // `_active_pool` filters them out, so the engine will never pick them.
      // Indexing the serializer's list here would name one, which is the one
      // answer that is certainly wrong.
      final rule = _rule(
        assignees: [
          _person('a', 'Ada', active: false),
          _person('b', 'Brin'),
          _person('c', 'Cai'),
        ],
        cursor: 0,
      );
      expect(rule.nextInRotation?.name, 'Brin');
      expect(rule.rotationPool.map((p) => p.name), ['Brin', 'Cai']);
    });

    test('indexes the pool in id order, not the order it arrived in', () {
      // `_active_pool` is `.order_by("id")`.
      final rule = _rule(
        assignees: [_person('c', 'Cai'), _person('a', 'Ada')],
        cursor: 0,
      );
      expect(rule.nextInRotation?.name, 'Ada');
    });

    test('says nothing for the strategies it cannot know', () {
      for (final strategy in [
        RoutingRule.strategyDirect,
        RoutingRule.strategyLeastBusy,
        RoutingRule.strategyByTeam,
      ]) {
        expect(
          _rule(
            strategy: strategy,
            assignees: [_person('a', 'Ada')],
            cursor: 0,
          ).nextInRotation,
          isNull,
          reason: '$strategy does not have a cursor to read',
        );
      }
    });
  });

  group('a rule that assigns nobody', () {
    test('is flagged when every assignee is deactivated', () {
      expect(
        _rule(assignees: [_person('a', 'Ada', active: false)]).assignsNobody,
        isTrue,
      );
    });

    test('is flagged when a by team rule has no team', () {
      expect(_rule(strategy: RoutingRule.strategyByTeam).assignsNobody, isTrue);
    });

    test('is not flagged when one live assignee remains', () {
      expect(
        _rule(
          assignees: [_person('a', 'Ada', active: false), _person('b', 'Brin')],
        ).assignsNobody,
        isFalse,
      );
    });

    test('is not flagged on a rule that is already turned off', () {
      // It is not running, so it is not swallowing anything.
      expect(
        _rule(assignees: const [], isActive: false).assignsNobody,
        isFalse,
      );
    });
  });

  group('what a rule matches', () {
    test('says so plainly when it matches everything', () {
      // The single most consequential thing a row can say.
      expect(routingMatchSentence(_rule()), 'Matches every new ticket');
    });

    test('reads conditions in the words the app uses', () {
      final rule = _rule(
        conditions: const [
          RoutingCondition(field: 'priority', op: 'eq', value: 'High'),
          RoutingCondition(
            field: 'case_type',
            op: 'in',
            value: ['Bug', 'Fault'],
          ),
        ],
      );
      expect(
        routingMatchSentence(rule),
        'Priority is High and Type is one of Bug, Fault',
      );
    });

    test('renders a custom field condition without inventing a label', () {
      final rule = _rule(
        conditions: const [
          RoutingCondition(field: 'custom_fields.severity', value: 'S1'),
        ],
      );
      expect(routingMatchSentence(rule), 'severity is S1');
    });
  });

  group('cleaning the condition rows', () {
    test('gives the in operator a list', () {
      // `cases/routing.py` evaluates `in` with
      // `if not isinstance(value, (list, tuple)): return False`, silently, and
      // `validate_conditions` never checks the type. A string here saves 200
      // and matches nothing forever.
      final cleaned = cleanRoutingConditions([
        RoutingConditionDraft(
          field: 'priority',
          op: 'in',
          value: 'High, Urgent',
        ),
      ]);
      expect(cleaned.single['value'], ['High', 'Urgent']);
    });

    test('leaves every other operator a plain string', () {
      final cleaned = cleanRoutingConditions([
        RoutingConditionDraft(field: 'priority', op: 'eq', value: 'High'),
      ]);
      expect(cleaned.single['value'], 'High');
    });

    test('an empty in list is still sent', () {
      // `validate_conditions` rejects a condition with no `value` key at all.
      final cleaned = cleanRoutingConditions([
        RoutingConditionDraft(field: 'tags', op: 'in', value: '  '),
      ]);
      expect(cleaned.single.containsKey('value'), isTrue);
      expect(cleaned.single['value'], isEmpty);
    });

    test('drops a row the admin added and left blank', () {
      // An empty row is how the editor says "I am about to type here".
      final cleaned = cleanRoutingConditions([
        RoutingConditionDraft(field: 'priority', value: 'High'),
        RoutingConditionDraft(),
      ]);
      expect(cleaned, hasLength(1));
    });

    test('a missing operator becomes the backend default', () {
      final cleaned = cleanRoutingConditions([
        RoutingConditionDraft(field: 'priority', op: '', value: 'High'),
      ]);
      expect(cleaned.single['op'], 'eq');
    });
  });

  group('the payload', () {
    Map<String, dynamic> build({
      String strategy = RoutingRule.strategyDirect,
      List<String> assignees = const ['p1'],
      String? teamId,
      String name = 'Billing',
      bool? isActive,
    }) {
      return routingRulePayload(
        name: name,
        priorityOrder: 100,
        strategy: strategy,
        stopProcessing: true,
        conditions: const [],
        assigneeIds: assignees,
        teamId: teamId,
        isActive: isActive,
      );
    }

    test('a by team rule sends no assignees', () {
      // The backend stores the half that does not apply rather than rejecting
      // it, so a later strategy switch would resurrect a stale target.
      final body = build(
        strategy: RoutingRule.strategyByTeam,
        assignees: const ['p1'],
        teamId: 't1',
      );
      expect(body.containsKey('target_assignee_ids'), isFalse);
      expect(body['target_team_id'], 't1');
    });

    test('a people rule sends no team', () {
      final body = build(strategy: RoutingRule.strategyDirect, teamId: 't1');
      expect(body.containsKey('target_team_id'), isFalse);
      expect(body['target_assignee_ids'], ['p1']);
    });

    test(
      'a by team rule with no team clears it with null, not an empty string',
      () {
        // The field is `allow_null=True`; `''` is a 400.
        final body = build(strategy: RoutingRule.strategyByTeam, teamId: '');
        expect(body['target_team_id'], isNull);
        expect(body.containsKey('target_team_id'), isTrue);
      },
    );

    test('an empty assignee list omits the key rather than sending []', () {
      // `[]` disarms the serializer's own guard, which only raises on `None`.
      // The rule would save, match tickets, and assign nobody.
      final body = build(assignees: const []);
      expect(body.containsKey('target_assignee_ids'), isFalse);
    });

    test('is_active rides only when the caller asks', () {
      expect(build(isActive: true)['is_active'], isTrue);
      expect(build().containsKey('is_active'), isFalse);
    });

    test('turning a rule on sends only is_active', () {
      // Rebuilding the full payload from a row control with no name field
      // would send `name: ''` and blank the rule's name.
      expect(routingActivatePayload(), {'is_active': true});
    });
  });

  group('what a write has to fix first', () {
    String? check({
      required bool isCreate,
      String name = 'Billing',
      String strategy = RoutingRule.strategyRoundRobin,
      List<String> assignees = const [],
      String? teamId,
      List<RoutingConditionDraft> conditions = const [],
    }) {
      return routingWriteProblem(
        isCreate: isCreate,
        name: name,
        strategy: strategy,
        assigneeIds: assignees,
        teamId: teamId,
        conditions: conditions,
      );
    }

    test('a blank name never leaves the phone', () {
      expect(
        check(isCreate: true, name: '  ', assignees: const ['p1']),
        isNotNull,
      );
    });

    test('a by team rule needs a team', () {
      expect(
        check(isCreate: true, strategy: RoutingRule.strategyByTeam),
        contains('needs a team'),
      );
    });

    test('an empty pool is refused on edit', () {
      // `RoutingRuleSerializer.validate` guards this behind
      // `self.instance is None`, so it never fires on a PUT, and the omitted
      // key means `partial=True` leaves the stored assignees in place. Sending
      // it would answer 200 and change nothing the admin asked to change.
      expect(check(isCreate: false), contains('at least one assignee'));
    });

    test('an empty pool is left to the server on create', () {
      // There the serializer does answer, in its own words, and its message is
      // better than one written here.
      expect(check(isCreate: true), isNull);
    });

    test('a custom field is a field a rule may match on', () {
      expect(
        check(
          isCreate: true,
          assignees: const ['p1'],
          conditions: [RoutingConditionDraft(field: 'custom_fields.severity')],
        ),
        isNull,
      );
    });

    test('an unsupported field is named back', () {
      expect(
        check(
          isCreate: true,
          assignees: const ['p1'],
          conditions: [RoutingConditionDraft(field: 'assignee')],
        ),
        contains('"assignee"'),
      );
    });
  });

  group('the provider', () {
    late ProviderContainer container;
    late _FakeClient client;

    setUp(() {
      client = _FakeClient();
      ApiService().setClientForTesting(client);
      container = ProviderContainer();
    });

    tearDown(() => container.dispose());

    Future<RoutingRulesState> readRules() {
      container.listen(routingRulesProvider, (_, _) {});
      return container.read(routingRulesProvider.future);
    }

    test('reads the rules, the totals and the cursor', () async {
      client.body = '''
      {"rules": [
        {"id": "r1", "name": "Billing", "priority_order": 100,
         "is_active": true, "strategy": "round_robin", "stop_processing": true,
         "conditions": [{"field": "priority", "op": "eq", "value": "High"}],
         "target_assignees": [
           {"id": "p1", "is_active": true,
            "user_details": {"name": "Ada", "email": "ada@example.com"}}
         ],
         "target_team": null, "matched_last_30d": 12,
         "state": {"last_assigned_index": 0}}
      ],
       "totals": {"count": 3, "active": 2, "unrouted_last_30d": 9}}
      ''';
      final state = await readRules();
      final rule = state.rules.single;
      expect(rule.name, 'Billing');
      expect(rule.targetAssignees.single.name, 'Ada');
      expect(rule.conditions.single.field, 'priority');
      expect(rule.matchedLast30d, 12);
      expect(rule.lastAssignedIndex, 0);
      expect(state.unroutedLast30d, 9);
      expect(state.active, 2);
    });

    test('keeps the order the server sent', () async {
      // The order IS the behaviour: the engine takes the first match. A client
      // that re-sorted would show a different program from the one that runs.
      client.body = '''
      {"rules": [
        {"id": "r1", "name": "Zebra", "priority_order": 10},
        {"id": "r2", "name": "Alpha", "priority_order": 20}
      ]}
      ''';
      final state = await readRules();
      expect(state.rules.map((r) => r.name), ['Zebra', 'Alpha']);
    });

    test('counts the rules that match tickets and assign nobody', () async {
      client.body = '''
      {"rules": [
        {"id": "r1", "name": "Dead", "is_active": true, "strategy": "direct",
         "target_assignees": []},
        {"id": "r2", "name": "Fine", "is_active": true, "strategy": "direct",
         "target_assignees": [{"id": "p1", "is_active": true,
                               "user_details": {"name": "Ada"}}]}
      ]}
      ''';
      final state = await readRules();
      expect(state.dead, 1);
    });

    test('creating one posts to the rule list endpoint', () async {
      client.body = '{"rules": []}';
      await readRules();
      await container.read(routingRulesProvider.notifier).createRule({
        'name': 'Billing',
      });
      final post = client.sent.firstWhere((r) => r.method == 'POST');
      expect(post.url.path, endsWith('/cases/routing-rules/'));
    });

    test('turning one off sends only is_active, false', () async {
      client.body = '{"rules": []}';
      await readRules();
      await container.read(routingRulesProvider.notifier).deactivateRule('r1');
      final put = client.sent.firstWhere((r) => r.method == 'PUT');
      expect(put.url.path, endsWith('/cases/routing-rules/r1/'));
      expect(jsonDecode(client.bodies[client.sent.indexOf(put)]), {
        'is_active': false,
      });
    });

    test('turning one on sends only is_active, true', () async {
      client.body = '{"rules": []}';
      await readRules();
      await container.read(routingRulesProvider.notifier).activateRule('r1');
      final put = client.sent.firstWhere((r) => r.method == 'PUT');
      expect(jsonDecode(client.bodies[client.sent.indexOf(put)]), {
        'is_active': true,
      });
    });

    test('deleting one is a DELETE on the row', () async {
      client.body = '{"rules": []}';
      await readRules();
      await container.read(routingRulesProvider.notifier).deleteRule('r1');
      final sent = client.sent.firstWhere((r) => r.method == 'DELETE');
      expect(sent.url.path, endsWith('/cases/routing-rules/r1/'));
    });

    test('a write re-reads the list', () async {
      // The order, the match counts and the unrouted total all move when a
      // rule does, and none can be recomputed from the write's answer.
      client.body = '{"rules": []}';
      await readRules();
      final before = client.sent.length;
      await container.read(routingRulesProvider.notifier).deleteRule('r1');
      expect(
        client.sent.skip(before).where((r) => r.method == 'GET').length,
        1,
      );
    });

    test(
      'the admin-only refusal is reported in the server own words',
      () async {
        client.body = '{"rules": []}';
        await readRules();
        client.queue.add((
          status: 403,
          body: '{"error": true, "errors": "Admin access required"}',
        ));
        final message = await container
            .read(routingRulesProvider.notifier)
            .createRule({'name': 'Billing'});
        expect(message, 'Admin access required');
      },
    );

    test('a serializer refusal comes back as its field message', () async {
      client.body = '{"rules": []}';
      await readRules();
      client.queue.add((
        status: 400,
        body:
            '{"error": true, "errors": {"target_assignee_ids": '
            '["round_robin strategy requires at least one target assignee."]}}',
      ));
      final message = await container
          .read(routingRulesProvider.notifier)
          .createRule({'name': 'Billing'});
      expect(
        message,
        'round_robin strategy requires at least one target assignee.',
      );
    });
  });
}
