import 'package:flutter/material.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/business_calendar.dart';

/// What the week form hands back.
typedef BusinessHoursDraft = ({
  List<BusinessDay> days,
  String name,
  String timezone,
});

/// What the holiday form hands back.
typedef HolidayDraft = ({String date, String name});

/// Edit the week, the calendar name and its timezone.
///
/// One sheet for all seven days, because the serializer validates the whole
/// week and a per-day sheet would make "Monday needs both times" arrive after
/// the sheet that could fix it had closed.
Future<BusinessHoursDraft?> showBusinessHoursFormSheet(
  BuildContext context,
  BusinessCalendar calendar,
) {
  return showModalBottomSheet<BusinessHoursDraft>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _BusinessHoursFormSheet(calendar: calendar),
  );
}

class _BusinessHoursFormSheet extends StatefulWidget {
  const _BusinessHoursFormSheet({required this.calendar});

  final BusinessCalendar calendar;

  @override
  State<_BusinessHoursFormSheet> createState() =>
      _BusinessHoursFormSheetState();
}

class _BusinessHoursFormSheetState extends State<_BusinessHoursFormSheet> {
  late final TextEditingController _name;
  late final TextEditingController _timezone;

  /// One row per weekday. A closed day keeps a sensible time so re-opening it
  /// does not hand back a blank field, and `closed` is what decides whether the
  /// times are sent at all.
  late List<({BusinessDay day, bool closed, String open, String close})> _rows;

  String? _error;

  @override
  void initState() {
    super.initState();
    _name = TextEditingController(text: widget.calendar.name);
    _timezone = TextEditingController(text: widget.calendar.timezone);
    _rows = [
      for (final day in widget.calendar.days)
        (
          day: day,
          closed: day.isClosed,
          open: day.open ?? '09:00',
          close: day.close ?? '17:00',
        ),
    ];
  }

  @override
  void dispose() {
    _name.dispose();
    _timezone.dispose();
    super.dispose();
  }

  List<BusinessDay> get _days => [
    for (final row in _rows)
      row.closed
          ? BusinessDay(day: row.day.day, key: row.day.key)
          : BusinessDay(
              day: row.day.day,
              key: row.day.key,
              open: row.open,
              close: row.close,
            ),
  ];

  Future<void> _pickTime(int index, {required bool isOpen}) async {
    final row = _rows[index];
    final current = _parse(isOpen ? row.open : row.close);
    final picked = await showTimePicker(context: context, initialTime: current);
    if (picked == null) return;
    final value = _format(picked);
    setState(() {
      _rows[index] = (
        day: row.day,
        closed: row.closed,
        open: isOpen ? value : row.open,
        close: isOpen ? row.close : value,
      );
    });
  }

  void _submit() {
    final days = _days;
    final problem = businessHoursProblem(
      days: days,
      name: _name.text,
      timezone: _timezone.text,
    );
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    Navigator.of(
      context,
    ).pop((days: days, name: _name.text, timezone: _timezone.text));
  }

