import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';

/// Timeline Item Widget
/// Displays activity events in a vertical timeline with connecting line
class TimelineItem extends StatelessWidget {
  final Activity activity;
  final bool isLast;
  final bool isFirst;

  const TimelineItem({
    super.key,
    required this.activity,
    this.isLast = false,
    this.isFirst = false,
  });

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Timeline indicator column
          SizedBox(
            width: 40,
            child: Column(
              children: [
                // Top connecting line
                if (!isFirst)
                  Container(
                    width: 2,
                    height: 8,
                    color: AppColors.gray200,
                  ),

                // Icon circle
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: _getIconColor(),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: _getIconColor().withValues(alpha: 0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Icon(
                    _getIcon(),
                    size: 16,
                    color: Colors.white,
                  ),
                ),

                // Bottom connecting line
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 2,
                      color: AppColors.gray200,
                    ),
                  ),
              ],
            ),
          ),

          const SizedBox(width: 12),

          // Content
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(
                top: isFirst ? 0 : 0,
                bottom: isLast ? 0 : 24,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title
                  Text(
                    activity.title,
                    style: AppTypography.label.copyWith(
                      color: AppColors.textPrimary,
                    ),
                  ),

                  // Description
                  if (activity.description != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      activity.description!,
                      style: AppTypography.body.copyWith(
                        color: AppColors.textSecondary,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],

                  // Timestamp
                  const SizedBox(height: 4),
                  Text(
                    _formatTimestamp(activity.timestamp),
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textTertiary,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getIconColor() {
    switch (activity.type) {
      case ActivityType.call:
        return AppColors.primary600;
      case ActivityType.email:
        return AppColors.primary500;
      case ActivityType.meeting:
        return AppColors.warning500;
      case ActivityType.note:
        return AppColors.gray400;
      case ActivityType.stageChange:
        return AppColors.success500;
      case ActivityType.taskCompleted:
        return AppColors.success600;
      case ActivityType.dealCreated:
        return AppColors.purple500;
      case ActivityType.dealWon:
        return AppColors.success600;
      case ActivityType.dealLost:
        return AppColors.danger500;
      case ActivityType.leadCreated:
        return AppColors.primary500;
    }
  }

  IconData _getIcon() {
    switch (activity.type) {
      case ActivityType.call:
        return LucideIcons.phone;
      case ActivityType.email:
        return LucideIcons.mail;
      case ActivityType.meeting:
        return LucideIcons.calendar;
      case ActivityType.note:
        return LucideIcons.fileText;
      case ActivityType.stageChange:
        return LucideIcons.arrowRight;
      case ActivityType.taskCompleted:
        return LucideIcons.checkCircle2;
      case ActivityType.dealCreated:
        return LucideIcons.plus;
      case ActivityType.dealWon:
        return LucideIcons.trophy;
      case ActivityType.dealLost:
        return LucideIcons.xCircle;
      case ActivityType.leadCreated:
        return LucideIcons.userPlus;
    }
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inDays > 7) {
      return '${timestamp.day}/${timestamp.month}/${timestamp.year}';
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

/// Timeline section header
class TimelineSectionHeader extends StatelessWidget {
  final String title;
  final int count;

  const TimelineSectionHeader({
    super.key,
    required this.title,
    required this.count,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          Text(
            title,
            style: AppTypography.overline.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: AppColors.gray100,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              count.toString(),
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Empty timeline state
class TimelineEmpty extends StatelessWidget {
  const TimelineEmpty({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: AppColors.gray100,
                shape: BoxShape.circle,
              ),
              child: Icon(
                LucideIcons.clock,
                size: 32,
                color: AppColors.gray400,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'No activity yet',
              style: AppTypography.h3.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Start by making a call or sending an email',
              style: AppTypography.body.copyWith(
                color: AppColors.textTertiary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
