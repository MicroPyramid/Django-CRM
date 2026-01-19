import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../data/mock/mock_data.dart';
import '../common/common.dart';

/// Deal Card Widget
/// Displays deal summary in Kanban columns or list view
class DealCard extends StatelessWidget {
  final Deal deal;
  final VoidCallback? onTap;
  final bool isDragging;
  final String currencySymbol;

  const DealCard({
    super.key,
    required this.deal,
    this.onTap,
    this.isDragging = false,
    this.currencySymbol = '\$',
  });

  int get daysUntilClose {
    if (deal.closeDate == null) return 999;
    return deal.closeDate!.difference(DateTime.now()).inDays;
  }

  Color get closeDateColor {
    if (daysUntilClose < 0) return AppColors.danger600;
    if (daysUntilClose <= 7) return AppColors.warning600;
    return AppColors.textSecondary;
  }

  String get closeDateText {
    if (daysUntilClose < 0) {
      return '${-daysUntilClose}d overdue';
    } else if (daysUntilClose == 0) {
      return 'Today';
    } else {
      return '${daysUntilClose}d left';
    }
  }

  @override
  Widget build(BuildContext context) {
    final assignedUser = MockData.getUserById(deal.assignedTo);

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: AppDurations.fast,
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusLg,
          boxShadow: isDragging ? AppLayout.shadowMd : AppLayout.shadowSm,
        ),
        child: Material(
          color: Colors.transparent,
          borderRadius: AppLayout.borderRadiusLg,
          child: InkWell(
            onTap: onTap,
            borderRadius: AppLayout.borderRadiusLg,
            child: Opacity(
              opacity: isDragging ? 0.8 : 1.0,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Row 1: Title + Priority
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Text(
                            deal.title,
                            style: AppTypography.label.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (deal.priority == Priority.high) ...[
                          const SizedBox(width: 8),
                          PriorityBadge(priority: deal.priority),
                        ],
                      ],
                    ),

                    // Row 2: Company
                    const SizedBox(height: 4),
                    Text(
                      deal.companyName,
                      style: AppTypography.body.copyWith(
                        color: AppColors.textSecondary,
                        fontSize: 13,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),

                    // Row 3: Labels
                    if (deal.labels.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: deal.labels
                            .take(3)
                            .map((label) => LabelPill(label: label))
                            .toList(),
                      ),
                    ],

                    // Row 4: Value + Close Date
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          _formatCurrency(deal.value),
                          style: AppTypography.h3.copyWith(
                            color: AppColors.textPrimary,
                          ),
                        ),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (daysUntilClose <= 7 && daysUntilClose >= 0)
                              Padding(
                                padding: const EdgeInsets.only(right: 4),
                                child: Icon(
                                  LucideIcons.alertCircle,
                                  size: 14,
                                  color: closeDateColor,
                                ),
                              ),
                            Text(
                              closeDateText,
                              style: AppTypography.caption.copyWith(
                                color: closeDateColor,
                                fontWeight: daysUntilClose <= 7
                                    ? FontWeight.w600
                                    : FontWeight.normal,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),

                    // Row 5: Probability bar + Assignee
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(2),
                                child: LinearProgressIndicator(
                                  value: deal.probability / 100,
                                  minHeight: 4,
                                  backgroundColor: AppColors.gray200,
                                  valueColor: AlwaysStoppedAnimation(
                                    _getProbabilityColor(deal.probability),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${deal.probability}% probability',
                                style: AppTypography.caption.copyWith(
                                  color: AppColors.textTertiary,
                                  fontSize: 10,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        if (assignedUser != null)
                          UserAvatar(
                            name: assignedUser.name,
                            imageUrl: assignedUser.avatar,
                            size: AvatarSize.xs,
                          ),
                      ],
                    ),

                    // Row 6: Products count
                    if (deal.products.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.gray100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              LucideIcons.package,
                              size: 12,
                              color: AppColors.textSecondary,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '${deal.products.length} product${deal.products.length > 1 ? 's' : ''}',
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textSecondary,
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _formatCurrency(double value) {
    if (value >= 1000000) {
      return '$currencySymbol${(value / 1000000).toStringAsFixed(1)}M';
    } else if (value >= 1000) {
      return '$currencySymbol${(value / 1000).toStringAsFixed(0)}K';
    } else {
      return '$currencySymbol${value.toStringAsFixed(0)}';
    }
  }

  Color _getProbabilityColor(int probability) {
    if (probability >= 75) return AppColors.success500;
    if (probability >= 50) return AppColors.primary500;
    if (probability >= 25) return AppColors.warning500;
    return AppColors.gray400;
  }
}

/// Compact deal card for horizontal lists
class DealCardCompact extends StatelessWidget {
  final Deal deal;
  final VoidCallback? onTap;
  final String currencySymbol;

  const DealCardCompact({
    super.key,
    required this.deal,
    this.onTap,
    this.currencySymbol = '\$',
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 220,
        padding: const EdgeInsets.all(14),
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
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: _getStageColor(deal.stage),
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    deal.title,
                    style: AppTypography.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              deal.companyName,
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '$currencySymbol${(deal.value / 1000).toStringAsFixed(0)}K',
                  style: AppTypography.label.copyWith(
                    color: AppColors.primary600,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  '${deal.probability}%',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Color _getStageColor(DealStage stage) {
    switch (stage) {
      case DealStage.prospecting:
        return AppColors.gray400;
      case DealStage.qualified:
        return AppColors.primary500;
      case DealStage.proposal:
        return AppColors.purple500;
      case DealStage.negotiation:
        return AppColors.warning500;
      case DealStage.closedWon:
        return AppColors.success500;
      case DealStage.closedLost:
        return AppColors.danger500;
    }
  }
}
