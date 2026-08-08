import 'package:bottle_crm/data/models/approval_rule.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> approverJson({
  String id = 'p1',
  String email = 'ada@acme.com',
  bool isActive = true,
}) => {'id': id, 'email': email, 'is_active': isActive};

/// A rule as `/api/cases/approval-rules/` returns one.
Map<String, dynamic> ruleJson({
  String id = 'r1',
  String name = 'Close review',
  bool isActive = true,
  String approverRole = 'ADMIN',
  List<Map<String, dynamic>> approvers = const [],
  String? matchPriority,
  String? matchCaseType,
  Map<String, dynamic>? matchTeam,
  int pendingCount = 0,
  String createdAt = '2026-01-01T00:00:00Z',
}) => {
  'id': id,
  'name': name,
  'is_active': isActive,
  'approver_role': approverRole,
  'approvers': approvers,
  'match_priority': matchPriority,
  'match_case_type': matchCaseType,
  'match_team': matchTeam,
  'pending_count': pendingCount,
  'created_at': createdAt,
};

ApprovalRule build([Map<String, dynamic>? json]) =>
    ApprovalRule.fromJson(json ?? ruleJson());

void main() {
  group('ApprovalRule.fromJson', () {
    test('reads the conditions, the approvers and the tie-break date', () {
      final rule = build(
        ruleJson(
          matchPriority: 'Urgent',
          matchTeam: {'id': 't1', 'name': 'Support'},
          approvers: [approverJson()],
          pendingCount: 3,
        ),
      );
      expect(rule.matchPriority, 'Urgent');
      expect(rule.matchTeam?.name, 'Support');
      expect(rule.approvers.single.email, 'ada@acme.com');
      expect(rule.pendingCount, 3);
      expect(rule.createdAt, isNotNull);
    });

    test('an approver row with no id is dropped rather than half-built', () {
      final rule = build(
        ruleJson(
          approvers: [
            {'email': 'ghost@acme.com'},
          ],
        ),
      );
      expect(rule.approvers, isEmpty);
    });

    test('a blank condition reads as any, not as an empty string', () {
      final rule = build(ruleJson(matchPriority: '', matchCaseType: ''));
      expect(rule.matchPriority, isNull);
      expect(rule.matchCaseType, isNull);
      expect(rule.matchSentence, 'Every ticket');
    });
  });

  group('roleClears', () {
    test('is true for admin, the one role a profile can hold', () {
      expect(build().roleClears, isTrue);
      expect(rolesThatExist, ['ADMIN']);
    });

    test('is false for manager, which matches no profile', () {
      expect(build(ruleJson(approverRole: 'MANAGER')).roleClears, isFalse);
    });
  });

  group('approverSentence', () {
    test('names the role when nobody is named', () {
      expect(build().approverSentence, 'any admin');
    });

    test('adds named approvers to the role rather than replacing it', () {
      // The finding. `can_be_acted_on_by` returns true for a named approver OR
      // anyone holding the role, and the web row used to list only the names,
      // so an admin read a rule as tighter than it is.
      final rule = build(
        ruleJson(
          approvers: [
            approverJson(),
            approverJson(id: 'p2', email: 'bob@acme.com'),
          ],
        ),
      );
      expect(
        rule.approverSentence,
        'any admin, or ada@acme.com or bob@acme.com',
      );
    });

    test('is the names alone when the role matches nobody', () {
      final rule = build(
        ruleJson(approverRole: 'MANAGER', approvers: [approverJson()]),
      );
      expect(rule.approverSentence, 'ada@acme.com');
    });

    test('says nobody when the role matches nobody and no one is named', () {
      expect(
        build(ruleJson(approverRole: 'MANAGER')).approverSentence,
        'nobody',
      );
    });
  });

  group('clearableByNobody', () {
    test('is a manager rule with no named approvers', () {
      expect(
        build(ruleJson(approverRole: 'MANAGER')).clearableByNobody,
        isTrue,
      );
    });

    test('is not one with a named approver', () {
      final rule = build(
        ruleJson(approverRole: 'MANAGER', approvers: [approverJson()]),
      );
      expect(rule.clearableByNobody, isFalse);
    });

    test('is not an admin rule', () {
      expect(build().clearableByNobody, isFalse);
    });

    test('is not an inactive rule, which gates nothing to strand', () {
      final rule = build(ruleJson(approverRole: 'MANAGER', isActive: false));
      expect(rule.clearableByNobody, isFalse);
    });
  });

  group('matchSentence and specificity', () {
    test('joins the conditions that are set', () {
      final rule = build(
        ruleJson(
          matchPriority: 'Urgent',
          matchCaseType: 'Incident',
          matchTeam: {'id': 't1', 'name': 'Support'},
        ),
      );
      expect(rule.matchSentence, 'Urgent priority · incident · Support team');
      expect(rule.specificity, 3);
    });

    test('an unfiltered rule matches everything and is least specific', () {
      expect(build().matchSentence, 'Every ticket');
      expect(build().specificity, 0);
    });
  });

  group('signature', () {
    test('is equal for two rules matching the same tickets', () {
      expect(
        build(ruleJson(id: 'a', matchPriority: 'High')).signature,
        build(ruleJson(id: 'b', matchPriority: 'High')).signature,
      );
    });

    test('separates an unset condition from a set one', () {
      expect(
        build().signature,
        isNot(build(ruleJson(matchPriority: 'High')).signature),
      );
    });
  });

  group('shadowedRuleIds', () {
    test('flags the older of two rules with identical conditions', () {
      // Both always match together, and the stable sort over -created_at hands
      // every case to the newer one, so the older never runs.
      final rules = [
        build(ruleJson(id: 'old', createdAt: '2026-01-01T00:00:00Z')),
        build(ruleJson(id: 'new', createdAt: '2026-02-01T00:00:00Z')),
      ];
      expect(shadowedRuleIds(rules), {'old'});
    });

    test('leaves rules with different conditions alone', () {
      // A broad rule is a fallback for the tickets the narrow one misses.
      final rules = [
        build(ruleJson(id: 'broad', createdAt: '2026-01-01T00:00:00Z')),
        build(
          ruleJson(
            id: 'narrow',
            matchPriority: 'Urgent',
            createdAt: '2026-02-01T00:00:00Z',
          ),
        ),
      ];
      expect(shadowedRuleIds(rules), isEmpty);
    });

    test('ignores an inactive rule in both directions', () {
      final beatenByOff = [
        build(ruleJson(id: 'old', createdAt: '2026-01-01T00:00:00Z')),
        build(
          ruleJson(
            id: 'off',
            isActive: false,
            createdAt: '2026-02-01T00:00:00Z',
          ),
        ),
      ];
      expect(shadowedRuleIds(beatenByOff), isEmpty);

      final offAndBeaten = [
        build(
          ruleJson(
            id: 'off',
            isActive: false,
            createdAt: '2026-01-01T00:00:00Z',
          ),
        ),
        build(ruleJson(id: 'new', createdAt: '2026-02-01T00:00:00Z')),
      ];
      expect(shadowedRuleIds(offAndBeaten), isEmpty);
    });

    test('flags every loser when three share conditions', () {
      final rules = [
        build(ruleJson(id: 'a', createdAt: '2026-01-01T00:00:00Z')),
        build(ruleJson(id: 'b', createdAt: '2026-02-01T00:00:00Z')),
        build(ruleJson(id: 'c', createdAt: '2026-03-01T00:00:00Z')),
      ];
      expect(shadowedRuleIds(rules), {'a', 'b'});
    });

    test('flags nothing when a date is missing, rather than guessing', () {
      // A blank must not read as "created first", which would declare a live
      // rule dead on the strength of an absent field.
      final undated = ApprovalRule.fromJson(
        ruleJson(id: 'a')..['created_at'] = null,
      );
      final rules = [undated, build(ruleJson(id: 'b'))];
      expect(shadowedRuleIds(rules), isEmpty);
    });

    test('is empty for no rules', () {
      expect(shadowedRuleIds(const []), isEmpty);
    });
  });

  group('shadowedBy', () {
    test('names the newest rule that takes the cases', () {
      final rules = [
        build(
          ruleJson(id: 'a', name: 'Oldest', createdAt: '2026-01-01T00:00:00Z'),
        ),
        build(
          ruleJson(id: 'b', name: 'Middle', createdAt: '2026-02-01T00:00:00Z'),
        ),
        build(
          ruleJson(id: 'c', name: 'Newest', createdAt: '2026-03-01T00:00:00Z'),
        ),
      ];
      expect(shadowedBy(rules.first, rules)?.name, 'Newest');
    });

    test('is null for a rule nothing shadows', () {
      final rules = [build()];
      expect(shadowedBy(rules.first, rules), isNull);
    });
  });

  group('approvalRulePayload', () {
    test('sets the one trigger the backend accepts rather than asking', () {
      final body = approvalRulePayload(
        name: '  Close review  ',
        approverRole: 'ADMIN',
        approverIds: const ['p1'],
      );
      expect(body['trigger_event'], 'pre_close');
      expect(body['name'], 'Close review');
      expect(body['approver_ids'], ['p1']);
    });

    test('clears the three nullable conditions with null, not empty', () {
      final body = approvalRulePayload(
        name: 'x',
        approverRole: 'ADMIN',
        approverIds: const [],
        matchPriority: '',
        matchCaseType: '',
        matchTeamId: '',
      );
      expect(body['match_priority'], isNull);
      expect(body['match_case_type'], isNull);
      expect(body['match_team_id'], isNull);
    });

    test('never sends anything the server owns', () {
      final body = approvalRulePayload(
        name: 'x',
        approverRole: 'ADMIN',
        approverIds: const [],
      );
      for (final key in ['org', 'created_by', 'id', 'pending_count']) {
        expect(body.containsKey(key), isFalse, reason: key);
      }
    });

    test('drops a blank approver id rather than posting one', () {
      final body = approvalRulePayload(
        name: 'x',
        approverRole: 'ADMIN',
        approverIds: const ['p1', '', '  '],
      );
      expect(body['approver_ids'], ['p1']);
    });

    test('omits is_active entirely when the form does not own it', () {
      final body = approvalRulePayload(
        name: 'x',
        approverRole: 'ADMIN',
        approverIds: const [],
      );
      expect(body.containsKey('is_active'), isFalse);
    });
  });

  group('approvalRuleActivePayload', () {
    test('carries the one key, so a save cannot blank the name', () {
      expect(approvalRuleActivePayload(true), {'is_active': true});
    });
  });

  group('approvalRuleNameProblem', () {
    test('accepts an ordinary name', () {
      expect(approvalRuleNameProblem('Close review'), isNull);
    });

    test('refuses an empty one', () {
      expect(approvalRuleNameProblem('  '), isNotNull);
    });

    test('refuses more than the column holds', () {
      expect(approvalRuleNameProblem('x' * 129), isNotNull);
      expect(approvalRuleNameProblem('x' * 128), isNull);
    });
  });

  group('the delete copy', () {
    test('names both outcomes before it happens', () {
      expect(approvalRuleDeleteExplanation, contains('deleted for good'));
      expect(approvalRuleDeleteExplanation, contains('turned off instead'));
    });

    test('reads the outcome off the response, and defaults to deleted', () {
      // The soft branch answers 200 with `is_active: false`; the hard one
      // answers 204 with no body at all. "Did it throw" cannot tell them apart.
      expect(approvalRuleWasTurnedOff(const {'is_active': false}), isTrue);
      expect(approvalRuleWasTurnedOff(null), isFalse);
      expect(approvalRuleWasTurnedOff(const {}), isFalse);
      expect(approvalRuleWasTurnedOff(const {'is_active': true}), isFalse);
    });

    test('reports which one actually happened', () {
      // Saying "deleted" about a row still in the list reads as a delete that
      // failed silently.
      expect(
        approvalRuleDeleteResult(turnedOff: true),
        contains('turned off instead of deleted'),
      );
      expect(approvalRuleDeleteResult(turnedOff: false), 'Rule deleted');
    });
  });
}