  @override
  Widget build(BuildContext context) {
    // Live, not on submit: closing the last open day is a change of meaning,
    // not a mistake, so it is announced while it is still being made.
    final wouldBeAlwaysOn = _days.every((d) => d.hours == 0);

    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Edit business hours',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _name,
              maxLength: 100,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Calendar name',
                border: OutlineInputBorder(),
                counterText: '',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _timezone,
              maxLength: 64,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: 'Timezone',
                helperText: 'An IANA name, like Asia/Kolkata',
                border: OutlineInputBorder(),
                counterText: '',
              ),
            ),
            const SizedBox(height: 16),
            const _SectionLabel('The week'),
            for (final (index, row) in _rows.indexed)
              _DayEditor(
                label: row.day.day,
                closed: row.closed,
                open: row.open,
                close: row.close,
                onClosed: (closed) => setState(() {
                  _rows[index] = (
                    day: row.day,
                    closed: closed,
                    open: row.open,
                    close: row.close,
                  );
                }),
                onOpenTap: () => _pickTime(index, isOpen: true),
                onCloseTap: () => _pickTime(index, isOpen: false),
              ),
            if (wouldBeAlwaysOn) ...[
              const SizedBox(height: 4),
              Text(
                'With no day open, targets run around the clock. The engine '
                'drops a calendar that never opens rather than treating it as '
                'permanently shut.',
                style: AppTypography.caption.copyWith(
                  color: AppColors.warning600,
                ),
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(
                _error!,
                style: AppTypography.caption.copyWith(
                  color: AppColors.danger600,
                ),
              ),
            ],
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Cancel'),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: FilledButton(
                      onPressed: _submit,
                      child: const Text('Save hours'),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// "09:30" to a TimeOfDay, defaulting to 09:00 rather than throwing on a value
/// the API sent in a shape this did not expect.
TimeOfDay _parse(String value) {
  final parts = value.split(':');
  final hour = parts.isNotEmpty ? int.tryParse(parts[0]) : null;
  final minute = parts.length > 1 ? int.tryParse(parts[1]) : null;
  return TimeOfDay(hour: hour ?? 9, minute: minute ?? 0);
}

/// TimeOfDay to "HH:MM", which DRF parses back into a TimeField.
String _format(TimeOfDay time) =>
    '${time.hour.toString().padLeft(2, '0')}:'
    '${time.minute.toString().padLeft(2, '0')}';

/// One weekday: a closed switch and two time buttons that stack under it.
///
/// Time buttons rather than text fields, because a phone's time picker is the
/// control people already know and typing "9" into a free field is how a
/// half-set day gets saved.
class _DayEditor extends StatelessWidget {
  const _DayEditor({
    required this.label,
    required this.closed,
    required this.open,
    required this.close,
    required this.onClosed,
    required this.onOpenTap,
    required this.onCloseTap,
  });

  final String label;
  final bool closed;
  final String open;
  final String close;
  final ValueChanged<bool> onClosed;
  final VoidCallback onOpenTap;
  final VoidCallback onCloseTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 12),
      decoration: BoxDecoration(
        color: AppColors.gray50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.gray200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  label,
                  style: AppTypography.body.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              Text(
                closed ? 'Closed' : 'Open',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              Switch(value: !closed, onChanged: (on) => onClosed(!on)),
            ],
          ),
          if (!closed)
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 44,
                    child: OutlinedButton(
                      onPressed: onOpenTap,
                      child: Text('From $open'),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: SizedBox(
                    height: 44,
                    child: OutlinedButton(
                      onPressed: onCloseTap,
                      child: Text('To $close'),
                    ),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
}

/// Add a holiday.
///
/// Warns before the write when the date is already on the calendar, because the
/// backend answers that with the existing row and 200 rather than an error, and
/// throws the typed name away.
Future<HolidayDraft?> showHolidayFormSheet(
  BuildContext context,
  BusinessCalendar calendar,
) {
  return showModalBottomSheet<HolidayDraft>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _HolidayFormSheet(calendar: calendar),
  );
}

class _HolidayFormSheet extends StatefulWidget {
  const _HolidayFormSheet({required this.calendar});

  final BusinessCalendar calendar;

  @override
  State<_HolidayFormSheet> createState() => _HolidayFormSheetState();
}

class _HolidayFormSheetState extends State<_HolidayFormSheet> {
  final TextEditingController _name = TextEditingController();
  DateTime? _date;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  String? get _iso {
    final date = _date;
    if (date == null) return null;
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _date ?? now,
      firstDate: DateTime(now.year - 1),
      lastDate: DateTime(now.year + 5),
    );
    if (picked == null) return;
    setState(() => _date = picked);
  }

  void _submit() {
    final iso = _iso;
    if (iso == null) {
      setState(() => _error = 'Pick a date.');
      return;
    }
    if (_name.text.trim().isEmpty) {
      setState(() => _error = 'Give the day a name, so the list reads.');
      return;
    }
    Navigator.of(context).pop((date: iso, name: _name.text));
  }

  @override
  Widget build(BuildContext context) {
    final iso = _iso;
    final duplicate = iso == null
        ? null
        : holidayDuplicateWarning(widget.calendar, iso);

    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Add a holiday',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 6),
            Text(
              'A full day off in ${widget.calendar.timezone}. Targets stop for '
              'the whole of it.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 48,
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _pickDate,
                icon: const Icon(LucideIcons.calendar, size: 18),
                label: Text(
                  iso == null ? 'Pick a date' : humanHolidayDate(iso),
                ),
              ),
            ),
            if (duplicate != null) ...[
              const SizedBox(height: 8),
              Text(
                duplicate,
                style: AppTypography.caption.copyWith(
                  color: AppColors.warning600,
                ),
              ),
            ],
            const SizedBox(height: 12),
            TextField(
              controller: _name,
              maxLength: 100,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Name',
                hintText: 'Christmas Day',
                border: OutlineInputBorder(),
                counterText: '',
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(
                _error!,
                style: AppTypography.caption.copyWith(
                  color: AppColors.danger600,
                ),
              ),
            ],
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Cancel'),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: FilledButton(
                      onPressed: _submit,
                      child: const Text('Add holiday'),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        text.toUpperCase(),
        style: AppTypography.overline.copyWith(
          color: AppColors.textSecondary,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}
