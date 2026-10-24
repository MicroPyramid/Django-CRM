import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/lead_source.dart';
import '../../providers/auth_provider.dart';
import '../../providers/lead_sources_provider.dart';
import '../../widgets/common/badge.dart';

/// Where leads come from: the org's list, which every lead, contact and deal
/// picker reads.
///
/// Reading is open to every member. Adding, renaming, retiring and reordering
/// are admin-only, and the server answers 403 to anyone else. There is no
/// delete: a retired source stays on the records that have it.
class LeadSourcesScreen extends ConsumerWidget {
  const LeadSourcesScreen({super.key});

  Future<void> _add(BuildContext context, WidgetRef ref) async {
    final label = await _askLabel(context, title: 'New source');
    if (label == null || !context.mounted) return;
    final error = await ref.read(leadSourcesProvider.notifier).add(label);
    if (context.mounted) _snack(context, error ?? 'Source added');
  }

  Future<void> _rename(
    BuildContext context,
    WidgetRef ref,
    LeadSource source,
  ) async {
    final label = await _askLabel(
      context,
      title: 'Rename ${source.label}',
      initial: source.label,
    );
    if (label == null || label == source.label || !context.mounted) return;
    final error = await ref
        .read(leadSourcesProvider.notifier)
        .rename(source.id, label);
    if (context.mounted) _snack(context, error ?? 'Source renamed');
  }

  Future<void> _setActive(
    BuildContext context,
    WidgetRef ref,
    LeadSource source,
  ) async {
    final error = await ref
        .read(leadSourcesProvider.notifier)
        .setActive(source.id, !source.isActive);
    if (!context.mounted) return;
    _snack(
      context,
      error ?? (source.isActive ? 'Source retired' : 'Source restored'),
    );
  }

  Future<void> _move(
    BuildContext context,
    WidgetRef ref,
    LeadSource source,
    int step,
  ) async {
    final error = await ref
        .read(leadSourcesProvider.notifier)
        .move(source.key, step);
    if (error != null && context.mounted) _snack(context, error);
  }

  void _snack(BuildContext context, String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(leadSourcesProvider);
    final answer = shownLeadSources(async);
    final canEdit = ref.watch(isOrgAdminProvider) && (answer?.offered ?? false);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Lead sources'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          if (canEdit)
            IconButton(
              icon: const Icon(LucideIcons.plus),
              tooltip: 'New source',
              onPressed: () => _add(context, ref),
            ),
        ],
      ),
      body: async.hasError && !async.isLoading
          ? _ErrorState(
              onRetry: () => ref.read(leadSourcesProvider.notifier).refresh(),
            )
          : answer == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () => ref.read(leadSourcesProvider.notifier).refresh(),
              child: ListView(
                padding: const EdgeInsets.only(bottom: 96),
                children: [
                  if (!answer.offered) const _NotOffered(),
                  for (final (i, source) in answer.sources.indexed)
                    _SourceRow(
                      source: source,
                      canEdit: canEdit,
                      onRename: () => _rename(context, ref, source),
                      onToggle: () => _setActive(context, ref, source),
                      onUp: i == 0
                          ? null
                          : () => _move(context, ref, source, -1),
                      onDown: i == answer.sources.length - 1
                          ? null
                          : () => _move(context, ref, source, 1),
                    ),
                  if (answer.offered)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                      child: Text(
                        'A retired source stays on the leads, contacts and '
                        'deals that have it, and cannot be picked for new '
                        'ones. Sources are never deleted.',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.textTertiary,
                        ),
                      ),
                    ),
                ],
              ),
            ),
    );
  }
}

/// The label typed in, trimmed, or null when cancelled or empty.
Future<String?> _askLabel(
  BuildContext context, {
  required String title,
  String initial = '',
}) async {
  final label = await showDialog<String>(
    context: context,
    builder: (_) => _LabelDialog(title: title, initial: initial),
  );
  final trimmed = label?.trim() ?? '';
  return trimmed.isEmpty ? null : trimmed;
}

/// Owns its controller, so it is disposed after the closing animation rather
/// than during it.
class _LabelDialog extends StatefulWidget {
  const _LabelDialog({required this.title, required this.initial});

  final String title;
  final String initial;

  @override
  State<_LabelDialog> createState() => _LabelDialogState();
}

class _LabelDialogState extends State<_LabelDialog> {
  late final TextEditingController _controller = TextEditingController(
    text: widget.initial,
  );

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.title),
      content: TextField(
        controller: _controller,
        autofocus: true,
        maxLength: 64,
        textCapitalization: TextCapitalization.sentences,
        decoration: const InputDecoration(
          labelText: 'Label',
          hintText: 'Spring open day',
        ),
        onSubmitted: (v) => Navigator.pop(context, v),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, _controller.text),
          child: const Text('Save'),
        ),
      ],
    );
  }
}

class _SourceRow extends StatelessWidget {
  const _SourceRow({
    required this.source,
    required this.canEdit,
    required this.onRename,
    required this.onToggle,
    this.onUp,
    this.onDown,
  });

  final LeadSource source;
  final bool canEdit;
  final VoidCallback onRename;
  final VoidCallback onToggle;
  final VoidCallback? onUp;
  final VoidCallback? onDown;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 12, 8, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Text(
                      source.label,
                      style: AppTypography.body.copyWith(
                        fontWeight: FontWeight.w600,
                        color: source.isActive
                            ? AppColors.textPrimary
                            : AppColors.textSecondary,
                      ),
                    ),
                    if (!source.isActive)
                      StatusBadge(label: 'Retired', color: AppColors.gray500),
                  ],
                ),
              ),
              if (canEdit) ...[
                IconButton(
                  icon: const Icon(LucideIcons.arrowUp, size: 18),
                  tooltip: 'Move ${source.label} up',
                  onPressed: onUp,
                ),
                IconButton(
                  icon: const Icon(LucideIcons.arrowDown, size: 18),
                  tooltip: 'Move ${source.label} down',
                  onPressed: onDown,
                ),
              ],
            ],
          ),
          if (canEdit) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                SizedBox(
                  height: 44,
                  child: OutlinedButton(
                    onPressed: onRename,
                    child: const Text('Rename'),
                  ),
                ),
                SizedBox(
                  height: 44,
                  child: OutlinedButton(
                    onPressed: onToggle,
                    child: Text(source.isActive ? 'Retire' : 'Restore'),
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

class _NotOffered extends StatelessWidget {
  const _NotOffered();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
      child: Text(
        'This server has a fixed list of lead sources, so they cannot be '
        'changed here. A newer server lets an admin edit them.',
        style: AppTypography.body.copyWith(color: AppColors.textSecondary),
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
      child: SingleChildScrollView(
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
              'Could not load the lead sources',
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
