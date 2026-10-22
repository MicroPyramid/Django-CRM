import 'package:flutter/material.dart';

import '../../../core/theme/theme.dart';
import '../../../data/models/automation.dart';

/// What a rule would do to one record. Nothing was changed; step texts and the
/// record name come from the server and render as plain text.
Future<void> showTryResults(
  BuildContext context, {
  required String recordName,
  required List<RunStep> steps,
  String? error,
}) => showModalBottomSheet<void>(
  context: context,
  backgroundColor: AppColors.surface,
  isScrollControlled: true,
  shape: const RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
  ),
  builder: (_) => DraggableScrollableSheet(
    initialChildSize: 0.6,
    minChildSize: 0.4,
    maxChildSize: 0.95,
    expand: false,
    builder: (sheet, controller) => ListView(
      controller: controller,
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
      children: [
        Text('Try it on a record', style: AppTypography.h3),
        const SizedBox(height: 12),
        if (error != null)
          Text(
            error,
            style: AppTypography.body.copyWith(color: AppColors.danger600),
          )
        else ...[
          Text(
            'Tried on "$recordName". Nothing was changed.',
            style: AppTypography.body,
          ),
          const SizedBox(height: 4),
          Text(
            'The trigger and conditions are not checked: this is what the '
            'actions would do.',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 12),
          for (final s in steps) _Step(step: s),
        ],
        const SizedBox(height: 8),
        SizedBox(
          height: 48,
          child: OutlinedButton(
            onPressed: () => Navigator.pop(sheet),
            child: const Text('Close'),
          ),
        ),
      ],
    ),
  ),
);

class _Step extends StatelessWidget {
  const _Step({required this.step});

  final RunStep step;

  @override
  Widget build(BuildContext context) {
    final failed = step.status == 'failed';
    final skipped = step.status == 'skipped';
    final color = failed
        ? AppColors.danger600
        : skipped
        ? AppColors.textSecondary
        : AppColors.textPrimary;
    final mark = failed
        ? 'Would fail'
        : skipped
        ? 'Skipped'
        : null;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(step.text, style: AppTypography.body.copyWith(color: color)),
          if (mark != null)
            Text(
              mark,
              style: AppTypography.caption.copyWith(
                color: color,
                fontWeight: FontWeight.w600,
              ),
            ),
        ],
      ),
    );
  }
}
