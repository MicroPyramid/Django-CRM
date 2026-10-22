import 'package:flutter/material.dart';

import '../../../core/theme/theme.dart';
import '../../../services/automation_text.dart';

/// The rule's state as a small outlined pill, shared by the list and the editor.
class AutomationStatusPill extends StatelessWidget {
  const AutomationStatusPill({super.key, required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'on' => AppColors.success600,
      'paused' || 'over_limit' => AppColors.warning600,
      'needs_attention' => AppColors.danger600,
      _ => AppColors.textSecondary,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        statusLabel(status),
        style: AppTypography.caption.copyWith(
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
