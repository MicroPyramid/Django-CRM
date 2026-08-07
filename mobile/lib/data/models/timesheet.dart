import 'time_entry.dart';

/// One week of the caller's logged time, as `/api/time-entries/timesheet/`
/// returns it.
///
/// The envelope carries every day in the range, including the ones with
/// nothing on them, and that is the point of the screen rather than an
/// artefact of the response: an unlogged Wednesday and a Wednesday you forgot
/// to look at are the same picture unless the empty day is drawn.
class TimesheetWeek {
  const TimesheetWeek({
    required this.start,
    required this.end,
    this.profileName = '',
    this.days = const [],
    this.totalMinutes = 0,
    this.billableMinutes = 0,
    this.runningCount = 0,
  });

  /// Inclusive Mon..Sun bounds, as the server resolved them. Read back from
  /// the response rather than kept from the request, so the header always
  /// names the week actually being shown.
  final DateTime start;
  final DateTime end;
  final String profileName;
  final List<TimesheetDay> days;

  /// Server-side totals, correct at response time. The screen recomputes both
  /// from the entries while a timer runs, because these do not tick.
  final int totalMinutes;
  final int billableMinutes;
  final int runningCount;

  Iterable<TimeEntry> get entries => days.expand((d) => d.entries);

  Iterable<TimeEntry> get runningEntries => entries.where((e) => e.isRunning);

  /// Billable time that has not been put on an invoice yet. The one number
  /// here that is a prompt to do something rather than a record of what
  /// happened.
  int get unbilledCount =>
      entries.where((e) => e.billable && !e.isBilled).length;

  /// Minutes logged in the week, `elapsed` minutes after the response.
  int totalMinutesAt(int elapsed) =>
      days.fold(0, (sum, d) => sum + d.totalMinutesAt(elapsed));

  int billableMinutesAt(int elapsed) =>
      days.fold(0, (sum, d) => sum + d.billableMinutesAt(elapsed));

  /// What the billable time in this week is worth, at the rate saved on each
  /// entry rather than at today's rate.
  ///
  /// Null when nothing carries a rate, and null again when the rated entries
  /// are not all in one currency, because there is no honest single total
  /// across two currencies and a number with one symbol on it would be a
  /// wrong one. Two currencies in a week is rare; being quietly wrong about
  /// money is not a rare problem.
  ({double amount, String currency})? billableValueAt(int elapsed) {
    final rated = entries.where(
      (e) => e.billable && e.hourlyRate != null && e.hourlyRate! > 0,
    );
    if (rated.isEmpty) return null;
    final currencies = rated.map((e) => e.currency ?? '').toSet();
    if (currencies.length > 1) return null;
    final amount = rated.fold<double>(
      0,
      (sum, e) => sum + (e.minutesAt(elapsed) / 60) * e.hourlyRate!,
    );
    return (amount: amount, currency: currencies.first);
  }

  factory TimesheetWeek.fromJson(Map<String, dynamic> json) {
    final profile = json['profile'];
    return TimesheetWeek(
      start: _date(json['start']),
      end: _date(json['end']),
      profileName: profile is Map<String, dynamic>
          ? (profile['name'] as String? ?? '')
          : '',
      days: ((json['days'] as List<dynamic>?) ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(TimesheetDay.fromJson)
          .toList(),
      totalMinutes: json['total_minutes'] as int? ?? 0,
      billableMinutes: json['billable_minutes'] as int? ?? 0,
      runningCount: json['running_count'] as int? ?? 0,
    );
  }
}

/// A single day's bucket. `entries` may be empty and the day is still drawn.
class TimesheetDay {
  const TimesheetDay({
    required this.date,
    this.entries = const [],
    this.totalMinutes = 0,
    this.billableMinutes = 0,
  });

  final DateTime date;
  final List<TimeEntry> entries;
  final int totalMinutes;
  final int billableMinutes;

  bool get isEmpty => entries.isEmpty;

  int totalMinutesAt(int elapsed) =>
      entries.fold(0, (sum, e) => sum + e.minutesAt(elapsed));

  int billableMinutesAt(int elapsed) => entries
      .where((e) => e.billable)
      .fold(0, (sum, e) => sum + e.minutesAt(elapsed));

  factory TimesheetDay.fromJson(Map<String, dynamic> json) {
    return TimesheetDay(
      date: _date(json['date']),
      entries: ((json['entries'] as List<dynamic>?) ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(TimeEntry.fromJson)
          .toList(),
      totalMinutes: json['total_minutes'] as int? ?? 0,
      billableMinutes: json['billable_minutes'] as int? ?? 0,
    );
  }
}

/// A YYYY-MM-DD string from the API as a local calendar date.
///
/// Parsed with an explicit midnight rather than `DateTime.parse` on the bare
/// date, so the value is local midnight and not UTC midnight. Reading a UTC
/// midnight in a zone behind UTC lands on the previous day, which would label
/// every column with the wrong weekday west of Greenwich.
DateTime _date(dynamic value) {
  final text = value?.toString() ?? '';
  return DateTime.tryParse('${text}T00:00:00') ?? DateTime.now();
}
