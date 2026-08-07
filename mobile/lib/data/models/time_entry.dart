/// Time-tracking entry on a ticket. Ended-null = currently running.
///
/// Mirrors `cases.serializer.TimeEntrySerializer`, which two endpoints emit in
/// two shapes. On a ticket's own list `case` and `invoice` are bare ids; on
/// `/time-entries/timesheet/` the view expands both to objects, because that
/// page shows a week across many tickets and an id is not a name. `fromJson`
/// reads either, so `caseId` is an id in both and never the string
/// `"{id: ..., name: ...}"`, which is what `.toString()` on the object form
/// used to produce.
class TimeEntry {
  final String id;
  final String caseId;

  /// Present only where the server expands the ticket (the timesheet).
  final String? caseName;
  final String profileId;
  final String? profileName;
  final DateTime startedAt;
  final DateTime? endedAt;
  final int? durationMinutes;
  final bool billable;
  final String? description;

  /// Set once the entry has been billed. A billed entry is shown as billed and
  /// never offered for editing: double-billing an hour is a refund.
  final String? invoiceId;
  final String? invoiceNumber;

  /// The rate as it stood when this entry was logged, and the currency it was
  /// logged in. Both are snapshotted per entry precisely so a rate change next
  /// month does not rewrite what last month was worth. Sent as a decimal
  /// string, so parsed rather than cast.
  final double? hourlyRate;
  final String? currency;

  /// The server's own count of minutes elapsed on a running timer, taken at
  /// response time. The phone's clock is a rendering detail, not the truth
  /// about how long somebody has been working, so the screen counts up from
  /// this rather than from `DateTime.now()` against `startedAt`.
  final int? liveDurationMinutes;

  const TimeEntry({
    required this.id,
    required this.caseId,
    this.caseName,
    required this.profileId,
    this.profileName,
    required this.startedAt,
    this.endedAt,
    this.durationMinutes,
    this.billable = false,
    this.description,
    this.invoiceId,
    this.invoiceNumber,
    this.hourlyRate,
    this.currency,
    this.liveDurationMinutes,
  });

  bool get isRunning => endedAt == null;

  bool get isBilled => invoiceId != null;

  /// Live duration, including currently-running timers.
  Duration get liveDuration {
    final end = endedAt ?? DateTime.now();
    return end.difference(startedAt);
  }

  /// Minutes this entry contributes to a total, `elapsed` minutes after the
  /// response was received. A stopped entry ignores `elapsed`: its duration is
  /// settled and must not drift upwards while the screen is open.
  int minutesAt(int elapsed) {
    if (!isRunning) return durationMinutes ?? 0;
    final base = liveDurationMinutes ?? liveDuration.inMinutes;
    return base + elapsed;
  }

  factory TimeEntry.fromJson(Map<String, dynamic> json) {
    String? profileName;
    final profile = json['profile'];
    if (profile is Map<String, dynamic>) {
      final user = profile['user_details'] ?? profile['user'];
      if (user is Map<String, dynamic>) {
        profileName = user['email'] as String?;
      }
      profileName ??= profile['email'] as String?;
    }
    final caseValue = json['case'];
    final invoice = json['invoice'];
    return TimeEntry(
      id: json['id']?.toString() ?? '',
      caseId: caseValue is Map<String, dynamic>
          ? caseValue['id']?.toString() ?? ''
          : caseValue?.toString() ?? '',
      caseName: caseValue is Map<String, dynamic>
          ? caseValue['name'] as String?
          : null,
      profileId: profile is Map<String, dynamic>
          ? profile['id']?.toString() ?? ''
          : json['profile']?.toString() ?? '',
      profileName: profileName,
      startedAt:
          DateTime.tryParse(json['started_at']?.toString() ?? '') ??
          DateTime.now(),
      endedAt: json['ended_at'] != null
          ? DateTime.tryParse(json['ended_at'].toString())
          : null,
      durationMinutes: json['duration_minutes'] as int?,
      billable: json['billable'] as bool? ?? false,
      description: json['description'] as String?,
      invoiceId: invoice is Map<String, dynamic>
          ? invoice['id']?.toString()
          : invoice?.toString(),
      invoiceNumber: invoice is Map<String, dynamic>
          ? invoice['invoice_number'] as String?
          : null,
      hourlyRate: double.tryParse(json['hourly_rate']?.toString() ?? ''),
      currency: json['currency'] as String?,
      liveDurationMinutes: json['live_duration_minutes'] as int?,
    );
  }
}

/// Aggregate totals for a ticket. Mirrors `CaseSerializer.time_summary`.
class TimeSummary {
  final int totalMinutes;
  final int billableMinutes;
  final DateTime? lastEntryAt;
  final List<TimeSummaryByProfile> byProfile;

  const TimeSummary({
    this.totalMinutes = 0,
    this.billableMinutes = 0,
    this.lastEntryAt,
    this.byProfile = const [],
  });

  factory TimeSummary.fromJson(Map<String, dynamic> json) {
    return TimeSummary(
      totalMinutes: json['total_minutes'] as int? ?? 0,
      billableMinutes: json['billable_minutes'] as int? ?? 0,
      lastEntryAt: json['last_entry_at'] != null
          ? DateTime.tryParse(json['last_entry_at'].toString())
          : null,
      byProfile: ((json['by_profile'] as List<dynamic>?) ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(TimeSummaryByProfile.fromJson)
          .toList(),
    );
  }
}

class TimeSummaryByProfile {
  final String profileId;
  final String name;
  final int minutes;
  const TimeSummaryByProfile({
    required this.profileId,
    required this.name,
    required this.minutes,
  });
  factory TimeSummaryByProfile.fromJson(Map<String, dynamic> json) {
    return TimeSummaryByProfile(
      profileId: json['profile_id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      minutes: json['minutes'] as int? ?? 0,
    );
  }
}
