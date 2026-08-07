import 'package:flutter/material.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/attachment.dart';

/// One uploaded file, with an icon that matches its type.
///
/// Lead detail and deal detail each carried a private copy of this, identical
/// to the character apart from one blank line. The ticket Files tab would have
/// been a third.
class AttachmentTile extends StatelessWidget {
  final Attachment attachment;
  final void Function(Attachment) onOpen;
  const AttachmentTile({
    super.key,
    required this.attachment,
    required this.onOpen,
  });

  IconData get _iconForName {
    final lower = attachment.fileName.toLowerCase();
    if (lower.endsWith('.pdf')) return LucideIcons.fileText;
    if (RegExp(r'\.(png|jpg|jpeg|gif|webp|bmp)$').hasMatch(lower)) {
      return LucideIcons.image;
    }
    if (RegExp(r'\.(xls|xlsx|csv)$').hasMatch(lower)) {
      return LucideIcons.fileSpreadsheet;
    }
    if (RegExp(r'\.(zip|tar|gz|rar|7z)$').hasMatch(lower)) {
      return LucideIcons.fileArchive;
    }
    return LucideIcons.file;
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      borderRadius: AppLayout.borderRadiusMd,
      child: InkWell(
        borderRadius: AppLayout.borderRadiusMd,
        onTap: () => onOpen(attachment),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            borderRadius: AppLayout.borderRadiusMd,
            border: Border.all(color: AppColors.border),
          ),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppColors.primary50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  _iconForName,
                  color: AppColors.primary600,
                  size: 18,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      attachment.fileName,
                      style: AppTypography.label,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      [
                        if (attachment.createdBy != null &&
                            attachment.createdBy!.isNotEmpty)
                          attachment.createdBy!,
                        if (attachment.createdAt != null)
                          _formatRelative(attachment.createdAt!),
                      ].join(' · '),
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textTertiary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Icon(
                LucideIcons.externalLink,
                size: 16,
                color: AppColors.textTertiary,
              ),
            ],
          ),
        ),
      ),
    );
  }

  static String _formatRelative(DateTime dt) {
    final d = DateTime.now().difference(dt);
    if (d.inDays > 30) return '${(d.inDays / 30).floor()}mo ago';
    if (d.inDays > 0) return '${d.inDays}d ago';
    if (d.inHours > 0) return '${d.inHours}h ago';
    if (d.inMinutes > 0) return '${d.inMinutes}m ago';
    return 'just now';
  }
}
