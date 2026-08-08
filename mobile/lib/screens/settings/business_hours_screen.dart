import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/business_calendar.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import 'business_hours_form_sheet.dart';

/// The calendar every response target is measured against.
///
/// Closed days and holidays are shown rather than omitted: a blank row for
/// Saturday reads as missing data, "Closed" reads as a decision.
///
/// Reading is open to every member. Every write is admin-only and the server
/// answers 403 to anyone else, so hiding the controls is UX rather than a
/// guard.
class BusinessHoursScreen extends ConsumerWidget {
  const BusinessHoursScreen({super.key});

  Future<void> _editHours(BuildContext context, WidgetRef ref) async {
    final calendar = ref.read(businessHoursProvider).value;
    if (calendar == null) return;
    final result = await showBusinessHoursFormSheet(context, calendar);
    if (result == null || !context.mounted) return;
    final error = await ref
        .read(businessHoursProvider.notifier)
        .saveHours(
          days: result.days,
          name: result.name,
          timezone: result.timezone,
        );
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? 'Business hours saved')));
  }

  Future<void> _addHoliday(BuildContext context, WidgetRef ref) async {
    final calendar = ref.read(businessHoursProvider).value;
    if (calendar == null) return;
    final result = await showHolidayFormSheet(context, calendar);
    if (result == null || !context.mounted) return;
    final outcome = await ref
        .read(businessHoursProvider.notifier)
        .addHoliday(date: result.date, name: result.name);
    if (!context.mounted) return;
    // Three outcomes, not two. A duplicate date answers 200 with the row that
    // was already there, so the name typed in was thrown away and calling that
    // "added" would be a lie the admin acts on.
    final message = outcome.error != null
        ? outcome.error!
        : outcome.existingName != null
        ? holidayAlreadyExistedMessage(outcome.existingName!)
        : 'Holiday added';
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _removeHoliday(
    BuildContext context,
    WidgetRef ref,
    BusinessHoliday holiday,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Remove ${holiday.name}?'),
        content: const Text(holidayRemovalExplanation),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Keep it'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: AppColors.danger600),
            child: const Text('Remove'),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;
    final error = await ref
        .read(businessHoursProvider.notifier)
        .removeHoliday(holiday.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? 'Holiday removed')));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(businessHoursProvider);
    final isAdmin = ref.watch(isOrgAdminProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Business hours'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          if (isAdmin && async.hasValue)
            IconButton(
              icon: const Icon(LucideIcons.pencil),
              tooltip: 'Edit hours',
              onPressed: () => _editHours(context, ref),
            ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => _ErrorState(
          onRetry: () => ref.read(businessHoursProvider.notifier).refresh(),
        ),
        data: (calendar) => RefreshIndicator(
          onRefresh: () => ref.read(businessHoursProvider.notifier).refresh(),
          child: ListView(
            padding: const EdgeInsets.only(bottom: 96),
            children: [
              _Summary(calendar: calendar),
              const _SectionHeader('The week'),
              for (final day in calendar.days) _DayRow(day: day),
              _SectionHeader(
                'Holidays',
                action: isAdmin
                    ? TextButton.icon(
                        onPressed: () => _addHoliday(context, ref),
                        icon: const Icon(LucideIcons.plus, size: 16),
                        label: const Text('Add'),
                      )
                    : null,
              ),
              if (calendar.holidays.isEmpty)
                const _NoHolidays()
              else
                for (final holiday in calendar.holidays)
                  _HolidayRow(
                    holiday: holiday,
                    canEdit: isAdmin,
                    onRemove: () => _removeHoliday(context, ref, holiday),
                  ),
              const _Footnote(),
            ],
          ),
        ),
      ),
    );
  }
}

class _Summary extends StatelessWidget {
  const _Summary({required this.calendar});

  final BusinessCalendar calendar;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      margin: const EdgeInsets.only(bottom: 1),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            calendar.name,
            style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          Text(
            businessHoursSummary(calendar),
            style: AppTypography.caption.copyWith(
              color: calendar.isAlwaysOn
                  ? AppColors.warning600
                  : AppColors.textSecondary,
            ),
          ),
          if (calendar.isAlwaysOn) ...[
            const SizedBox(height: 12),
            // The one state where the screen has to contradict what its own
            // rows imply, so it gets a banner rather than a footnote.
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.warning50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.warning200),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    LucideIcons.triangleAlert,
                    size: 18,
                    color: AppColors.warning600,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Every day below reads Closed, and a four-hour target '
                      'still expires four hours after the ticket arrives, '
                      'weekend or not. Open at least one day to make the '
                      'calendar count.',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _DayRow extends StatelessWidget {
  const _DayRow({required this.day});

  final BusinessDay day;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Row(
        children: [
          Expanded(
            child: Text(
              day.day,
              style: AppTypography.body.copyWith(
                color: day.isClosed
                    ? AppColors.textSecondary
                    : AppColors.textPrimary,
              ),
            ),
          ),
          Text(
            // Named, not blank. A blank cell reads as missing data.
            day.isClosed ? 'Closed' : '${day.open} to ${day.close}',
            style: AppTypography.body.copyWith(
              color: day.isClosed
                  ? AppColors.textTertiary
                  : AppColors.textPrimary,
              fontWeight: day.isClosed ? FontWeight.w400 : FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

class _HolidayRow extends StatelessWidget {
  const _HolidayRow({
    required this.holiday,
    required this.canEdit,
    required this.onRemove,
  });

  final BusinessHoliday holiday;
  final bool canEdit;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: EdgeInsets.fromLTRB(16, 10, canEdit ? 4 : 16, 10),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(holiday.name, style: AppTypography.body),
                const SizedBox(height: 2),
                Text(
                  humanHolidayDate(holiday.date),
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          if (canEdit)
            IconButton(
              icon: const Icon(LucideIcons.trash2, size: 18),
              tooltip: 'Remove this holiday',
              color: AppColors.danger600,
              onPressed: onRemove,
            ),
        ],
      ),
    );
  }
}

class _NoHolidays extends StatelessWidget {
  const _NoHolidays();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Text(
        'No holidays set. Targets keep running on public holidays.',
        style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title, {this.action});

  final String title;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(16, 22, action != null ? 8 : 16, 8),
      child: Row(
        children: [
          Expanded(
            child: Text(
              title.toUpperCase(),
              style: AppTypography.overline.copyWith(
                color: AppColors.textSecondary,
                letterSpacing: 1.2,
              ),
            ),
          ),
          ?action,
        ],
      ),
    );
  }
}

class _Footnote extends StatelessWidget {
  const _Footnote();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 0),
      child: Text(
        'A ticket that arrives after closing starts its clock when the week '
        'next opens, so the hours in between do not spend a target. Service '
        'analytics is measured on this calendar too. A holiday is a full day '
        'off in this timezone, which is separate from the organization '
        'timezone.',
        style: AppTypography.caption.copyWith(color: AppColors.textTertiary),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              LucideIcons.triangleAlert,
              size: 40,
              color: AppColors.textTertiary,
            ),
            const SizedBox(height: 16),
            Text(
              'Could not load the business hours',
              style: AppTypography.body,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            OutlinedButton(onPressed: onRetry, child: const Text('Try again')),
          ],
        ),
      ),
    );
  }
}
