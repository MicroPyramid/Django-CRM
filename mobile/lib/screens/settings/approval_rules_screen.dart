import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/approval_rule.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import '../../widgets/common/badge.dart';
import 'approval_rule_form_sheet.dart';

/// What gates a ticket close, and who can clear it.
///
/// The approvals queue answers "what is waiting on me". This answers "what will
/// be gated next time, and by whom": the same rows, a different question.
///
/// **A ticket is gated by one rule**, the most specific that matches it, so the
/// list is a set of gates and fallbacks rather than a stack. Two rules with
/// identical conditions are not equals either: the newest takes every case, so
/// the older never runs however live it looks.
///
/// Reading is open to every member; every write is admin-only and the server
/// answers 403 to anyone else.
class ApprovalRulesScreen extends ConsumerWidget {
  const ApprovalRulesScreen({super.key});

  Future<void> _edit(
    BuildContext context,
    WidgetRef ref,
    ApprovalRule? existing,
  ) async {
    final payload = await showApprovalRuleFormSheet(
      context,
      existing: existing,
    );
    if (payload == null || !context.mounted) return;
    final notifier = ref.read(approvalRulesProvider.notifier);
    final error = existing == null
        ? await notifier.createRule(payload)
        : await notifier.updateRule(existing.id, payload);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error ?? (existing == null ? 'Rule added' : 'Rule saved'),
        ),
      ),
    );
  }

  Future<void> _turnOff(
    BuildContext context,
    WidgetRef ref,
    ApprovalRule rule,
  ) async {
    final error = await ref
        .read(approvalRulesProvider.notifier)
        .deactivateRule(rule.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? 'Rule turned off')));
  }

  Future<void> _turnOn(
    BuildContext context,
    WidgetRef ref,
    ApprovalRule rule,
  ) async {
    final error = await ref
        .read(approvalRulesProvider.notifier)
        .activateRule(rule.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? 'Rule turned on')));
  }

  /// Delete, or turn off. Which one is the server's decision, so the dialog
  /// names both outcomes and the snackbar reports the one that happened.
  Future<void> _delete(
    BuildContext context,
    WidgetRef ref,
    ApprovalRule rule,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Delete ${rule.name}?'),
        content: const Text(approvalRuleDeleteExplanation),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Keep it'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: AppColors.danger600),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;
    final result = await ref
        .read(approvalRulesProvider.notifier)
        .deleteRule(rule.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          result.error ?? approvalRuleDeleteResult(turnedOff: result.turnedOff),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(approvalRulesProvider);
    final isAdmin = ref.watch(isOrgAdminProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Approval rules'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          if (isAdmin)
            IconButton(
              icon: const Icon(LucideIcons.plus),
              tooltip: 'New rule',
              onPressed: () => _edit(context, ref, null),
            ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => _ErrorState(
          onRetry: () => ref.read(approvalRulesProvider.notifier).refresh(),
        ),
        data: (state) {
          if (state.rules.isEmpty) return _EmptyState(isAdmin: isAdmin);
          final shadowed = state.shadowed;
          return RefreshIndicator(
            onRefresh: () => ref.read(approvalRulesProvider.notifier).refresh(),
            child: ListView(
              padding: const EdgeInsets.only(bottom: 96),
              children: [
                _Summary(state: state),
                for (final rule in state.rules)
                  _RuleRow(
                    rule: rule,
                    beatenBy: shadowed.contains(rule.id)
                        ? shadowedBy(rule, state.rules)
                        : null,
                    canEdit: isAdmin,
                    onEdit: () => _edit(context, ref, rule),
                    onTurnOff: () => _turnOff(context, ref, rule),
                    onTurnOn: () => _turnOn(context, ref, rule),
                    onDelete: () => _delete(context, ref, rule),
                  ),
                const _Footnote(),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _Summary extends StatelessWidget {
  const _Summary({required this.state});

  final ApprovalRulesState state;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      margin: const EdgeInsets.only(bottom: 1),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 20,
            runSpacing: 10,
            children: [
              _Stat(value: '${state.active}', label: 'active'),
              _Stat(
                value: '${state.count - state.active}',
                label: 'turned off',
              ),
              _Stat(value: '${state.pending}', label: 'waiting on them'),
            ],
          ),
          if (state.stranding > 0) ...[
            const SizedBox(height: 14),
            _Warning(
              text: state.stranding == 1
                  ? 'One active rule can be cleared by nobody. What it gates '
                        'cannot be closed by anyone.'
                  : '${state.stranding} active rules can be cleared by nobody. '
                        'What they gate cannot be closed by anyone.',
            ),
          ],
        ],
      ),
    );
  }
}

class _Warning extends StatelessWidget {
  const _Warning({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
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
              text,
              style: AppTypography.caption.copyWith(
                color: AppColors.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: AppTypography.h2.copyWith(fontWeight: FontWeight.w600),
        ),
        Text(
          label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
      ],
    );
  }
}

class _RuleRow extends StatelessWidget {
  const _RuleRow({
    required this.rule,
    required this.beatenBy,
    required this.canEdit,
    required this.onEdit,
    required this.onTurnOff,
    required this.onTurnOn,
    required this.onDelete,
  });

  final ApprovalRule rule;

  /// The rule that takes this one's tickets, when one does. Non-null means this
  /// row never runs.
  final ApprovalRule? beatenBy;

  final bool canEdit;
  final VoidCallback onEdit;
  final VoidCallback onTurnOff;
  final VoidCallback onTurnOn;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            rule.name,
            style: AppTypography.body.copyWith(
              fontWeight: FontWeight.w600,
              color: rule.isActive
                  ? AppColors.textPrimary
                  : AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Gates ${rule.matchSentence}',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            'Cleared by ${rule.approverSentence}',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              if (!rule.isActive)
                StatusBadge(label: 'Turned off', color: AppColors.gray500),
              if (rule.clearableByNobody)
                StatusBadge(
                  label: 'Nobody can clear',
                  color: AppColors.danger600,
                ),
              if (beatenBy != null)
                StatusBadge(label: 'Never runs', color: AppColors.danger600),
              if (rule.pendingCount > 0)
                StatusBadge(
                  label: '${rule.pendingCount} waiting',
                  color: AppColors.gray500,
                ),
            ],
          ),
          if (rule.clearableByNobody) ...[
            const SizedBox(height: 8),
            Text(
              'This organization has admins and members. There is no manager '
              'role. With no named approvers, the first ticket this gates '
              'cannot be closed by anyone. Name approvers, or set it to admin.',
              style: AppTypography.caption.copyWith(
                color: AppColors.warning600,
              ),
            ),
          ],
          if (beatenBy != null) ...[
            const SizedBox(height: 8),
            Text(
              '${beatenBy!.name} gates exactly the same tickets and was written '
              'later. One rule gates a close, the most specific match, and the '
              'newest wins between equals, so this one never runs.',
              style: AppTypography.caption.copyWith(
                color: AppColors.warning600,
              ),
            ),
          ],
          if (canEdit) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                SizedBox(
                  height: 40,
                  child: OutlinedButton(
                    onPressed: onEdit,
                    child: const Text('Edit'),
                  ),
                ),
                SizedBox(
                  height: 40,
                  child: rule.isActive
                      ? OutlinedButton(
                          onPressed: onTurnOff,
                          child: const Text('Turn off'),
                        )
                      : OutlinedButton(
                          onPressed: onTurnOn,
                          child: const Text('Turn on'),
                        ),
                ),
                SizedBox(
                  height: 40,
                  child: OutlinedButton(
                    onPressed: onDelete,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.danger600,
                    ),
                    child: const Text('Delete'),
                  ),
                ),
              ],
            ),
          ],
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
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      child: Text(
        'A ticket is gated by one rule, the most specific that matches it. The '
        'others are fallbacks for the tickets it misses. Whoever asked for the '
        'close can never be the one who clears it, whatever a rule says.',
        style: AppTypography.caption.copyWith(color: AppColors.textTertiary),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.isAdmin});

  final bool isAdmin;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              LucideIcons.circleCheckBig,
              size: 40,
              color: AppColors.textTertiary,
            ),
            const SizedBox(height: 16),
            Text(
              'No approval rules',
              style: AppTypography.h3,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              isAdmin
                  ? 'Tickets close without anyone signing off. Add a rule to '
                        'gate the closes that need a second pair of eyes.'
                  : 'Tickets close without anyone signing off. An '
                        'administrator sets these up.',
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
              'Could not load the approval rules',
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
