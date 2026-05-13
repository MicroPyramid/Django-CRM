/// Time-tracking entry on a ticket. Ended-null = currently running.
///
/// Mirrors `cases.serializer.TimeEntrySerializer`.
class TimeEntry {
  final String id;
  final String caseId;
  final String profileId;
  final String? profileName;
  final DateTime startedAt;
  final DateTime? endedAt;
  final int? durationMinutes;
  final bool billable;
  final String? description;

  const TimeEntry({
    required this.id,
    required this.caseId,
    required this.profileId,
    this.profileName,
    required this.startedAt,
    this.endedAt,
    this.durationMinutes,
    this.billable = false,
    this.description,
  });

  bool get isRunning => endedAt == null;

  /// Live duration, including currently-running timers.
  Duration get liveDuration {
    final end = endedAt ?? DateTime.now();
    return end.difference(startedAt);
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
    return TimeEntry(
      id: json['id']?.toString() ?? '',
      caseId: json['case']?.toString() ?? '',
      profileId: profile is Map<String, dynamic>
          ? profile['id']?.toString() ?? ''
          : json['profile']?.toString() ?? '',
      profileName: profileName,
      startedAt: DateTime.tryParse(json['started_at']?.toString() ?? '') ??
          DateTime.now(),
      endedAt: json['ended_at'] != null
          ? DateTime.tryParse(json['ended_at'].toString())
          : null,
      durationMinutes: json['duration_minutes'] as int?,
      billable: json['billable'] as bool? ?? false,
      description: json['description'] as String?,
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
