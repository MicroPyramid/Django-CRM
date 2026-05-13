import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/ticket.dart';

/// Ticket Card — list item for the tickets list.
/// Flat card aesthetic per mobile/DESIGN_SYSTEM.md (no shadow, grey-200 border).
class TicketCard extends StatelessWidget {
  final Ticket ticketItem;
  final VoidCallback? onTap;

  const TicketCard({super.key, required this.ticketItem, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusMd,
          border: Border.all(color: AppColors.border),
        ),
        child: Material(
          color: Colors.transparent,
          borderRadius: AppLayout.borderRadiusMd,
          child: InkWell(
            onTap: onTap,
            borderRadius: AppLayout.borderRadiusMd,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeader(),
                  const SizedBox(height: 8),
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
        // Priority dot
        Container(
          margin: const EdgeInsets.only(top: 5, right: 8),
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: ticketItem.priority.color,
            shape: BoxShape.circle,
          ),
        ),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                ticketItem.name,
                style: AppTypography.label.copyWith(
                  fontWeight: FontWeight.w600,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              if (ticketItem.accountName != null &&
                  ticketItem.accountName!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Text(
                    ticketItem.accountName!,
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textSecondary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        // Status pill
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: ticketItem.status.color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            ticketItem.status.label,
            style: AppTypography.caption.copyWith(
              color: ticketItem.status.color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildFooter() {
    return Row(
      children: [
        Icon(
          ticketItem.ticketType.icon,
          size: 12,
          color: AppColors.textSecondary,
        ),
        const SizedBox(width: 3),
        Text(
          ticketItem.ticketType.label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(width: 10),
        Text(
          _formatTimeAgo(ticketItem.createdAt),
          style: AppTypography.caption.copyWith(color: AppColors.textTertiary),
        ),
        const Spacer(),
        if (ticketItem.isFirstResponseSlaBreached) _buildSlaChip(),
      ],
    );
  }

  Widget _buildSlaChip() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.danger100,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(LucideIcons.alertTriangle, size: 11, color: AppColors.danger600),
          const SizedBox(width: 3),
          Text(
            'SLA',
            style: AppTypography.caption.copyWith(
              color: AppColors.danger600,
              fontWeight: FontWeight.w600,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
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
