import 'package:bottle_crm/data/models/business_calendar.dart';
import 'package:flutter_test/flutter_test.dart';

/// A calendar as `BusinessCalendarSerializer` sends it: fourteen flat fields,
/// times as "HH:MM:SS", a null pair meaning closed.
Map<String, dynamic> calendarJson({
  String id = 'c1',
  String name = 'Default',
  String timezone = 'UTC',
  bool isDefault = true,
  Map<String, String?> hours = const {
    'monday': '09:00:00/17:00:00',
    'tuesday': '09:00:00/17:00:00',
    'wednesday': '09:00:00/17:00:00',
    'thursday': '09:00:00/17:00:00',
    'friday': '09:00:00/17:00:00',
  },
  List<Map<String, dynamic>> holidays = const [],
}) {
  final json = <String, dynamic>{
    'id': id,
    'name': name,
    'timezone': timezone,
    'is_default': isDefault,
    'holidays': holidays,
  };
  for (final (_, key) in businessWeekdays) {
    final window = hours[key];
    final parts = window?.split('/');
    json['${key}_open'] = parts?.first;
    json['${key}_close'] = parts?.last;
  }
  return json;
}

BusinessCalendar build({
  Map<String, String?>? hours,
  List<Map<String, dynamic>> holidays = const [],
  String timezone = 'UTC',
}) => BusinessCalendar.fromJson(
  hours == null
      ? calendarJson(holidays: holidays, timezone: timezone)
      : calendarJson(hours: hours, holidays: holidays, timezone: timezone),
);

