import 'package:bottle_crm/data/models/time_entry.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _json(Map<String, dynamic> extra) => {
  'id': 'e1',
  'case': 'c1',
  'profile': 'p1',
  'started_at': '2026-09-01T09:00:00Z',
  'ended_at': '2026-09-01T10:00:00Z',
  'duration_minutes': 60,
  'billable': true,
  ...extra,
};

void main() {
  test('an entry billed while Invoices is off reads as billed', () {
    final entry = TimeEntry.fromJson(
      _json({'invoiced': true, 'invoice': null}),
    );
    expect(entry.invoiceId, isNull);
    expect(entry.isBilled, isTrue);
  });

  test(
    'an entry with an invoice reads as billed, and one without does not',
    () {
      expect(TimeEntry.fromJson(_json({'invoice': 'i1'})).isBilled, isTrue);
      final open = TimeEntry.fromJson(_json({}));
      expect(open.invoiced, isFalse);
      expect(open.isBilled, isFalse);
    },
  );
}
