import 'package:flutter/material.dart';

import '../../core/theme/theme.dart';

/// Confirm closing a parent ticket, with an explicit choice about its children.
///
/// **[startsTicked] comes from `Org.auto_close_children_on_parent_close`, and
/// that setting has no other effect on a person.**
/// `CaseCloseWithChildrenView` reads the org column only when the caller omits
/// `cascade` entirely, and this app always sends it, so the setting reaches
/// someone through this checkbox or nowhere. It was hardcoded to `true` here,
/// which made the setting inert and the settings screen's "starts unticked"
/// simply false.
///
/// Its own function rather than a closure inside the ticket screen so that the
/// seeding can be tested: a checkbox that silently reverts to always-ticked is
/// exactly the regression this exists to catch.
///
/// Returns null if dismissed, otherwise the choice that was confirmed.
Future<({bool cascade})?> showCloseWithChildrenDialog(
  BuildContext context, {
  required String ticketName,
  required int childCount,
  required bool startsTicked,
}) async {
  var cascade = startsTicked;
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (ctx, setLocal) => AlertDialog(
        title: const Text('Close ticket'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Close "$ticketName"? This ticket has $childCount '
              'linked ticket${childCount == 1 ? '' : 's'}.',
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Checkbox(
                  value: cascade,
                  onChanged: (v) => setLocal(() => cascade = v ?? startsTicked),
                ),
                const Expanded(child: Text('Also close linked tickets')),
              ],
            ),
            Text(
              'Only the linked tickets that are still open are closed, '
              'including any beneath them.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Close ticket'),
          ),
        ],
      ),
    ),
  );
  if (confirmed != true) return null;
  return (cascade: cascade);
}
