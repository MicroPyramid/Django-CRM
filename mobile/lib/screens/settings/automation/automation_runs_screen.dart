import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../../core/theme/theme.dart';
import '../../../data/models/automation.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/automation_provider.dart';
import '../../../services/automation_text.dart';
import '../../../services/run_time.dart';

const _pageSize = 20;

/// One rule's runs from the last 30 days, newest first, each opening to what
/// every step did. Read-only; paged by 20 with Newer and Older.
class AutomationRunsScreen extends ConsumerStatefulWidget {
  const AutomationRunsScreen({super.key, required this.ruleId});

  final String ruleId;

  @override
  ConsumerState<AutomationRunsScreen> createState() =>
      _AutomationRunsScreenState();
}

class _AutomationRunsScreenState extends ConsumerState<AutomationRunsScreen> {
  int _offset = 0;

  @override
  Widget build(BuildContext context) {
    ref.listen(selectedOrgProvider.select((o) => o?.id), (prev, next) {
      if (prev != next && _offset != 0) setState(() => _offset = 0);
    });
    if (!ref.watch(isOrgAdminProvider)) {
      return _shell('Runs', const _Notice.member());
    }
    final rule = ref.watch(automationRuleProvider(widget.ruleId));
    final name = rule.isLoading || rule.hasError ? null : rule.value?.name;
    final title = name == null || name.isEmpty ? 'Runs' : name;
    final runs = ref.watch(
      automationRunsProvider((id: widget.ruleId, offset: _offset)),
    );
    final page = runs.isLoading || runs.hasError ? null : runs.value;
    if (page == null) {
      return _shell(
        title,
        runs.hasError && !runs.isLoading
            ? _Notice.error(
                onRetry: _retry,
                onNewer: _offset > 0 ? _newer : null,
              )
            : const Center(child: CircularProgressIndicator()),
      );
    }
    return _shell(title, _body(page));
  }

  void _newer() =>
      setState(() => _offset = (_offset - _pageSize).clamp(0, _offset));

  void _retry() {
    ref.invalidate(automationRuleProvider(widget.ruleId));
    ref.invalidate(
      automationRunsProvider((id: widget.ruleId, offset: _offset)),
    );
  }

  Widget _shell(String title, Widget body) => Scaffold(
    backgroundColor: AppColors.surfaceDim,
    appBar: AppBar(
      title: Text(title),
      backgroundColor: AppColors.surface,
      elevation: 0,
      scrolledUnderElevation: 1,
    ),
    body: body,
  );

  Widget _body(RunPage page) {
    if (page.runs.isEmpty && _offset == 0) {
      return const _Notice.empty();
    }
    final past = page.runs.isEmpty;
    final hasNewer = _offset > 0;
    final hasOlder = _offset + _pageSize < page.count;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          'Runs from the last 30 days, newest first.',
          style: AppTypography.bodySmall.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 12),
        if (past)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Text(
              'No more runs.',
              textAlign: TextAlign.center,
              style: AppTypography.body,
            ),
          ),
        for (final run in page.runs) ...[
          _RunCard(run: run),
          const SizedBox(height: 8),
        ],
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: hasNewer ? _newer : null,
                child: const Text('Newer'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: OutlinedButton(
                onPressed: hasOlder
                    ? () => setState(() => _offset += _pageSize)
                    : null,
                child: const Text('Older'),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _RunCard extends StatelessWidget {
  const _RunCard({required this.run});

  final AutomationRun run;

  @override
  Widget build(BuildContext context) {
    final at = run.createdAt;
    final when = at == null ? '' : runTimeLabel(at);
    final by = run.triggeredByRuleName;
    final head = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                when,
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ),
            const SizedBox(width: 8),
            _RunPill(status: run.status),
          ],
        ),
        _RecordName(run: run),
        if (run.reason.isNotEmpty)
          Text(run.reason, style: AppTypography.bodySmall),
        if (by != null)
          Text(
            'Set off by "$by"',
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
      ],
    );
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Material(
        type: MaterialType.transparency,
        child: run.steps.isEmpty
            ? ListTile(title: head)
            : Theme(
                data: Theme.of(
                  context,
                ).copyWith(dividerColor: Colors.transparent),
                child: ExpansionTile(
                  key: PageStorageKey('run-${run.id}'),
                  title: head,
                  expandedCrossAxisAlignment: CrossAxisAlignment.start,
                  childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                  children: [for (final s in run.steps) _StepRow(step: s)],
                ),
              ),
      ),
    );
  }
}

