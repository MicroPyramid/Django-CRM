import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/reopen_policy.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import 'reopen_form_sheet.dart';

/// Whether a customer's reply brings a closed ticket back.
///
/// Four fields, and the only question that matters is what number goes in the
/// window. Nothing answers that except how customers actually behave, so the
/// three 30-day figures sit above the settings rather than below them.
///
/// **Admin-only to read, not just to write.** `ReopenPolicyView.get` calls
/// `is_org_admin` before it answers, unlike every other read in this cluster,
/// so a member is told why rather than shown a failed request.
class ReopenScreen extends ConsumerWidget {
  const ReopenScreen({super.key});

  Future<void> _edit(BuildContext context, WidgetRef ref) async {
    final policy = ref.read(reopenPolicyProvider).value;
    if (policy == null) return;
    final payload = await showReopenFormSheet(context, policy);
    if (payload == null || !context.mounted) return;
    final error = await ref
        .read(reopenPolicyProvider.notifier)
        .savePolicy(payload);
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? 'Reopen policy saved')));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isAdmin = ref.watch(isOrgAdminProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Reopen policy'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          if (isAdmin)
            IconButton(
              icon: const Icon(LucideIcons.pencil),
              tooltip: 'Edit policy',
              onPressed: () => _edit(context, ref),
            ),
        ],
      ),
      body: isAdmin ? const _AdminBody() : const _MemberNotice(),
    );
  }
}

/// The read itself is gated, so a member never issues it.
class _MemberNotice extends StatelessWidget {
  const _MemberNotice();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(LucideIcons.lock, size: 40, color: AppColors.textTertiary),
            const SizedBox(height: 16),
            Text(
              'Administrators only',
              style: AppTypography.h3,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'The reopen policy and the reply figures behind it are visible '
              'to administrators. Ask one of yours whether replies to closed '
              'tickets bring them back.',
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _AdminBody extends ConsumerWidget {
  const _AdminBody();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(reopenPolicyProvider);
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (_, _) => _ErrorState(
        onRetry: () => ref.read(reopenPolicyProvider.notifier).refresh(),
      ),
      data: (policy) => RefreshIndicator(
        onRefresh: () => ref.read(reopenPolicyProvider.notifier).refresh(),
        child: ListView(
          padding: const EdgeInsets.only(bottom: 96),
          children: [
            _Summary(policy: policy),
            const _SectionHeader('Last 30 days'),
            _Metrics(policy: policy),
            const _SectionHeader('The rule'),
            _SettingRow(
              label: 'Reopen on customer reply',
              detail:
                  'Off means a reply is filed on the closed ticket and '
                  'nothing else happens.',
              value: policy.isEnabled ? 'On' : 'Off',
            ),
            _SettingRow(
              label: 'Window',
              detail:
                  'Counted from when the ticket was closed, in calendar '
                  'days.',
              value: '${policy.windowDays} days',
            ),
            _SettingRow(
              label: 'Comes back as',
              detail:
                  'Has to be a status that counts as open, or the ticket '
                  'would close again on arrival.',
              value: policy.reopenToStatus,
            ),
            _SettingRow(
              label: 'Tell the assignee',
              detail: 'The person the ticket was assigned to when it closed.',
              value: policy.notifyAssigned ? 'Yes' : 'No',
            ),
            _Footnote(isEnabled: policy.isEnabled),
          ],
        ),
      ),
    );
  }
}

class _Summary extends StatelessWidget {
  const _Summary({required this.policy});

  final ReopenPolicy policy;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      margin: const EdgeInsets.only(bottom: 1),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Icon(
              LucideIcons.rotateCcw,
              size: 18,
              color: policy.isEnabled
                  ? AppColors.textSecondary
                  : AppColors.warning600,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(reopenSummary(policy), style: AppTypography.body),
          ),
        ],
      ),
    );
  }
}

class _Metrics extends StatelessWidget {
  const _Metrics({required this.policy});

  final ReopenPolicy policy;

  @override
  Widget build(BuildContext context) {
    final caveat = missedWindowCaveat(policy);
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 22,
            runSpacing: 12,
            children: [
              _Stat(
                value: '${policy.reopenedLast30d}',
                label: 'reopened',
                tone: AppColors.textPrimary,
              ),
              _Stat(
                // "n/a" rather than 0 while the policy is off: the figure is
                // a zero by construction there, and a plain 0 reads as
                // reassurance about the one thing certainly happening.
                value: caveat != null
                    ? 'n/a'
                    : '${policy.repliesAfterWindow30d}',
                label: 'missed the window',
                tone: caveat == null && policy.repliesAfterWindow30d > 0
                    ? AppColors.warning600
                    : AppColors.textPrimary,
              ),
              _Stat(
                value: '${policy.medianDaysToReply}d',
                label: 'median reply',
                tone: AppColors.textPrimary,
              ),
            ],
          ),
          if (caveat != null) ...[
            const SizedBox(height: 12),
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
                    LucideIcons.mailX,
                    size: 18,
                    color: AppColors.warning600,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      caveat,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ] else if (policy.repliesAfterWindow30d > 0) ...[
            const SizedBox(height: 12),
            Text(
              '${policy.repliesAfterWindow30d} replies landed on tickets '
              'closed more than ${policy.windowDays} days earlier, so no '
              'ticket came back and nobody was told. Those customers are '
              'still waiting.',
              style: AppTypography.caption.copyWith(
                color: AppColors.warning600,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.value, required this.label, required this.tone});

  final String value;
  final String label;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: AppTypography.h2.copyWith(
            fontWeight: FontWeight.w600,
            color: tone,
          ),
        ),
        Text(
          label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
      ],
    );
  }
}

class _SettingRow extends StatelessWidget {
  const _SettingRow({
    required this.label,
    required this.detail,
    required this.value,
  });

  final String label;
  final String detail;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
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
              const SizedBox(width: 12),
              Text(
                value,
                style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 3),
          Text(
            detail,
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 22, 16, 8),
      child: Text(
        title.toUpperCase(),
        style: AppTypography.overline.copyWith(
          color: AppColors.textSecondary,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

class _Footnote extends StatelessWidget {
  const _Footnote({required this.isEnabled});

  final bool isEnabled;

  @override
  Widget build(BuildContext context) {
    // Present tense either way, so with the policy off this cannot be written
    // as though a reply still reopened anything.
    final what = isEnabled
        ? 'A reopened ticket is the same ticket, keeping its history and its '
              'number, so first response and resolution are still measured '
              'from the original open.'
        : 'Turned on, a reply inside the window would bring the same ticket '
              'back rather than open a new one, keeping its history and its '
              'number.';
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 0),
      child: Text(
        '$what Which addresses accept replies at all is set in inbound email.',
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
              'Could not load the reopen policy',
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
