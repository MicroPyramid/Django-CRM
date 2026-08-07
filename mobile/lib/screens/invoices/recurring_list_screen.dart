import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/recurring_invoice.dart';
import '../../providers/invoice_extras_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/common/badge.dart';
import 'invoice_format.dart';
import 'invoice_shell.dart';

/// Recurring billing schedules, with the one write a phone should have:
/// pausing a schedule that is about to bill a client it should not.
class RecurringListScreen extends ConsumerWidget {
  const RecurringListScreen({super.key});

  static const _filters = <bool?>[null, true, false];
  static const _labels = ['All', 'Running', 'Paused'];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(recurringProvider);
    final active = ref.watch(recurringProvider.notifier).activeFilter;

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Recurring'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.plus),
            tooltip: 'New schedule',
            onPressed: () => context.push(AppRoutes.recurringNew),
          ),
        ],
      ),
      body: Column(
        children: [
          InvoiceFilterChips(
            labels: _labels,
            selected: _filters.indexOf(active),
            onSelected: (i) => ref
                .read(recurringProvider.notifier)
                .filterByActive(_filters[i]),
          ),
          Expanded(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (_, _) => InvoiceErrorState(
                message: 'Could not load schedules',
                onRetry: () => ref.read(recurringProvider.notifier).refresh(),
              ),
              data: (schedules) {
                if (schedules.isEmpty) {
                  return const InvoiceEmptyState(
                    icon: LucideIcons.repeat,
                    message: 'No recurring schedules',
                    detail:
                        'Set one up on the web to bill the same client '
                        'on a cadence.',
                  );
                }
                return RefreshIndicator(
                  onRefresh: () =>
                      ref.read(recurringProvider.notifier).refresh(),
                  child: ListView.builder(
                    padding: const EdgeInsets.only(bottom: 96),
                    itemCount: schedules.length,
                    itemBuilder: (context, i) =>
                        _ScheduleCard(schedule: schedules[i]),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ScheduleCard extends ConsumerStatefulWidget {
  const _ScheduleCard({required this.schedule});

  final RecurringInvoice schedule;

  @override
  ConsumerState<_ScheduleCard> createState() => _ScheduleCardState();
}

class _ScheduleCardState extends ConsumerState<_ScheduleCard> {
  bool _busy = false;

  /// Confirmed before sending, because the endpoint flips whatever is stored
  /// rather than taking a target state. A mis-tap on a running schedule stops
  /// a client being billed, and nothing on screen would say so afterwards.
  Future<void> _toggle() async {
    final schedule = widget.schedule;
    final pausing = schedule.isActive;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(pausing ? 'Pause this schedule?' : 'Resume this schedule?'),
        content: Text(
          pausing
              ? 'No invoice will be generated for ${schedule.title} until it is '
                    'resumed.'
              : 'Invoices for ${schedule.title} will start generating again on '
                    'its cadence.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Leave it'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(pausing ? 'Pause' : 'Resume'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _busy = true);
    final error = await ref
        .read(recurringProvider.notifier)
        .toggle(schedule.id);
    if (!mounted) return;
    setState(() => _busy = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error ?? (pausing ? 'Schedule paused' : 'Schedule resumed'),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final schedule = widget.schedule;
    final nextRun = schedule.effectiveNextRun;

    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      schedule.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.body.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      schedule.accountName ??
                          (schedule.clientName.isEmpty
                              ? 'No account'
                              : schedule.clientName),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Text(
                money(schedule.totalAmount, schedule.currencyInfo.symbol),
                style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 4,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              StatusBadge(
                label: schedule.isActive ? 'Running' : 'Paused',
                color: schedule.isActive
                    ? AppColors.success600
                    : AppColors.gray500,
              ),
              Text(
                schedule.frequencyLabel,
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              // Only while running. The server keeps next_generation_date on a
              // paused schedule, so printing it unqualified would promise an
              // invoice that is not coming.
              if (nextRun != null)
                Text(
                  'next ${DateFormat('d MMM').format(nextRun)}',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              if (schedule.autoSend)
                StatusBadge(label: 'auto-sends', color: AppColors.warning600),
            ],
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: 40,
            child: OutlinedButton(
              onPressed: _busy ? null : _toggle,
              child: Text(schedule.isActive ? 'Pause' : 'Resume'),
            ),
          ),
        ],
      ),
    );
  }
}
