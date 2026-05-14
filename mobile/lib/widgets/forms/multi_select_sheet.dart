import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/theme/theme.dart';

/// Generic searchable multi-select bottom sheet.
///
/// Open with `MultiSelectSheet.show<T>(...)` — returns the new selection or
/// null if cancelled. Items are matched against `searchText(item)`.
class MultiSelectSheet<T> extends StatefulWidget {
  final String title;
  final List<T> items;
  final List<T> initialSelection;
  final String Function(T) labelOf;
  final String Function(T) searchText;
  final Widget Function(T)? leadingOf;
  final String emptyMessage;

  const MultiSelectSheet({
    super.key,
    required this.title,
    required this.items,
    required this.initialSelection,
    required this.labelOf,
    required this.searchText,
    this.leadingOf,
    this.emptyMessage = 'No options',
  });

  static Future<List<T>?> show<T>({
    required BuildContext context,
    required String title,
    required List<T> items,
    required List<T> initialSelection,
    required String Function(T) labelOf,
    required String Function(T) searchText,
    Widget Function(T)? leadingOf,
    String emptyMessage = 'No options',
  }) {
    return showModalBottomSheet<List<T>>(
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
        builder: (ctx, controller) => MultiSelectSheet<T>(
          title: title,
          items: items,
          initialSelection: initialSelection,
          labelOf: labelOf,
          searchText: searchText,
          leadingOf: leadingOf,
          emptyMessage: emptyMessage,
        ),
      ),
    );
  }

  @override
  State<MultiSelectSheet<T>> createState() => _MultiSelectSheetState<T>();
}

class _MultiSelectSheetState<T> extends State<MultiSelectSheet<T>> {
  late final TextEditingController _searchController;
  late final Set<T> _selected;
  String _query = '';

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
    _selected = Set<T>.from(widget.initialSelection);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<T> get _filtered {
    if (_query.isEmpty) return widget.items;
    final q = _query.toLowerCase();
    return widget.items
        .where((item) => widget.searchText(item).toLowerCase().contains(q))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _filtered;
    return Column(
      children: [
        Container(
          margin: const EdgeInsets.only(top: 12),
          width: 40,
          height: 4,
          decoration: BoxDecoration(
            color: AppColors.gray300,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
          child: Row(
            children: [
              Expanded(
                child: Text(widget.title, style: AppTypography.h3),
              ),
              TextButton(
                onPressed: () =>
                    Navigator.pop(context, _selected.toList()),
                child: const Text('Done'),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: 'Search…',
              prefixIcon: const Icon(LucideIcons.search, size: 18),
              filled: true,
              fillColor: AppColors.gray50,
              contentPadding: const EdgeInsets.symmetric(vertical: 8),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: BorderSide(color: AppColors.border),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: BorderSide(color: AppColors.border),
              ),
            ),
            onChanged: (v) => setState(() => _query = v),
          ),
        ),
        Expanded(
          child: filtered.isEmpty
              ? Center(
                  child: Text(
                    widget.emptyMessage,
                    style: AppTypography.body.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                )
              : ListView.builder(
                  itemCount: filtered.length,
                  itemBuilder: (_, i) {
                    final item = filtered[i];
                    final isChecked = _selected.contains(item);
                    return InkWell(
                      onTap: () {
                        setState(() {
                          if (isChecked) {
                            _selected.remove(item);
                          } else {
                            _selected.add(item);
                          }
                        });
                      },
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 12,
                        ),
                        child: Row(
                          children: [
                            if (widget.leadingOf != null) ...[
                              widget.leadingOf!(item),
                              const SizedBox(width: 12),
                            ],
                            Expanded(
                              child: Text(
                                widget.labelOf(item),
                                style: AppTypography.body,
                              ),
                            ),
                            Checkbox(
                              value: isChecked,
                              onChanged: (v) {
                                setState(() {
                                  if (v == true) {
                                    _selected.add(item);
                                  } else {
                                    _selected.remove(item);
                                  }
                                });
                              },
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }
}
