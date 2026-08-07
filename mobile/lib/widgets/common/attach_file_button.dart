import 'package:flutter/material.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';

/// "Attach a file", on every detail screen that lists attachments.
///
/// Disabled while an upload is in flight rather than hidden, so the row does
/// not jump and a second tap cannot start a second upload of the same file.
class AttachFileButton extends StatelessWidget {
  const AttachFileButton({
    super.key,
    required this.onPressed,
    this.isUploading = false,
    this.label = 'Attach a file',
  });

  final VoidCallback onPressed;
  final bool isUploading;
  final String label;

  @override
  Widget build(BuildContext context) {
    return TextButton.icon(
      onPressed: isUploading ? null : onPressed,
      icon: isUploading
          ? const SizedBox(
              height: 14,
              width: 14,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Icon(LucideIcons.paperclip, size: 16),
      label: Text(isUploading ? 'Uploading…' : label),
      style: TextButton.styleFrom(
        foregroundColor: AppColors.primary600,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        // A themed button's minimum size is infinite width inside a Row, which
        // has blanked a page here before. Shrink-wrap instead.
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }
}
