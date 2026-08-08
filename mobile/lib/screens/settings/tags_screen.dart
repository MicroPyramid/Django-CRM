import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/tag.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import '../../widgets/common/badge.dart';

/// The labels shared across accounts, contacts, leads, deals, tickets and
/// tasks.
///
/// Reading is open to every member; creating, turning off, turning back on and
/// merging are admin-only and the server answers 403 to anyone else. The
/// controls follow that rule so a member is not offered an action that cannot
/// work. Hiding them is not what keeps a member out.
///
/// Nothing here deletes a tag, because nothing in `tags_views.py` does. Every
/// removal path is a soft archive.
class TagsScreen extends ConsumerWidget {
  const TagsScreen({super.key});

  Future<void> _create(BuildContext context, WidgetRef ref) async {
    final name = await showDialog<String>(
      context: context,
      builder: (context) => const _NewTagDialog(),
    );
    if (name == null || !context.mounted) return;
    final result = await ref.read(tagSettingsProvider.notifier).createTag(name);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          result.error ??
              // Not the same event, and the difference is not cosmetic: a
              // revived tag comes back with its old colour and description, and
              // every record that carried it before still carries it.
              (result.revived
                  ? 'That tag already existed and was turned back on'
                  : 'Tag added'),
        ),
      ),
    );
  }

  Future<void> _turnOff(BuildContext context, WidgetRef ref, Tag tag) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Turn off ${tag.name}?'),
        content: Text(tagArchiveExplanation(tag)),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Leave it on'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: AppColors.danger600),
            child: const Text('Turn off'),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;
    final error = await ref
        .read(tagSettingsProvider.notifier)
        .archiveTag(tag.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? 'Tag turned off')));
  }

  /// No confirm. Turning a tag back on restores nothing that was destroyed and
  /// is undone by the button next to it.
  Future<void> _turnOn(BuildContext context, WidgetRef ref, Tag tag) async {
    final error = await ref
        .read(tagSettingsProvider.notifier)
        .restoreTag(tag.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? 'Tag turned back on')));
  }

  Future<void> _merge(
    BuildContext context,
    WidgetRef ref, {
    required Tag from,
    required Tag into,
  }) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Merge ${from.name} into ${into.name}?'),
        content: Text(tagMergeExplanation(from: from, into: into)),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Keep both'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: AppColors.danger600),
            child: const Text('Merge'),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;
    final result = await ref
        .read(tagSettingsProvider.notifier)
        .mergeTags(from: from.id, into: into.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          result.error ??
              '${result.moved} ${result.moved == 1 ? 'record' : 'records'} '
                  'moved to ${into.name}',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(tagSettingsProvider);
    final isAdmin = ref.watch(isOrgAdminProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Tags'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          if (isAdmin)
            IconButton(
              icon: const Icon(LucideIcons.plus),
              tooltip: 'New tag',
              onPressed: () => _create(context, ref),
            ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => _ErrorState(
          onRetry: () => ref.read(tagSettingsProvider.notifier).refresh(),
        ),
        data: (state) {
          if (state.tags.isEmpty) return _EmptyState(isAdmin: isAdmin);
          return RefreshIndicator(
            onRefresh: () => ref.read(tagSettingsProvider.notifier).refresh(),
            child: ListView(
              padding: const EdgeInsets.only(bottom: 96),
              children: [
                _Summary(state: state),
                // Shown to everyone, actionable by an admin, matching the web.
                // A member seeing that two tags overlap is worth something on
                // its own: they can stop using one of them today.
                for (final group in state.duplicates)
                  _DuplicateBanner(
                    group: group,
                    canEdit: isAdmin,
                    onMerge: (from) =>
                        _merge(context, ref, from: from, into: group.keep),
                  ),
                const _ListHeader(),
                for (final tag in state.tags)
                  _TagRow(
                    tag: tag,
                    canEdit: isAdmin,
                    onTurnOff: () => _turnOff(context, ref, tag),
                    onTurnOn: () => _turnOn(context, ref, tag),
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

/// The name, and nothing else.
///
/// Colour and description are settable through the API and offered by neither
/// client: the model has eighteen named hues and this app renders tags in its
/// own palette.
class _NewTagDialog extends StatefulWidget {
  const _NewTagDialog();

  @override
  State<_NewTagDialog> createState() => _NewTagDialogState();
}

class _NewTagDialogState extends State<_NewTagDialog> {
  final TextEditingController _name = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  void _submit() {
    final problem = validateTagName(_name.text);
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    Navigator.of(context).pop(_name.text.trim());
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('New tag'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: _name,
            autofocus: true,
            textCapitalization: TextCapitalization.sentences,
            maxLength: 50,
            onSubmitted: (_) => _submit(),
            decoration: InputDecoration(
              labelText: 'Tag name',
              border: const OutlineInputBorder(),
              counterText: '',
              errorText: _error,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Tags are shared across every record type, so the first ones are '
            'worth naming carefully.',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        TextButton(onPressed: _submit, child: const Text('Create')),
      ],
    );
  }
}

class _Summary extends StatelessWidget {
  const _Summary({required this.state});

  final TagsState state;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      margin: const EdgeInsets.only(bottom: 1),
      // Wrap, not Row: three stat pairs with their labels do not fit on one
      // line at 390px, and a Row would overflow rather than wrap.
      child: Wrap(
        spacing: 20,
        runSpacing: 10,
        children: [
          _Stat(value: '${state.active}', label: 'in use'),
          _Stat(value: '${state.unused}', label: 'applied to nothing'),
          _Stat(value: '${state.archived}', label: 'turned off'),
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

/// "Renewal and Renewals look like the same tag", with the merge offered.
class _DuplicateBanner extends StatelessWidget {
  const _DuplicateBanner({
    required this.group,
    required this.canEdit,
    required this.onMerge,
  });

  final TagDuplicateGroup group;
  final bool canEdit;
  final void Function(Tag from) onMerge;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(LucideIcons.merge, size: 18, color: AppColors.warning600),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  '${group.all.map((t) => t.name).join(' and ')} look like the '
                  'same tag',
                  style: AppTypography.body.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            '${group.all.map((t) => '${t.name} is on ${t.used} '
                '${t.used == 1 ? 'record' : 'records'}').join('; ')}. '
            'Anyone filtering by one of them misses the other.',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          if (canEdit) ...[
            const SizedBox(height: 10),
            // One control per tag being emptied rather than one Merge for the
            // group: the endpoint takes a pair, and a group of three needs a
            // person to say which two go where.
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final loser in group.merge)
                  SizedBox(
                    height: 40,
                    child: OutlinedButton(
                      onPressed: () => onMerge(loser),
                      child: Text(
                        group.merge.length > 1
                            ? 'Merge ${loser.name}'
                            : 'Merge into ${group.keep.name}',
                      ),
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

class _ListHeader extends StatelessWidget {
  const _ListHeader();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 22, 16, 8),
      child: Text(
        'ALL TAGS',
        style: AppTypography.overline.copyWith(
          color: AppColors.textSecondary,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

class _TagRow extends StatelessWidget {
  const _TagRow({
    required this.tag,
    required this.canEdit,
    required this.onTurnOff,
    required this.onTurnOn,
  });

  final Tag tag;
  final bool canEdit;
  final VoidCallback onTurnOff;
  final VoidCallback onTurnOn;

  @override
  Widget build(BuildContext context) {
    final used = tag.used;
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
                child: Text(
                  tag.name,
                  style: AppTypography.body.copyWith(
                    fontWeight: FontWeight.w600,
                    color: tag.isActive
                        ? AppColors.textPrimary
                        : AppColors.textSecondary,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text(
                '$used',
                style: AppTypography.body.copyWith(
                  fontWeight: FontWeight.w600,
                  color: used == 0
                      ? AppColors.textTertiary
                      : AppColors.textPrimary,
                ),
              ),
            ],
          ),
          if (tag.description.isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              tag.description,
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
          if (used > 0) ...[
            const SizedBox(height: 4),
            Text(
              tagUsageSummary(tag),
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          ],
          if (!tag.isActive || used == 0) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                if (!tag.isActive)
                  StatusBadge(label: 'Turned off', color: AppColors.gray500),
                // Only meaningful while a tag is still being offered. On a
                // turned-off one "Unused" is not news.
                if (tag.isActive && used == 0)
                  StatusBadge(label: 'Unused', color: AppColors.warning600),
              ],
            ),
          ],
          if (canEdit) ...[
            const SizedBox(height: 10),
            SizedBox(
              height: 40,
              child: tag.isActive
                  ? OutlinedButton(
                      onPressed: onTurnOff,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.danger600,
                      ),
                      child: const Text('Turn off'),
                    )
                  : OutlinedButton(
                      onPressed: onTurnOn,
                      child: const Text('Turn back on'),
                    ),
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
        'Turning a tag off hides it from the pickers and leaves it on the '
        'records that already carry it. Nothing is removed, and you can turn a '
        'tag back on at any time.',
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
            Icon(LucideIcons.tags, size: 40, color: AppColors.textTertiary),
            const SizedBox(height: 16),
            Text(
              'No tags yet',
              style: AppTypography.h3,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              isAdmin
                  ? 'Tags are shared across every record type, so the first '
                        'one is worth naming carefully.'
                  : 'An administrator adds these.',
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
              'Could not load the tags',
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
