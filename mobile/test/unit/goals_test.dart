import 'package:bottle_crm/data/models/sales_goal.dart';
import 'package:bottle_crm/providers/goals_provider.dart';
import 'package:flutter_test/flutter_test.dart';

SalesGoal goal({
  String id = 'g1',
  String name = 'Goal',
  String status = 'on_track',
  bool isActive = true,
  double target = 1000,
  double progress = 100,
  int percent = 10,
  String periodEnd = '2026-12-31',
  String? assignedToId,
  String? assignedToName,
  String? teamId,
  String? teamName,
  String goalType = 'REVENUE',
}) => SalesGoal(
  id: id,
  name: name,
  goalType: goalType,
  targetValue: target,
  periodType: 'MONTHLY',
  periodStart: '2026-01-01',
  periodEnd: periodEnd,
  assignedToId: assignedToId,
  assignedToName: assignedToName,
  teamId: teamId,
  teamName: teamName,
  isActive: isActive,
  progressValue: progress,
  progressPercent: percent,
  status: status,
);

void main() {
  group('SalesGoal.fromJson', () {
    test('flattens the nested assignee and team the API sends', () {
      final parsed = SalesGoal.fromJson({
        'id': 'g1',
        'name': 'Q1 revenue',
        'goal_type': 'REVENUE',
        'target_value': '50000.00',
        'period_type': 'QUARTERLY',
        'period_start': '2026-01-01',
        'period_end': '2026-03-31',
        'assigned_to': 'p1',
        'assigned_to_detail': {
          'id': 'p1',
          'user_details': {'name': 'Ada Lovelace', 'email': 'ada@example.com'},
        },
        'team': null,
        'team_detail': null,
        'is_active': true,
        'progress_value': 20000,
        'progress_percent': 40,
        'status': 'behind',
      });

      expect(parsed.assignedToId, 'p1');
      expect(parsed.assignedToName, 'Ada Lovelace');
      // `target_value` is a DecimalField, so it arrives as a string.
      expect(parsed.targetValue, 50000);
      expect(parsed.progressPercent, 40);
    });

    test('falls back to the email when a person has no name', () {
      final parsed = SalesGoal.fromJson({
        'id': 'g1',
        'assigned_to_detail': {
          'id': 'p1',
          'user_details': {'name': '', 'email': 'ada@example.com'},
        },
      });
      expect(parsed.assignedToName, 'ada@example.com');
    });

    test('survives a payload with nothing in it', () {
      final parsed = SalesGoal.fromJson(const {});
      expect(parsed.id, '');
      expect(parsed.targetValue, 0);
      expect(parsed.assignedToName, isNull);
    });
  });

  group('targetLabel', () {
    test('names the person, then the team, then the org', () {
      expect(
        goal(assignedToId: 'p1', assignedToName: 'Ada').targetLabel,
        'Ada',
      );
      expect(
        goal(teamId: 't1', teamName: 'Support').targetLabel,
        'Support (team)',
      );
      expect(goal().targetLabel, 'Whole organisation');
    });

    test('prefers the person when the API sends both', () {
      // The API permits both FKs. Neither client can write that state, but a
      // row created by curl can arrive in it, and the label must pick one.
      final both = goal(
        assignedToId: 'p1',
        assignedToName: 'Ada',
        teamId: 't1',
        teamName: 'Support',
      );
      expect(both.targetLabel, 'Ada');
    });
  });

  group('goalTotals', () {
    test('sums the active goals and counts every one', () {
      final totals = goalTotals([
        goal(id: 'a', target: 100, progress: 50),
        goal(id: 'b', target: 200, progress: 20),
        goal(id: 'c', target: 999, progress: 999, isActive: false),
      ], today: '2026-06-01');

      expect(totals.count, 3);
      expect(totals.active, 2);
      // The retired goal's 999 is in neither sum.
      expect(totals.target, 300);
      expect(totals.achieved, 70);
    });

    test('counts a goal ending today as still behind pace', () {
      // The boundary the web got wrong: it compared `period_end` as a UTC
      // instant against the clock, so a goal dropped out of this count part-way
      // through its own final day. A goal ending today is one somebody can
      // still act on.
      final totals = goalTotals([
        goal(status: 'behind', periodEnd: '2026-06-01'),
      ], today: '2026-06-01');
      expect(totals.behind, 1);
    });

    test('leaves out a goal whose period has already ended', () {
      final totals = goalTotals([
        goal(status: 'behind', periodEnd: '2026-05-31'),
      ], today: '2026-06-01');
      expect(totals.behind, 0);
    });

    test('leaves out a retired goal even when it is behind and open', () {
      final totals = goalTotals([
        goal(status: 'behind', periodEnd: '2026-12-31', isActive: false),
      ], today: '2026-06-01');
      expect(totals.behind, 0);
    });

    test('is all zeroes for no goals rather than throwing', () {
      final totals = goalTotals(const [], today: '2026-06-01');
      expect(totals.count, 0);
      expect(totals.target, 0);
    });
  });

  group('goalToday', () {
    test('is the local date, zero-padded', () {
      expect(goalToday(DateTime(2026, 1, 5)), '2026-01-05');
      expect(goalToday(DateTime(2026, 12, 31)), '2026-12-31');
    });

    test('does not shift the day for a late-evening local time', () {
      // `toIso8601String()` on a UTC conversion would hand back the next day
      // here for anywhere west of Greenwich, and the previous one east of it.
      // These are date-only fields, so a day is the whole quantity.
      expect(goalToday(DateTime(2026, 6, 1, 23, 59)), '2026-06-01');
      expect(goalToday(DateTime(2026, 6, 1, 0, 1)), '2026-06-01');
    });
  });

  group('sortGoalsByUrgency', () {
    test('puts active before retired, whatever the status', () {
      final sorted = sortGoalsByUrgency([
        goal(id: 'retired', status: 'behind', isActive: false),
        goal(id: 'active', status: 'completed'),
      ]);
      expect(sorted.map((g) => g.id), ['active', 'retired']);
    });

    test('orders behind, at risk, on track, then met', () {
      final sorted = sortGoalsByUrgency([
        goal(id: 'done', status: 'completed'),
        goal(id: 'ok', status: 'on_track'),
        goal(id: 'bad', status: 'behind'),
        goal(id: 'risky', status: 'at_risk'),
      ]);
      expect(sorted.map((g) => g.id), ['bad', 'risky', 'ok', 'done']);
    });

    test('breaks a tie on progress, furthest along first', () {
      final sorted = sortGoalsByUrgency([
        goal(id: 'low', status: 'behind', percent: 10),
        goal(id: 'high', status: 'behind', percent: 40),
      ]);
      expect(sorted.map((g) => g.id), ['high', 'low']);
    });

    test('does not mutate what it was given', () {
      final input = [
        goal(id: 'done', status: 'completed'),
        goal(id: 'bad', status: 'behind'),
      ];
      sortGoalsByUrgency(input);
      expect(input.map((g) => g.id), ['done', 'bad']);
    });
  });

  group('validateGoalForm', () {
    String? check({
      String name = 'Goal',
      String target = '100',
      String start = '2026-01-01',
      String end = '2026-03-31',
    }) => validateGoalForm(
      name: name,
      targetValue: target,
      periodStart: start,
      periodEnd: end,
    );

    test('accepts a filled-in form', () {
      expect(check(), isNull);
    });

    test('refuses a blank name', () {
      expect(check(name: '   '), isNotNull);
    });

    test('refuses a target that is not a number', () {
      expect(check(target: 'lots'), contains('number'));
    });

    test('refuses zero and negative targets, matching the serializer', () {
      // `SalesGoalCreateSerializer.validate` rejects `target_value <= 0`.
      expect(check(target: '0'), contains('greater than 0'));
      expect(check(target: '-5'), contains('greater than 0'));
    });

    test('refuses an end date on or before the start', () {
      // The serializer rejects `period_end <= period_start`, so equal dates are
      // refused too and the message must not imply a one-day goal is possible.
      expect(check(start: '2026-03-31', end: '2026-01-01'), isNotNull);
      expect(check(start: '2026-01-01', end: '2026-01-01'), isNotNull);
    });

    test('refuses a missing date rather than sending a blank one', () {
      expect(check(start: ''), isNotNull);
      expect(check(end: ''), isNotNull);
    });
  });

  group('goalTargetFields', () {
    test('sets exactly one FK and explicitly nulls the other', () {
      // Both keys are always present. PUT is partial, so omitting one keeps the
      // old value, and switching a goal from a person to a team would leave it
      // assigned to both.
      expect(goalTargetFields('profile:p1'), {
        'assigned_to': 'p1',
        'team': null,
      });
      expect(goalTargetFields('team:t1'), {'assigned_to': null, 'team': 't1'});
    });

    test('clears both for a whole-org goal, and for anything unrecognised', () {
      expect(goalTargetFields('org'), {'assigned_to': null, 'team': null});
      expect(goalTargetFields(null), {'assigned_to': null, 'team': null});
      expect(goalTargetFields('nonsense'), {'assigned_to': null, 'team': null});
    });
  });

  group('goalTargetValue', () {
    test('round-trips through goalTargetFields', () {
      expect(goalTargetFields(goalTargetValue(goal(assignedToId: 'p1'))), {
        'assigned_to': 'p1',
        'team': null,
      });
      expect(goalTargetFields(goalTargetValue(goal(teamId: 't1'))), {
        'assigned_to': null,
        'team': 't1',
      });
      expect(goalTargetFields(goalTargetValue(goal())), {
        'assigned_to': null,
        'team': null,
      });
    });

    test('reads an empty string FK as no target, not as an id', () {
      expect(goalTargetValue(goal(assignedToId: '', teamId: '')), 'org');
    });
  });

  group('GoalLeaderRow.fromJson', () {
    test('reads the name the endpoint now sends', () {
      final row = GoalLeaderRow.fromJson({
        'rank': 1,
        'goal_id': 'g1',
        'goal_name': 'Q1',
        'user': {'id': 'p1', 'name': 'Ada Lovelace'},
        'target': 100.0,
        'achieved': 104.0,
        'percent': 104,
      });
      expect(row.user, 'Ada Lovelace');
      // Uncapped, unlike SalesGoal.progressPercent. 104% is the point of a board.
      expect(row.percent, 104);
    });

    test('says Unknown rather than blank when the user block is missing', () {
      expect(GoalLeaderRow.fromJson(const {'rank': 1}).user, 'Unknown');
    });
  });

  group('labels', () {
    test('spell each status for a person', () {
      expect(goalStatusLabel('behind'), 'Behind pace');
      expect(goalStatusLabel('at_risk'), 'At risk');
      expect(goalStatusLabel('on_track'), 'On track');
      expect(goalStatusLabel('completed'), 'Target met');
    });

    test('pass an unrecognised status through rather than blanking it', () {
      expect(goalStatusLabel('surprise'), 'surprise');
    });

    test('cover every type and period the backend accepts', () {
      for (final type in goalTypes) {
        expect(goalTypeLabel(type), isNot(type));
      }
      for (final period in goalPeriodTypes) {
        expect(goalPeriodLabel(period), isNotEmpty);
      }
    });
  });
}