void main() {
  group('BusinessCalendar.fromJson', () {
    test('folds the flat fields into seven days, Monday first', () {
      final calendar = build();
      expect(calendar.days.length, 7);
      expect(calendar.days.first.day, 'Monday');
      expect(calendar.days.last.day, 'Sunday');
    });

    test('trims the seconds the API sends', () {
      final calendar = build();
      expect(calendar.days.first.open, '09:00');
      expect(calendar.days.first.close, '17:00');
    });

    test('a null pair is a closed day, not a zero-length one', () {
      final calendar = build();
      final sunday = calendar.days.last;
      expect(sunday.isClosed, isTrue);
      expect(sunday.open, isNull);
    });

    test('reads holidays', () {
      final calendar = build(
        holidays: const [
          {'id': 'h1', 'date': '2026-12-25', 'name': 'Christmas'},
        ],
      );
      expect(calendar.holidays.single.name, 'Christmas');
      expect(calendar.holidays.single.date, '2026-12-25');
    });

    test('a calendar with no holidays key parses rather than throwing', () {
      final json = calendarJson()..remove('holidays');
      expect(BusinessCalendar.fromJson(json).holidays, isEmpty);
    });
  });

  group('hours', () {
    test('a normal day counts its span', () {
      expect(build().days.first.hours, 8);
      expect(build().weeklyHours, 40);
    });

    test('half hours count', () {
      final calendar = build(hours: const {'monday': '09:30:00/17:00:00'});
      expect(calendar.weeklyHours, 7.5);
    });

    test('a day whose close is not after its open counts as shut', () {
      // The serializer refuses this on write, so it can only arrive from older
      // data, and the walker treats it as closed via `close_t <= open_t`.
      final calendar = build(hours: const {'monday': '17:00:00/09:00:00'});
      expect(calendar.days.first.hours, 0);
      expect(calendar.openDayCount, 0);
    });
  });

  group('isAlwaysOn', () {
    test('is false for an ordinary week', () {
      expect(build().isAlwaysOn, isFalse);
    });

    test('is true when every day is closed', () {
      // The finding: `_has_any_open_window` false means the calendar is dropped
      // and the clock runs on the wall, so this is 24/7 rather than never.
      final calendar = build(hours: const {});
      expect(calendar.isAlwaysOn, isTrue);
    });

    test('one open day is enough to make the calendar count', () {
      final calendar = build(hours: const {'sunday': '10:00:00/11:00:00'});
      expect(calendar.isAlwaysOn, isFalse);
    });

    test('a backwards day does not count as open', () {
      final calendar = build(hours: const {'monday': '09:00:00/09:00:00'});
      expect(calendar.isAlwaysOn, isTrue);
    });
  });

  group('businessHoursSummary', () {
    test('says the clock runs when nothing is open', () {
      final text = businessHoursSummary(build(hours: const {}));
      expect(text, contains('around the clock'));
      expect(text, isNot(contains('hours a week')));
    });

    test('names the weekly total and the timezone otherwise', () {
      final text = businessHoursSummary(build(timezone: 'Asia/Kolkata'));
      expect(text, contains('40 hours a week'));
      expect(text, contains('Asia/Kolkata'));
    });

    test('does not render a trailing .0 on a whole number', () {
      expect(businessHoursSummary(build()), isNot(contains('40.0')));
    });
  });

  group('businessHoursPayload', () {
    test('sends the fourteen flat fields', () {
      final body = businessHoursPayload(
        days: build().days,
        name: 'Default',
        timezone: 'UTC',
      );
      for (final (_, key) in businessWeekdays) {
        expect(body.containsKey('${key}_open'), isTrue, reason: key);
        expect(body.containsKey('${key}_close'), isTrue, reason: key);
      }
    });

    test('a closed day goes as a null pair, never a blank string', () {
      final body = businessHoursPayload(
        days: build().days,
        name: 'Default',
        timezone: 'UTC',
      );
      expect(body['sunday_open'], isNull);
      expect(body['sunday_close'], isNull);
    });

    test('never sends is_default, which is read-only server-side', () {
      final body = businessHoursPayload(
        days: build().days,
        name: 'Default',
        timezone: 'UTC',
      );
      expect(body.containsKey('is_default'), isFalse);
      expect(body.containsKey('id'), isFalse);
      expect(body.containsKey('holidays'), isFalse);
    });

    test('trims the name and the timezone', () {
      final body = businessHoursPayload(
        days: build().days,
        name: '  Support  ',
        timezone: ' UTC ',
      );
      expect(body['name'], 'Support');
      expect(body['timezone'], 'UTC');
    });
  });

  group('businessHoursProblem', () {
    List<BusinessDay> daysWith(String key, String? open, String? close) => [
      for (final day in build().days)
        if (day.key == key)
          BusinessDay(day: day.day, key: day.key, open: open, close: close)
        else
          day,
    ];

    test('accepts an ordinary week', () {
      expect(
        businessHoursProblem(
          days: build().days,
          name: 'Default',
          timezone: 'UTC',
        ),
        isNull,
      );
    });

    test('names the day when only one time is set', () {
      final problem = businessHoursProblem(
        days: daysWith('wednesday', '09:00', null),
        name: 'Default',
        timezone: 'UTC',
      );
      expect(problem, contains('Wednesday'));
    });

    test('names the day when close is not after open', () {
      final problem = businessHoursProblem(
        days: daysWith('friday', '17:00', '09:00'),
        name: 'Default',
        timezone: 'UTC',
      );
      expect(problem, contains('Friday'));
      expect(problem, contains('past midnight'));
    });

    test('refuses equal times, which the serializer also refuses', () {
      expect(
        businessHoursProblem(
          days: daysWith('monday', '09:00', '09:00'),
          name: 'Default',
          timezone: 'UTC',
        ),
        isNotNull,
      );
    });

    test('accepts a week with every day closed', () {
      // Legal, and the reason the screen has a banner rather than a block: the
      // engine accepts it and reads it as 24/7.
      expect(
        businessHoursProblem(
          days: build(hours: const {}).days,
          name: 'Default',
          timezone: 'UTC',
        ),
        isNull,
      );
    });

    test('needs a name and a timezone', () {
      expect(
        businessHoursProblem(days: build().days, name: '  ', timezone: 'UTC'),
        contains('name'),
      );
      expect(
        businessHoursProblem(days: build().days, name: 'Default', timezone: ''),
        contains('IANA'),
      );
    });
  });

  group('holidays', () {
    final calendar = build(
      holidays: const [
        {'id': 'h1', 'date': '2026-12-25', 'name': 'Xmas'},
      ],
    );

    test('holidayOn finds a stored date', () {
      expect(calendar.holidayOn('2026-12-25')!.name, 'Xmas');
      expect(calendar.holidayOn('2026-12-26'), isNull);
    });

    test('warns before adding a date already stored, and names it', () {
      // The POST answers 200 with the row that was already there, so the name
      // typed into the form is discarded.
      final warning = holidayDuplicateWarning(calendar, '2026-12-25');
      expect(warning, contains('Xmas'));
      expect(warning, contains('25 Dec 2026'));
    });

    test('says nothing for a free date', () {
      expect(holidayDuplicateWarning(calendar, '2026-12-26'), isNull);
    });

    test('the after-the-fact message names what was kept', () {
      expect(holidayAlreadyExistedMessage('Xmas'), contains('Xmas'));
      expect(holidayAlreadyExistedMessage('Xmas'), contains('Nothing changed'));
    });

    test('the payload trims the name and passes the date through', () {
      final body = holidayPayload(date: '2026-12-25', name: '  Xmas  ');
      expect(body, {'date': '2026-12-25', 'name': 'Xmas'});
    });

    test('humanHolidayDate falls back to the input it cannot parse', () {
      expect(humanHolidayDate('2026-01-05'), '5 Jan 2026');
      expect(humanHolidayDate('not a date'), 'not a date');
    });
  });
}
