import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/custom_object.dart';
import '../../providers/custom_objects_provider.dart';

/// One link field on a record form. Only the records the user can open are
/// held here; hidden ones are counted, never named, and never sent.
class LinkFieldPicker extends StatelessWidget {
  const LinkFieldPicker({
    super.key,
    required this.field,
    required this.value,
    required this.selected,
    required this.onChanged,
  });

  final ObjectField field;
  final LinkValue value;
  final List<LinkedRecord> selected;
  final ValueChanged<List<LinkedRecord>> onChanged;

  bool get _many => field.many ?? true;

  Future<void> _add(BuildContext context) async {
    final picked = await showLinkSearchSheet(
      context,
      title: field.label,
      target: field.target ?? '',
      taken: {for (final r in selected) r.id},
    );
    if (picked == null) return;
    onChanged(_many ? [...selected, picked] : [picked]);
  }

  @override
  Widget build(BuildContext context) {
    final label = Text(
      field.isRequired ? '${field.label} *' : field.label,
      style: AppTypography.label.copyWith(color: AppColors.textSecondary),
    );
    if (value.readOnly) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          label,
          const SizedBox(height: 6),
          Text("Linked to a record you can't open", style: AppTypography.body),
        ],
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        label,
        const SizedBox(height: 6),
        if (selected.isNotEmpty)
          Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              for (final r in selected)
                InputChip(
                  label: Text(r.name.isEmpty ? r.id : r.name),
                  deleteIcon: const Icon(LucideIcons.x, size: 16),
                  deleteButtonTooltipMessage: 'Remove ${r.name}',
                  onDeleted: () => onChanged([
                    for (final s in selected)
                      if (s.id != r.id) s,
                  ]),
                ),
            ],
          ),
        if (_many && value.hidden > 0)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              "and ${value.hidden} you can't open",
              style: AppTypography.bodySmall.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ),
        TextButton.icon(
          style: TextButton.styleFrom(
            minimumSize: const Size(44, 44),
            alignment: Alignment.centerLeft,
          ),
          onPressed: () => _add(context),
          icon: const Icon(LucideIcons.plus, size: 16),
          label: const Text('Add'),
        ),
      ],
    );
  }
}

/// Searches the server for records of [target] and pops the one tapped.
Future<LinkedRecord?> showLinkSearchSheet(
  BuildContext context, {
  required String title,
  required String target,
  Set<String> taken = const {},
}) => showModalBottomSheet<LinkedRecord>(
  context: context,
  backgroundColor: AppColors.surface,
  isScrollControlled: true,
  shape: const RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
  ),
  builder: (_) => DraggableScrollableSheet(
    initialChildSize: 0.7,
    minChildSize: 0.4,
    maxChildSize: 0.95,
    expand: false,
    builder: (_, controller) => LinkSearchSheet(
      title: title,
      target: target,
      taken: taken,
      controller: controller,
    ),
  ),
);

class LinkSearchSheet extends ConsumerStatefulWidget {
  const LinkSearchSheet({
    super.key,
    required this.title,
    required this.target,
    required this.taken,
    required this.controller,
  });

  final String title;
  final String target;
  final Set<String> taken;
  final ScrollController controller;

  @override
  ConsumerState<LinkSearchSheet> createState() => LinkSearchSheetState();
}

class LinkSearchSheetState extends ConsumerState<LinkSearchSheet> {
  String _query = '';
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  void _onChanged(String text) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      if (mounted) setState(() => _query = text.trim());
    });
  }

  @override
  Widget build(BuildContext context) {
    final results = ref.watch(
      linkTargetSearchProvider((target: widget.target, query: _query)),
    );
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 20, 16, 12),
          child: Row(
            children: [
              Expanded(child: Text(widget.title, style: AppTypography.h3)),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
          child: TextField(
            onChanged: _onChanged,
            decoration: const InputDecoration(
              hintText: 'Search',
              prefixIcon: Icon(LucideIcons.search, size: 18),
            ),
          ),
        ),
        Expanded(
          child: results.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, _) => Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Could not search. Try again.'),
                  TextButton(
                    style: TextButton.styleFrom(
                      minimumSize: const Size(44, 44),
                    ),
                    onPressed: () => ref.invalidate(
                      linkTargetSearchProvider((
                        target: widget.target,
                        query: _query,
                      )),
                    ),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            ),
            data: (rows) {
              final shown = [
                for (final r in rows)
                  if (!widget.taken.contains(r.id)) r,
              ];
              if (shown.isEmpty) {
                return const Center(child: Text('No matches'));
              }
              return ListView.builder(
                controller: widget.controller,
                itemCount: shown.length,
                itemBuilder: (_, i) => ListTile(
                  minTileHeight: 48,
                  title: Text(
                    shown[i].name.isEmpty ? shown[i].id : shown[i].name,
                  ),
                  onTap: () => Navigator.pop(context, shown[i]),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
