import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../common/common.dart';

/// Lead Card Widget
/// Displays lead summary in list view with avatar, status, priority, and tags
class LeadCard extends StatelessWidget {
  final Lead lead;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;

  const LeadCard({
    super.key,
    required this.lead,
    this.onTap,
    this.onLongPress,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      onLongPress: onLongPress,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusLg,
          boxShadow: AppLayout.shadowSm,
        ),
        child: Material(
          color: Colors.transparent,
          borderRadius: AppLayout.borderRadiusLg,
          child: InkWell(
            onTap: onTap,
            onLongPress: onLongPress,
            borderRadius: AppLayout.borderRadiusLg,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Row 1: Avatar + Info + Priority/Time
                  _buildHeader(),

                  // Row 2: Tags
                  if (lead.tags.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    _buildTags(),
                  ],

                  // Row 3: Status + Assignment
                  const SizedBox(height: 12),
                  _buildFooter(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Avatar
        UserAvatar(
          name: lead.name,
          size: AvatarSize.md,
        ),

        const SizedBox(width: 12),

        // Name + Company
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                lead.name,
                style: AppTypography.h3,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 2),
              Text(
                lead.company,
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),

        const SizedBox(width: 8),

        // Right side: Priority badge + time
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (lead.priority == Priority.high)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.danger100,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      LucideIcons.flame,
                      size: 12,
                      color: AppColors.danger600,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'Hot',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.danger600,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 4),
            Text(
              _formatTimeAgo(lead.createdAt),
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildTags() {
    final displayTags = lead.tags.take(2).toList();
    final remainingCount = lead.tags.length - 2;

    return Row(
      children: [
        ...displayTags.map((tag) => Padding(
              padding: const EdgeInsets.only(right: 6),
              child: LabelPill(label: tag),
            )),
        if (remainingCount > 0)
          Text(
            '+$remainingCount more',
            style: AppTypography.caption.copyWith(
              color: AppColors.textTertiary,
            ),
          ),
      ],
    );
  }

  Widget _buildFooter() {
    return Row(
      children: [
        // Status Badge
        StatusBadge.fromLeadStatus(lead.status),

        const Spacer(),

        // Source indicator
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: AppColors.gray100,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _getSourceIcon(lead.source),
                size: 12,
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 4),
              Text(
                lead.source.displayName,
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  IconData _getSourceIcon(LeadSource source) {
    // Use the icon defined in the enum
    return source.icon;
  }

  String _formatTimeAgo(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays > 30) {
      return '${(difference.inDays / 30).floor()}mo ago';
    } else if (difference.inDays > 0) {
      return '${difference.inDays}d ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}m ago';
    } else {
      return 'Just now';
    }
  }
}

/// Compact lead card variant for horizontal scrolling lists
class LeadCardCompact extends StatelessWidget {
  final Lead lead;
  final VoidCallback? onTap;

  const LeadCardCompact({
    super.key,
    required this.lead,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 200,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusMd,
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                UserAvatar(
                  name: lead.name,
                  size: AvatarSize.sm,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        lead.name,
                        style: AppTypography.label,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      Text(
                        lead.company,
                        style: AppTypography.caption.copyWith(
                          color: AppColors.textSecondary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            StatusBadge.fromLeadStatus(lead.status),
          ],
        ),
      ),
    );
  }
}
