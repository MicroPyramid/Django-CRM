import 'package:flutter/material.dart';

import '../../core/theme/theme.dart';
import '../../data/models/ticket.dart';

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
/// **[openNames] is the tickets that would actually close**, not the ticket's
/// child count. Those are different numbers: `child_count` counts direct
/// children whether open or closed, while the close walks the whole subtree and
/// touches only the open, active ones. This prompt used to quote the first and
/// so could offer to close three tickets that closed last week, or fail to
/// mention an open grandchild that was about to close.
///
/// Its own function rather than a closure inside the ticket screen so that the
/// seeding and the counting can be tested: a checkbox that silently reverts to
/// always-ticked is exactly the regression this exists to catch.
///
/// Returns null if dismissed, otherwise the choice that was confirmed.
Future<({bool cascade, String comment})?> showCloseWithChildrenDialog(
  BuildContext context, {
  required String ticketName,
  required List<String> openNames,
  required bool startsTicked,
  bool truncated = false,
}) async {
  final hasOpen = openNames.isNotEmpty;
  // Nothing open below means nothing for a cascade to do, so the box starts
  // clear whatever the org set and the request closes this ticket alone.
  var cascade = hasOpen && startsTicked;
  final comment = TextEditingController();

  final confirmed = await showDialog<bool>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (ctx, setLocal) => AlertDialog(
        title: const Text('Close ticket'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Close "$ticketName"?'),
              const SizedBox(height: 10),
              Text(
                cascadeSummary(count: openNames.length, truncated: truncated),
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              if (hasOpen) ...[
                const SizedBox(height: 12),
                // Named, because they can belong to somebody else and nobody
                // is asked twice.
                ConstrainedBox(
                  constraints: const BoxConstraints(maxHeight: 140),
                  child: SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        for (final name in openNames)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Text(
                              name,
                              style: AppTypography.caption,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Checkbox(
                      value: cascade,
                      onChanged: (v) => setLocal(() => cascade = v ?? cascade),
                    ),
                    const Expanded(child: Text('Close these as well')),
                  ],
                ),
                TextField(
                  controller: comment,
                  maxLines: 2,
                  maxLength: 1000,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: const InputDecoration(
                    labelText: 'Why (optional)',
                    helperText:
                        'Recorded against every ticket closed with this one',
                    helperMaxLines: 2,
                    border: OutlineInputBorder(),
                    counterText: '',
                  ),
                ),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(cascade ? 'Close all of them' : 'Close ticket'),
          ),
        ],
      ),
    ),
  );

  final text = comment.text;
  comment.dispose();
  if (confirmed != true) return null;
  return (cascade: cascade, comment: text);
}
