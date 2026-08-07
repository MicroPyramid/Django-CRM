/// The calendar every response target is measured against.
///
/// One default calendar per org, enforced by a partial unique constraint, and
/// created on first read. This is the file that decides whether "answered in
/// 4h" means anything: a ticket opened at 17:20 on Friday and answered at 09:10
/// on Monday is either fifteen hours late or fifty minutes early, and only this
/// calendar says which.
library;

/// Monday first, matching `windows_by_weekday()` and the web. The key is the
/// prefix of the model's fourteen flat TimeFields.
const List<(String, String)> businessWeekdays = [
  ('Monday', 'monday'),
  ('Tuesday', 'tuesday'),
  ('Wednesday', 'wednesday'),
  ('Thursday', 'thursday'),
  ('Friday', 'friday'),
  ('Saturday', 'saturday'),
  ('Sunday', 'sunday'),
];

/// One weekday's window. Both times null means closed; the serializer refuses
/// one set and the other null.
class BusinessDay {
  const BusinessDay({
    required this.day,
    required this.key,
    this.open,
    this.close,
  });

  final String day;
  final String key;

  /// "HH:MM", or null for a closed day. The API sends "HH:MM:SS" and this is
  /// trimmed on parse; DRF parses "HH:MM" back, so nothing widens it again.
  final String? open;
  final String? close;

  bool get isClosed => open == null || close == null;

  /// Hours open, or 0. Zero for a day whose close is not after its open, which
  /// mirrors `_has_any_open_window` treating that day as shut.
  double get hours {
    final from = _minutes(open);
    final to = _minutes(close);
    if (from == null || to == null || to <= from) return 0;
    return (to - from) / 60;
  }
}

/// "09:30" or "09:30:00" to minutes past midnight, or null.
int? _minutes(String? value) {
  if (value == null) return null;
  final parts = value.split(':');
  if (parts.length < 2) return null;
  final hour = int.tryParse(parts[0]);
  final minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) return null;
  return hour * 60 + minute;
}

/// "09:00:00" to "09:00". A blank stays null, which is a closed day.
String? trimSeconds(String? value) {
  if (value == null || value.isEmpty) return null;
  return value.length >= 5 ? value.substring(0, 5) : value;
}

class BusinessHoliday {
  const BusinessHoliday({
    required this.id,
    required this.date,
    required this.name,
  });

  final String id;

  /// ISO `yyyy-MM-dd`. A full day off in the calendar's timezone; partial days
  /// are not modelled.
  final String date;
  final String name;

  factory BusinessHoliday.fromJson(Map<String, dynamic> json) =>
      BusinessHoliday(
        id: json['id']?.toString() ?? '',
        date: json['date']?.toString() ?? '',
        name: json['name']?.toString() ?? '',
      );
}

class BusinessCalendar {
  const BusinessCalendar({
    required this.id,
    this.name = 'Default',
    this.timezone = 'UTC',
    this.isDefault = true,
    this.days = const [],
    this.holidays = const [],
  });

  final String id;
  final String name;

  /// The calendar's own IANA zone, which is not the org's. Both exist and can
  /// disagree; SLA windows are read in this one.
  final String timezone;

  final bool isDefault;

  /// Monday first, always seven entries.
  final List<BusinessDay> days;

  /// Sorted by date server-side (`ordering = ("date",)`).
  final List<BusinessHoliday> holidays;

  double get weeklyHours => days.fold(0, (sum, d) => sum + d.hours);

  int get openDayCount => days.where((d) => d.hours > 0).length;

  /// **A calendar with no open window at all is a 24/7 calendar, not a closed
  /// one.**
  ///
  /// `business_hours/calendar.py::add_business_hours` checks
  /// `_has_any_open_window` first and, when nothing is open, returns
  /// `start_dt + timedelta(hours=hours)`: plain wall-clock arithmetic, holidays
  /// included. So marking every day Closed does not stop the SLA clock, it
  /// makes it run continuously, which is the opposite of what the screen would
  /// otherwise imply. The one state where a settings page has to contradict its
  /// own reading of itself.
  bool get isAlwaysOn => openDayCount == 0;

  /// The holiday already stored for this date, or null. See
  /// [holidayDuplicateWarning].
  BusinessHoliday? holidayOn(String date) {
    for (final holiday in holidays) {
      if (holiday.date == date) return holiday;
    }
    return null;
  }

  factory BusinessCalendar.fromJson(Map<String, dynamic> json) {
    final rawHolidays = json['holidays'];
    return BusinessCalendar(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? 'Default',
      timezone: json['timezone']?.toString() ?? 'UTC',
      isDefault: json['is_default'] as bool? ?? true,
      days: [
        for (final (label, key) in businessWeekdays)
          BusinessDay(
            day: label,
            key: key,
            open: trimSeconds(json['${key}_open']?.toString()),
            close: trimSeconds(json['${key}_close']?.toString()),
          ),
      ],
      holidays: rawHolidays is List
          ? [
              for (final h in rawHolidays)
                if (h is Map<String, dynamic>) BusinessHoliday.fromJson(h),
            ]
          : const [],
    );
  }
}

