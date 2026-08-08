import 'package:bottle_crm/data/models/reopen_policy.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> policyJson({
  bool isEnabled = true,
  int windowDays = 7,
  String reopenToStatus = 'Pending',
  bool notifyAssigned = true,
  int reopened = 0,
  int missed = 0,
  int median = 0,
}) => {
  'is_enabled': isEnabled,
  'reopen_window_days': windowDays,
  'reopen_to_status': reopenToStatus,
  'notify_assigned': notifyAssigned,
  'reopened_last_30d': reopened,
  'replies_after_window_30d': missed,
  'median_days_to_reply': median,
};

void main() {
  group('ReopenPolicy.fromJson', () {
    test('reads the four fields and the three metrics', () {
      final policy = ReopenPolicy.fromJson(
        policyJson(
          windowDays: 14,
          reopenToStatus: 'New',
          notifyAssigned: false,
          reopened: 6,
          missed: 4,
          median: 2,
        ),
      );
      expect(policy.windowDays, 14);
      expect(policy.reopenToStatus, 'New');
      expect(policy.notifyAssigned, isFalse);
      expect(policy.reopenedLast30d, 6);
      expect(policy.repliesAfterWindow30d, 4);
      expect(policy.medianDaysToReply, 2);
    });

    test('a median sent as a float rounds rather than crashing', () {
      final json = policyJson()..['median_days_to_reply'] = 2.6;
      expect(ReopenPolicy.fromJson(json).medianDaysToReply, 3);
    });

    test('a missing metric reads as zero', () {
      final json = policyJson()..remove('reopened_last_30d');
      expect(ReopenPolicy.fromJson(json).reopenedLast30d, 0);
    });
  });

  group('missedWindowIsMeasured', () {
    test('is true while reopening is on', () {
      expect(
        ReopenPolicy.fromJson(policyJson()).missedWindowIsMeasured,
        isTrue,
      );
    });

    test('is false while reopening is off', () {
      // `_evaluate_reopen` returns None on `if not policy["is_enabled"]`,
      // before the window comparison, and the out_of_reopen_window flag is
      // written only for the "out_of_window" return. So the count is zero by
      // construction in exactly the state where every reply is being lost.
      expect(
        ReopenPolicy.fromJson(
          policyJson(isEnabled: false),
        ).missedWindowIsMeasured,
        isFalse,
      );
    });
  });

  group('missedWindowCaveat', () {
    test('is null while reopening is on, even at zero', () {
      expect(missedWindowCaveat(ReopenPolicy.fromJson(policyJson())), isNull);
    });

    test('explains the zero while reopening is off', () {
      final note = missedWindowCaveat(
        ReopenPolicy.fromJson(policyJson(isEnabled: false)),
      );
      expect(note, isNotNull);
      expect(note, contains('not because nothing is being lost'));
    });
  });

  group('reopenSummary', () {
    test('names the window while on', () {
      final text = reopenSummary(
        ReopenPolicy.fromJson(
          policyJson(windowDays: 14, reopenToStatus: 'New'),
        ),
      );
      expect(text, contains('14 days'));
      expect(text, contains('New'));
    });

    test(
      'says what off means, which is not "nothing happens to the reply"',
      () {
        final text = reopenSummary(
          ReopenPolicy.fromJson(policyJson(isEnabled: false)),
        );
        expect(text, contains('stay closed'));
        expect(text, contains('filed'));
      },
    );
  });

  group('reopenPolicyProblem', () {
    test('accepts the defaults', () {
      expect(
        reopenPolicyProblem(windowDays: 7, reopenToStatus: 'Pending'),
        isNull,
      );
    });

    test('refuses a window outside 1 to 365, which the serializer refuses', () {
      expect(
        reopenPolicyProblem(windowDays: 0, reopenToStatus: 'Pending'),
        isNotNull,
      );
      expect(
        reopenPolicyProblem(windowDays: 366, reopenToStatus: 'Pending'),
        isNotNull,
      );
      expect(
        reopenPolicyProblem(windowDays: null, reopenToStatus: 'Pending'),
        isNotNull,
      );
    });

    test('accepts the boundaries themselves', () {
      expect(
        reopenPolicyProblem(windowDays: 1, reopenToStatus: 'Pending'),
        isNull,
      );
      expect(
        reopenPolicyProblem(windowDays: 365, reopenToStatus: 'Pending'),
        isNull,
      );
    });

    test('refuses a terminal status, which would close on arrival', () {
      expect(
        reopenPolicyProblem(windowDays: 7, reopenToStatus: 'Closed'),
        isNotNull,
      );
    });

    test('accepts each of the three non-terminal statuses', () {
      for (final status in reopenToStatuses) {
        expect(
          reopenPolicyProblem(windowDays: 7, reopenToStatus: status),
          isNull,
          reason: status,
        );
      }
    });
  });

  group('reopenPolicyPayload', () {
    test('sends all four fields, so an unchecked box is not an omission', () {
      final body = reopenPolicyPayload(
        isEnabled: false,
        windowDays: 3,
        reopenToStatus: 'Assigned',
        notifyAssigned: false,
      );
      expect(body, {
        'is_enabled': false,
        'reopen_window_days': 3,
        'reopen_to_status': 'Assigned',
        'notify_assigned': false,
      });
    });

    test('never sends a computed metric back', () {
      final body = reopenPolicyPayload(
        isEnabled: true,
        windowDays: 7,
        reopenToStatus: 'Pending',
        notifyAssigned: true,
      );
      expect(body.containsKey('reopened_last_30d'), isFalse);
      expect(body.containsKey('replies_after_window_30d'), isFalse);
      expect(body.containsKey('median_days_to_reply'), isFalse);
    });
  });
}
