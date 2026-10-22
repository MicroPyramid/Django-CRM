import 'package:bottle_crm/services/run_time.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final now = DateTime.utc(2026, 10, 22, 5, 0);
  String kolkata(DateTime at) =>
      runTimeLabel(at, zone: 'Asia/Kolkata', now: now);

  test('formats run times in the org timezone', () {
    expect(kolkata(DateTime.utc(2026, 10, 22, 5, 12)), 'Today 10:42');
    expect(kolkata(DateTime.utc(2026, 10, 21, 12, 33)), 'Yesterday 18:03');
    expect(kolkata(DateTime.utc(2026, 9, 21, 12, 33)), '21 Sep 18:03');
    expect(kolkata(DateTime.utc(2025, 10, 21, 12, 33)), '21 Oct 2025 18:03');
  });

  test('counts a UTC instant just after Kolkata midnight as that day', () {
    expect(kolkata(DateTime.utc(2026, 10, 21, 18, 45)), 'Today 00:15');
    expect(kolkata(DateTime.utc(2026, 10, 21, 18, 15)), 'Yesterday 23:45');
  });

  test('reads a local DateTime as the same instant', () {
    final local = DateTime.utc(2026, 10, 22, 5, 12).toLocal();
    expect(kolkata(local), 'Today 10:42');
  });

  test('falls back to UTC for no zone or an unknown one', () {
    final at = DateTime.utc(2026, 10, 22, 5, 12);
    expect(runTimeLabel(at, now: now), 'Today 05:12');
    expect(runTimeLabel(at, zone: 'Nowhere/Land', now: now), 'Today 05:12');
  });

  test('legacy zone names resolve', () {
    final at = DateTime.utc(2026, 10, 22, 5, 12);
    expect(runTimeLabel(at, zone: 'Asia/Calcutta', now: now), 'Today 10:42');
  });
}