/// The body for `PUT /business-hours/calendar/<id>/`.
///
/// The seven days go back out as the model's fourteen flat fields, Monday
/// first, null for a closed day. `is_default` is read-only on the serializer
/// and is never sent; `id` never travels through a form, because there is one
/// calendar per org and the read that produced it was already org-scoped.
Map<String, dynamic> businessHoursPayload({
  required List<BusinessDay> days,
  required String name,
  required String timezone,
}) {
  final body = <String, dynamic>{
    'name': name.trim(),
    'timezone': timezone.trim(),
  };
  for (final (label, key) in businessWeekdays) {
    final day = days.where((d) => d.day == label).firstOrNull;
    body['${key}_open'] = day?.isClosed ?? true ? null : day!.open;
    body['${key}_close'] = day?.isClosed ?? true ? null : day!.close;
  }
  return body;
}

/// What a business-hours save has to fix before it is worth sending, or `null`.
///
/// Every rule here is also in `BusinessCalendarSerializer.validate`, which is
/// the authority. These exist to name the day, since the serializer's error
/// arrives keyed on `monday_open` and a phone has nowhere useful to put that.
String? businessHoursProblem({
  required List<BusinessDay> days,
  required String name,
  required String timezone,
}) {
  if (name.trim().isEmpty) return 'The calendar needs a name.';
  if (timezone.trim().isEmpty) {
    return 'The calendar needs a timezone, as an IANA name like '
        'Asia/Kolkata.';
  }
  for (final day in days) {
    final open = day.open;
    final close = day.close;
    if ((open == null) != (close == null)) {
      return '${day.day} needs an opening and a closing time, or neither.';
    }
    if (open == null || close == null) continue;
    final from = _minutes(open);
    final to = _minutes(close);
    if (from == null || to == null) {
      return '${day.day} has a time that is not readable.';
    }
    if (to <= from) {
      // Not arbitrary: the walker only ever moves forward within one local
      // day, so a window that wraps midnight has no meaning to it.
      return '${day.day} has to close after it opens. A shift that runs '
          'past midnight cannot be set here.';
    }
  }
  return null;
}

/// The body for `POST /business-hours/calendar/<id>/holidays/`.
Map<String, dynamic> holidayPayload({
  required String date,
  required String name,
}) => {'date': date, 'name': name.trim()};

/// What the admin should know before adding a holiday on a date already taken,
/// or `null`.
///
/// `BusinessHolidayListView.post` is idempotent on `(calendar, date)`: it
/// answers **200 with the row that was already there**, not 201, and creates
/// nothing. The name typed into the form is discarded, silently, and the web
/// treats both status codes as the same success. So adding 25 December as
/// "Christmas Day" when it is already stored as "Xmas" looks like it worked and
/// changed nothing.
String? holidayDuplicateWarning(BusinessCalendar calendar, String date) {
  final existing = calendar.holidayOn(date);
  if (existing == null) return null;
  return '${_humanDate(date)} is already a holiday, called '
      '"${existing.name}". Adding it again keeps that name.';
}

/// What the screen says after a holiday add that turned out to be a duplicate.
String holidayAlreadyExistedMessage(String name) =>
    'That date was already a holiday, called "$name". Nothing changed.';

/// Removing a holiday is permanent, and takes effect at once.
const String holidayRemovalExplanation =
    'The day counts as working time again straight away, so targets that were '
    'paused over it move earlier. This cannot be undone, only added back.';

/// "25 Dec 2026" from an ISO date, or the input when it is not one.
String _humanDate(String iso) {
  final parsed = DateTime.tryParse(iso);
  if (parsed == null) return iso;
  const months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];
  return '${parsed.day} ${months[parsed.month - 1]} ${parsed.year}';
}

String humanHolidayDate(String iso) => _humanDate(iso);

/// The sentence the screen leads with, which has to be the engine's behaviour
/// rather than the form's appearance.
String businessHoursSummary(BusinessCalendar calendar) {
  if (calendar.isAlwaysOn) {
    return 'No day is open, so targets run around the clock. Closing every '
        'day does not stop the clock, it removes the calendar from the '
        'calculation entirely.';
  }
  final hours = calendar.weeklyHours;
  final rounded = hours == hours.roundToDouble()
      ? hours.round().toString()
      : hours.toStringAsFixed(1);
  return '$rounded hours a week, in ${calendar.timezone}. Targets count only '
      'the time inside them.';
}
