import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';

/// Stage configuration
class _StageConfig {
  final DealStage stage;
  final String label;
  final IconData icon;

  const _StageConfig(this.stage, this.label, this.icon);
}

/// Stage Stepper Widget
/// Visual pipeline progression indicator for deals
class StageStepper extends StatelessWidget {
  final DealStage currentStage;
  final Function(DealStage)? onStageChange;
  final bool showLabels;

  const StageStepper({
    super.key,
    required this.currentStage,
    this.onStageChange,
    this.showLabels = true,
  });

  static const List<_StageConfig> _stages = [
    _StageConfig(DealStage.prospecting, 'Prospect', LucideIcons.search),
    _StageConfig(DealStage.qualified, 'Qualified', LucideIcons.checkCircle),
    _StageConfig(DealStage.proposal, 'Proposal', LucideIcons.fileText),
    _StageConfig(DealStage.negotiation, 'Negotiate', LucideIcons.messageSquare),
    _StageConfig(DealStage.closedWon, 'Won', LucideIcons.trophy),
  ];

  int get _currentIndex {
    return _stages.indexWhere((s) => s.stage == currentStage);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppLayout.borderRadiusLg,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          // Stepper row
          Row(
            children: List.generate(_stages.length * 2 - 1, (index) {
              if (index.isOdd) {
                // Connector line
                final stageIndex = index ~/ 2;
                final isCompleted = stageIndex < _currentIndex;

                return Expanded(
                  child: Container(
                    height: 2,
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    decoration: BoxDecoration(
                      color: isCompleted
                          ? AppColors.primary500
                          : AppColors.gray200,
                      borderRadius: BorderRadius.circular(1),
                    ),
                  ),
                );
              } else {
                // Stage circle
                final stageIndex = index ~/ 2;
                return _buildStageIndicator(stageIndex);
              }
            }),
          ),

          // Labels row
          if (showLabels) ...[
            const SizedBox(height: 8),
            Row(
              children: _stages.asMap().entries.map((entry) {
                final index = entry.key;
                final stage = entry.value;
                final isCompleted = index < _currentIndex;
                final isCurrent = index == _currentIndex;

                return Expanded(
                  child: Text(
                    stage.label,
                    textAlign: TextAlign.center,
                    style: AppTypography.caption.copyWith(
                      fontSize: 10,
                      color: isCurrent
                          ? AppColors.primary600
                          : isCompleted
                              ? AppColors.textSecondary
                              : AppColors.textTertiary,
                      fontWeight:
                          isCurrent ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStageIndicator(int index) {
    final stage = _stages[index];
    final isCompleted = index < _currentIndex;
    final isCurrent = index == _currentIndex;
    final isFuture = index > _currentIndex;

    return GestureDetector(
      onTap: isFuture && onStageChange != null
          ? () => onStageChange!(stage.stage)
          : null,
      child: AnimatedContainer(
        duration: AppDurations.normal,
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: isCompleted || isCurrent
              ? AppColors.primary600
              : Colors.transparent,
          shape: BoxShape.circle,
          border: Border.all(
            color: isFuture ? AppColors.gray300 : AppColors.primary600,
            width: 2,
          ),
          boxShadow: isCurrent
              ? [
                  BoxShadow(
                    color: AppColors.primary500.withValues(alpha: 0.3),
                    blurRadius: 8,
                    spreadRadius: 2,
                  ),
                ]
              : null,
        ),
        child: Icon(
          isCompleted ? LucideIcons.check : stage.icon,
          size: 16,
          color: isCompleted || isCurrent ? Colors.white : AppColors.gray400,
        ),
      ),
    );
  }
}

/// Mini stage indicator for compact views
class StageMiniIndicator extends StatelessWidget {
  final DealStage stage;

  const StageMiniIndicator({
    super.key,
    required this.stage,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: _getStageColor().withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: _getStageColor().withValues(alpha: 0.3),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              color: _getStageColor(),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            stage.displayName,
            style: AppTypography.caption.copyWith(
              color: _getStageColor(),
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Color _getStageColor() {
    switch (stage) {
      case DealStage.prospecting:
        return AppColors.gray500;
      case DealStage.qualified:
        return AppColors.primary600;
      case DealStage.proposal:
        return AppColors.purple600;
      case DealStage.negotiation:
        return AppColors.warning600;
      case DealStage.closedWon:
        return AppColors.success600;
      case DealStage.closedLost:
        return AppColors.danger600;
    }
  }
}
