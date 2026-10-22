import 'package:flutter/material.dart';

import '../../../core/theme/theme.dart';

/// Opens one of the editor's bottom sheets in the record picker's style.
Future<T?> showRuleSheet<T>(
  BuildContext context,
  Widget Function(ScrollController controller) builder,
) => showModalBottomSheet<T>(
  context: context,
  backgroundColor: AppColors.surface,
  isScrollControlled: true,
  shape: const RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
  ),
  builder: (context) => Padding(
    padding: EdgeInsets.only(bottom: MediaQuery.viewInsetsOf(context).bottom),
    child: DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      expand: false,
      builder: (_, controller) => builder(controller),
    ),
  ),
);

/// The handle, title, scrolling body and Cancel and Done of an editor sheet.
class RuleSheetFrame extends StatelessWidget {
  const RuleSheetFrame({
    super.key,
    required this.title,
    required this.controller,
    required this.children,
    required this.onDone,
  });

  final String title;
  final ScrollController controller;
  final List<Widget> children;

  /// Null disables Done.
  final VoidCallback? onDone;

  @override
  Widget build(BuildContext context) => Column(
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
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
        child: Align(
          alignment: Alignment.centerLeft,
          child: Text(title, style: AppTypography.h3),
        ),
      ),
      Expanded(
        child: ListView(
          controller: controller,
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          children: children,
        ),
      ),
      Container(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: AppColors.border)),
        ),
        child: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
            child: Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Cancel'),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: FilledButton(
                      onPressed: onDone,
                      child: const Text('Done'),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    ],
  );
}
