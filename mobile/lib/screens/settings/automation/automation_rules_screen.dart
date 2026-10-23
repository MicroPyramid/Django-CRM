import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../../core/theme/theme.dart';
import '../../../data/models/automation.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/automation_provider.dart';
import '../../../providers/org_modules_provider.dart';
import '../../../routes/app_router.dart';
import '../../../services/automation_text.dart';
import 'status_pill.dart';

/// The automation rules list. Admin only: the API refuses a member, so the
/// screen says so without asking.
class AutomationRulesScreen extends ConsumerStatefulWidget {
  const AutomationRulesScreen({super.key});

  @override
  ConsumerState<AutomationRulesScreen> createState() =>
      _AutomationRulesScreenState();
}

class _AutomationRulesScreenState extends ConsumerState<AutomationRulesScreen> {
  bool _moving = false;

  Future<void> _move(String id, String direction) async {
    final messenger = ScaffoldMessenger.of(context);
    setState(() => _moving = true);
    final message = await ref
        .read(automationRulesProvider.notifier)
        .move(id, direction);
    if (!mounted) return;
    setState(() => _moving = false);
    if (message != null) {
      messenger.showSnackBar(SnackBar(content: Text(message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final isAdmin = ref.watch(isOrgAdminProvider);
    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Automation'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          if (isAdmin)
            IconButton(
              tooltip: 'New rule',
              icon: const Icon(LucideIcons.plus),
              onPressed: () => context.push(AppRoutes.settingsAutomationNew),
            ),
        ],
      ),
      body: isAdmin
          ? _Body(moving: _moving, onMove: _move)
          : const _MemberNotice(),
    );
  }
}

class _Body extends ConsumerWidget {
  const _Body({required this.moving, required this.onMove});

  final bool moving;
  final Future<void> Function(String id, String direction) onMove;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(automationRulesProvider);
    final answer = shownAutomationRules(async);
    final loaded = ref.watch(automationCatalogueProvider);
    final catalogue = loaded.isLoading || loaded.hasError ? null : loaded.value;
    if (answer == null) {
      if (async.hasError && !async.isLoading) {
        if (automationNotOffered(async)) {
          return const _ErrorState(
            message: 'Automation rules are not available here.',
          );
        }
        return _ErrorState(
          message: 'Could not load automation rules',
          onRetry: () => ref.read(automationRulesProvider.notifier).refresh(),
        );
      }
      return const Center(child: CircularProgressIndicator());
    }
    final rules = answer.rules;
    final modules = ref.watch(shownModulesProvider);
    final paused = [
      for (final r in rules)
        if (r.status == 'paused') r,
    ];
    return RefreshIndicator(
      onRefresh: () => ref.read(automationRulesProvider.notifier).refresh(),
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 48),
        children: [
          if (rules.isEmpty) const _Empty(),
          for (final r in paused)
            _PausedNote(row: r, byModule: pausedByModule(r, modules)),
          for (var i = 0; i < rules.length; i++)
            _RuleCard(
              row: rules[i],
              catalogue: catalogue,
              canUp: !moving && i > 0,
              canDown: !moving && i < rules.length - 1,
              onMove: (d) => onMove(rules[i].id, d),
            ),
        ],
      ),
    );
  }
}

class _PausedNote extends StatelessWidget {
  const _PausedNote({required this.row, required this.byModule});

  final AutomationRuleRow row;
  final bool byModule;

  @override
  Widget build(BuildContext context) {
    final why = statusText(row) ?? '${statusLabel(row.status)}.';
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.warning50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.warning100),
      ),
      child: Text(
        byModule
            ? modulePausedNote(row)
            : '"${row.name}": $why Switch it on again to take it over.',
        style: AppTypography.caption.copyWith(color: AppColors.textPrimary),
      ),
    );
  }
}

class _RuleCard extends StatelessWidget {
  const _RuleCard({
    required this.row,
    required this.catalogue,
    required this.canUp,
    required this.canDown,
    required this.onMove,
  });

  final AutomationRuleRow row;
  final AutomationCatalogue? catalogue;
  final bool canUp;
  final bool canDown;
  final void Function(String direction) onMove;

  @override
  Widget build(BuildContext context) {
    final c = catalogue;
    final object = c == null ? null : objectOf(c, row.objectKey);
    final trigger = c != null
        ? triggerSentence(row, c)
        : (row.trigger.event == 'created' ? 'Created' : 'Updated');
    final note = row.status == 'paused' ? null : statusText(row);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: () => context.push(AppRoutes.settingsAutomationRule(row.id)),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 4, 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        row.name,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.body.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        '${object?.label ?? row.objectKey}, $trigger',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 6),
                      // The pill shares a wrapping line with the runs, so a
                      // long status at a large font moves down, not off.
                      Wrap(
                        spacing: 8,
                        runSpacing: 4,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          AutomationStatusPill(status: row.status),
                          Text(
                            runsLabel(row),
                            style: AppTypography.caption.copyWith(
                              color: row.failures7d > 0
                                  ? AppColors.danger600
                                  : AppColors.textTertiary,
                            ),
                          ),
                        ],
                      ),
                      if (note != null) ...[
                        const SizedBox(height: 6),
                        Text(
                          note,
                          style: AppTypography.caption.copyWith(
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(width: 4),
                Column(
                  children: [
                    _MoveButton(
                      tooltip: 'Move up',
                      icon: LucideIcons.chevronUp,
                      onPressed: canUp ? () => onMove('up') : null,
                    ),
                    _MoveButton(
                      tooltip: 'Move down',
                      icon: LucideIcons.chevronDown,
                      onPressed: canDown ? () => onMove('down') : null,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _MoveButton extends StatelessWidget {
  const _MoveButton({
    required this.tooltip,
    required this.icon,
    required this.onPressed,
  });

  final String tooltip;
  final IconData icon;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: tooltip,
    onPressed: onPressed,
    icon: Icon(icon, size: 20),
    constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
    padding: EdgeInsets.zero,
  );
}

class _Empty extends StatelessWidget {
  const _Empty();

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(8, 32, 8, 16),
    child: Column(
      children: [
        Icon(LucideIcons.zap, size: 40, color: AppColors.textTertiary),
        const SizedBox(height: 14),
        Text('No rules yet', style: AppTypography.h3),
        const SizedBox(height: 8),
        Text(
          'A rule does something when a record is created or changes: assign '
          'it, create a task, notify people, or set a field.',
          style: AppTypography.body.copyWith(color: AppColors.textSecondary),
          textAlign: TextAlign.center,
        ),
      ],
    ),
  );
}

class _MemberNotice extends StatelessWidget {
  const _MemberNotice();

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(LucideIcons.lock, size: 40, color: AppColors.textTertiary),
          const SizedBox(height: 16),
          Text(
            'Only an organization admin can see automation rules.',
            style: AppTypography.body,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    ),
  );
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => Center(
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
          Text(message, style: AppTypography.body, textAlign: TextAlign.center),
          if (onRetry != null) ...[
            const SizedBox(height: 16),
            OutlinedButton(onPressed: onRetry, child: const Text('Try again')),
          ],
        ],
      ),
    ),
  );
}