class _RecordName extends StatelessWidget {
  const _RecordName({required this.run});

  final AutomationRun run;

  @override
  Widget build(BuildContext context) {
    final name = run.recordName.isEmpty ? 'Record' : run.recordName;
    final path = run.recordId.isEmpty
        ? null
        : recordPath(run.objectKey, run.recordId);
    if (path == null) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Text(
          name,
          style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
        ),
      );
    }
    return TextButton(
      onPressed: () => context.push(path),
      style: TextButton.styleFrom(
        minimumSize: const Size(44, 44),
        padding: EdgeInsets.zero,
        alignment: Alignment.centerLeft,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
      child: Text(
        name,
        textAlign: TextAlign.left,
        style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
      ),
    );
  }
}

Color _runColor(String status) => switch (status) {
  'done' => AppColors.success600,
  'failed' => AppColors.danger600,
  _ => AppColors.textSecondary,
};

String _runLabel(String status) => switch (status) {
  'done' => 'Done',
  'failed' => 'Failed',
  'skipped' => 'Skipped',
  _ => status,
};

class _RunPill extends StatelessWidget {
  const _RunPill({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final color = _runColor(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        _runLabel(status),
        style: AppTypography.caption.copyWith(
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _StepRow extends StatelessWidget {
  const _StepRow({required this.step});

  final RunStep step;

  @override
  Widget build(BuildContext context) {
    final (icon, color, label) = switch (step.status) {
      'done' => (LucideIcons.check, AppColors.success600, null),
      'undone' => (LucideIcons.undo2, AppColors.warning600, 'Undone'),
      'failed' => (LucideIcons.circleX, AppColors.danger600, 'Failed'),
      _ => (LucideIcons.minus, AppColors.textSecondary, 'Skipped'),
    };
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Icon(
              icon,
              size: 16,
              color: color,
              semanticLabel: label ?? 'Done',
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(step.text, style: AppTypography.bodySmall),
                if (label != null)
                  Text(
                    label,
                    style: AppTypography.caption.copyWith(
                      color: color,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice.member()
    : icon = LucideIcons.lock,
      title = null,
      message = 'Only an organization admin can see automation rules.',
      onRetry = null,
      onNewer = null;

  const _Notice.empty()
    : icon = LucideIcons.history,
      title = 'No runs yet',
      message =
          'When this rule runs, each run and what it did shows here for 30 days.',
      onRetry = null,
      onNewer = null;

  const _Notice.error({required VoidCallback this.onRetry, this.onNewer})
    : icon = LucideIcons.triangleAlert,
      title = null,
      message = 'Could not load the runs';

  final IconData icon;
  final String? title;
  final String message;
  final VoidCallback? onRetry;
  final VoidCallback? onNewer;

  @override
  Widget build(BuildContext context) => Center(
    child: SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 40, color: AppColors.textTertiary),
          const SizedBox(height: 16),
          if (title != null) ...[
            Text(title!, style: AppTypography.h3, textAlign: TextAlign.center),
            const SizedBox(height: 8),
          ],
          Text(message, style: AppTypography.body, textAlign: TextAlign.center),
          if (onRetry != null) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 12,
              children: [
                if (onNewer != null)
                  OutlinedButton(
                    onPressed: onNewer,
                    child: const Text('Newer'),
                  ),
                OutlinedButton(
                  onPressed: onRetry,
                  child: const Text('Try again'),
                ),
              ],
            ),
          ],
        ],
      ),
    ),
  );
}
