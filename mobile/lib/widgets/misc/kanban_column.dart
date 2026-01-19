import 'package:flutter/material.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../cards/deal_card.dart';

/// Kanban Column Widget
/// Displays a pipeline stage column with draggable deal cards
class KanbanColumn extends StatelessWidget {
  final DealStage stage;
  final List<Deal> deals;
  final Function(Deal) onDealTap;
  final Function(Deal, DealStage)? onDealMoved;
  final double width;
  final String currencySymbol;

  const KanbanColumn({
    super.key,
    required this.stage,
    required this.deals,
    required this.onDealTap,
    this.onDealMoved,
    this.width = 300,
    this.currencySymbol = '\$',
  });

  double get totalValue {
    return deals.fold<double>(0, (sum, deal) => sum + deal.value);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      margin: const EdgeInsets.symmetric(horizontal: 6),
      decoration: BoxDecoration(
        color: AppColors.gray50,
        borderRadius: AppLayout.borderRadiusLg,
      ),
      child: Column(
        children: [
          // Column Header
          _buildHeader(),

          // Deals List (Droppable)
          Expanded(
            child: DragTarget<Deal>(
              onWillAcceptWithDetails: (details) {
                return details.data.stage != stage;
              },
              onAcceptWithDetails: (details) {
                onDealMoved?.call(details.data, stage);
              },
              builder: (context, candidateData, rejectedData) {
                final isHighlighted = candidateData.isNotEmpty;

                return AnimatedContainer(
                  duration: AppDurations.fast,
                  decoration: BoxDecoration(
                    color: isHighlighted
                        ? _getStageColor().withValues(alpha: 0.1)
                        : Colors.transparent,
                    borderRadius: const BorderRadius.vertical(
                      bottom: Radius.circular(16),
                    ),
                    border: isHighlighted
                        ? Border.all(
                            color: _getStageColor().withValues(alpha: 0.5),
                            width: 2,
                          )
                        : null,
                  ),
                  child: deals.isEmpty
                      ? _buildEmptyState()
                      : ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: deals.length,
                          itemBuilder: (context, index) {
                            final deal = deals[index];
                            return LongPressDraggable<Deal>(
                              data: deal,
                              feedback: Material(
                                elevation: 8,
                                borderRadius: AppLayout.borderRadiusLg,
                                child: SizedBox(
                                  width: width - 24,
                                  child: DealCard(
                                    deal: deal,
                                    isDragging: true,
                                    currencySymbol: currencySymbol,
                                  ),
                                ),
                              ),
                              childWhenDragging: Opacity(
                                opacity: 0.3,
                                child: DealCard(
                                  deal: deal,
                                  currencySymbol: currencySymbol,
                                ),
                              ),
                              child: DealCard(
                                deal: deal,
                                onTap: () => onDealTap(deal),
                                currencySymbol: currencySymbol,
                              ),
                            );
                          },
                        ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: AppColors.border,
            width: 1,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // Color dot
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  color: _getStageColor(),
                  shape: BoxShape.circle,
                ),
              ),

              const SizedBox(width: 8),

              // Stage name
              Expanded(
                child: Text(
                  stage.displayName,
                  style: AppTypography.label.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),

              // Count badge
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 8,
                  vertical: 3,
                ),
                decoration: BoxDecoration(
                  color: AppColors.gray200,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${deals.length}',
                  style: AppTypography.caption.copyWith(
                    fontWeight: FontWeight.w600,
                    color: AppColors.textSecondary,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 4),

          // Total value
          Text(
            _formatCurrency(totalValue),
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.inbox_outlined,
              size: 32,
              color: AppColors.gray300,
            ),
            const SizedBox(height: 8),
            Text(
              'No deals',
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getStageColor() {
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

  String _formatCurrency(double value) {
    if (value >= 1000000) {
      return '$currencySymbol${(value / 1000000).toStringAsFixed(1)}M';
    } else if (value >= 1000) {
      return '$currencySymbol${(value / 1000).toStringAsFixed(0)}K';
    } else {
      return '$currencySymbol${value.toStringAsFixed(0)}';
    }
  }
}
