import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../data/mock/mock_data.dart';
import '../../widgets/common/common.dart';
import '../../widgets/misc/stage_stepper.dart';
import '../../widgets/misc/timeline_item.dart';

/// Deal Detail Screen
/// Shows deal information with stage stepper and progression actions
class DealDetailScreen extends StatefulWidget {
  final String dealId;

  const DealDetailScreen({
    super.key,
    required this.dealId,
  });

  @override
  State<DealDetailScreen> createState() => _DealDetailScreenState();
}

class _DealDetailScreenState extends State<DealDetailScreen> {
  Deal? get deal => MockData.getDealById(widget.dealId);
  User? get assignedUser =>
      deal != null ? MockData.getUserById(deal!.assignedTo) : null;
  Lead? get relatedLead =>
      deal?.leadId != null ? MockData.getLeadById(deal!.leadId!) : null;

  List<Activity> get dealActivities => MockData.activities
      .where((a) =>
          a.relatedTo?.type == RelatedEntityType.deal && a.relatedTo?.id == widget.dealId)
      .toList()
    ..sort((a, b) => b.timestamp.compareTo(a.timestamp));

  static const List<DealStage> _stageOrder = [
    DealStage.prospecting,
    DealStage.qualified,
    DealStage.proposal,
    DealStage.negotiation,
    DealStage.closedWon,
  ];

  DealStage? get nextStage {
    final currentIndex = _stageOrder.indexOf(deal!.stage);
    if (currentIndex < _stageOrder.length - 1 && currentIndex >= 0) {
      return _stageOrder[currentIndex + 1];
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    if (deal == null) {
      return Scaffold(
        appBar: AppBar(
          leading: IconButton(
            icon: const Icon(LucideIcons.chevronLeft),
            onPressed: () => context.pop(),
          ),
        ),
        body: const EmptyState(
          icon: LucideIcons.briefcase,
          title: 'Deal not found',
          description: 'This deal may have been deleted',
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      body: CustomScrollView(
        slivers: [
          // App Bar + Header
          SliverAppBar(
            expandedHeight: 220,
            pinned: true,
            backgroundColor: AppColors.primary50,
            leading: IconButton(
              icon: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.9),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  LucideIcons.chevronLeft,
                  size: 20,
                  color: AppColors.textPrimary,
                ),
              ),
              onPressed: () => context.pop(),
            ),
            actions: [
              IconButton(
                icon: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.9),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    LucideIcons.pencil,
                    size: 18,
                    color: AppColors.textPrimary,
                  ),
                ),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Edit coming soon'),
                      behavior: SnackBarBehavior.floating,
                    ),
                  );
                },
              ),
              IconButton(
                icon: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.9),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    LucideIcons.moreVertical,
                    size: 18,
                    color: AppColors.textPrimary,
                  ),
                ),
                onPressed: () => _showMoreOptions(),
              ),
            ],
            flexibleSpace: FlexibleSpaceBar(
              background: _buildHeader(),
            ),
          ),

          // Content
          SliverToBoxAdapter(
            child: Column(
              children: [
                // Stage Stepper
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: StageStepper(
                    currentStage: deal!.stage,
                    onStageChange: _handleStageChange,
                  ),
                ),

                // Deal Info Card
                _buildInfoCard(),

                // Probability Indicator
                _buildProbabilityCard(),

                // Products Section
                if (deal!.products.isNotEmpty) _buildProductsCard(),

                // Related Lead Card
                if (relatedLead != null) _buildRelatedLeadCard(),

                // Activity Timeline
                _buildActivitySection(),

                // Bottom spacing for action buttons
                const SizedBox(height: 140),
              ],
            ),
          ),
        ],
      ),

      // Bottom Action Buttons
      bottomSheet: _buildActionButtons(),
    );
  }

  Widget _buildHeader() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.primary50,
            AppColors.primary100.withValues(alpha: 0.5),
          ],
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 60, 24, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              // Deal Title
              Text(
                deal!.title,
                style: AppTypography.h1.copyWith(
                  color: AppColors.textPrimary,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),

              const SizedBox(height: 4),

              // Company Name
              GestureDetector(
                onTap: relatedLead != null
                    ? () => context.push('/leads/${relatedLead!.id}')
                    : null,
                child: Row(
                  children: [
                    Text(
                      deal!.companyName,
                      style: AppTypography.body.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    if (relatedLead != null) ...[
                      const SizedBox(width: 4),
                      Icon(
                        LucideIcons.externalLink,
                        size: 14,
                        color: AppColors.textSecondary,
                      ),
                    ],
                  ],
                ),
              ),

              const SizedBox(height: 12),

              // Deal Value
              Text(
                _formatCurrency(deal!.value),
                style: AppTypography.display.copyWith(
                  color: AppColors.primary600,
                  fontSize: 32,
                ),
              ),

              const SizedBox(height: 8),

              // Badges
              Row(
                children: [
                  if (deal!.priority == Priority.high) ...[
                    PriorityBadge(priority: deal!.priority),
                    const SizedBox(width: 8),
                  ],
                  ...deal!.labels.take(2).map((label) => Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: LabelPill(label: label),
                      )),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoCard() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusLg,
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'DEAL INFORMATION',
              style: AppTypography.overline.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 16),

            // Info Grid
            Row(
              children: [
                Expanded(
                  child: _InfoItem(
                    icon: LucideIcons.dollarSign,
                    label: 'VALUE',
                    value: _formatCurrency(deal!.value),
                  ),
                ),
                Expanded(
                  child: _InfoItem(
                    icon: LucideIcons.percent,
                    label: 'PROBABILITY',
                    value: '${deal!.probability}%',
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _InfoItem(
                    icon: LucideIcons.calendar,
                    label: 'EXPECTED CLOSE',
                    value: deal!.closeDate != null
                        ? _formatDate(deal!.closeDate!)
                        : 'Not set',
                  ),
                ),
                Expanded(
                  child: _InfoItem(
                    icon: LucideIcons.clock,
                    label: 'CREATED',
                    value: _formatDate(deal!.createdAt),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Assigned User
            Row(
              children: [
                Icon(
                  LucideIcons.user,
                  size: 16,
                  color: AppColors.gray400,
                ),
                const SizedBox(width: 8),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'ASSIGNED TO',
                      style: AppTypography.overline.copyWith(
                        color: AppColors.textTertiary,
                        fontSize: 10,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        UserAvatar(
                          name: assignedUser?.name ?? 'Unknown',
                          imageUrl: assignedUser?.avatar,
                          size: AvatarSize.xs,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          assignedUser?.name ?? 'Unknown',
                          style: AppTypography.body,
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProbabilityCard() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusLg,
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'WIN PROBABILITY',
                  style: AppTypography.overline.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                Text(
                  '${deal!.probability}%',
                  style: AppTypography.h3.copyWith(
                    color: _getProbabilityColor(deal!.probability),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: deal!.probability / 100,
                minHeight: 8,
                backgroundColor: AppColors.gray200,
                valueColor: AlwaysStoppedAnimation(
                  _getProbabilityColor(deal!.probability),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _getProbabilityText(deal!.probability),
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProductsCard() {
    final totalProductValue = deal!.products
        .fold<double>(0, (sum, p) => sum + (p.unitPrice * p.quantity));

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusLg,
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Text(
                      'PRODUCTS',
                      style: AppTypography.overline.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    const SizedBox(width: 8),
                    CountBadge(count: deal!.products.length),
                  ],
                ),
                Text(
                  _formatCurrency(totalProductValue),
                  style: AppTypography.label.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...deal!.products.map((product) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    children: [
                      Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(
                          color: AppColors.primary100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(
                          LucideIcons.package,
                          size: 18,
                          color: AppColors.primary600,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              product.name,
                              style: AppTypography.label,
                            ),
                            Text(
                              'Qty: ${product.quantity}',
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Text(
                        _formatCurrency(product.unitPrice * product.quantity),
                        style: AppTypography.label.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildRelatedLeadCard() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: GestureDetector(
        onTap: () => context.push('/leads/${relatedLead!.id}'),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: AppLayout.borderRadiusLg,
            border: Border.all(color: AppColors.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'RELATED LEAD',
                style: AppTypography.overline.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  UserAvatar(
                    name: relatedLead!.name,
                    imageUrl: relatedLead!.avatar,
                    size: AvatarSize.md,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          relatedLead!.name,
                          style: AppTypography.label,
                        ),
                        Text(
                          relatedLead!.company,
                          style: AppTypography.caption.copyWith(
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    LucideIcons.chevronRight,
                    size: 20,
                    color: AppColors.textTertiary,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActivitySection() {
    final activities = dealActivities.take(5).toList();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusLg,
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'ACTIVITY',
                  style: AppTypography.overline.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                if (dealActivities.length > 5)
                  Text(
                    'See All',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.primary600,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 16),
            if (activities.isEmpty)
              Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                    'No activity yet',
                    style: AppTypography.body.copyWith(
                      color: AppColors.textTertiary,
                    ),
                  ),
                ),
              )
            else
              ...activities.asMap().entries.map((entry) {
                return TimelineItem(
                  activity: entry.value,
                  isFirst: entry.key == 0,
                  isLast: entry.key == activities.length - 1,
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    final isWon = deal!.stage == DealStage.closedWon;
    final isLost = deal!.stage == DealStage.closedLost;
    final isClosed = isWon || isLost;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(
          top: BorderSide(color: AppColors.border),
        ),
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (!isClosed && nextStage != null)
              PrimaryButton(
                label: 'Move to ${nextStage!.displayName}',
                icon: LucideIcons.arrowRight,
                iconRight: true,
                onPressed: () => _handleStageChange(nextStage!),
              ),

            if (isWon)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  color: AppColors.success100,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      LucideIcons.trophy,
                      color: AppColors.success600,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Deal Won!',
                      style: AppTypography.label.copyWith(
                        color: AppColors.success600,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),

            if (!isClosed) ...[
              const SizedBox(height: 12),
              GhostButton(
                label: 'Mark as Lost',
                icon: LucideIcons.xCircle,
                color: AppColors.danger600,
                onPressed: () => _handleMarkLost(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _handleStageChange(DealStage newStage) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Move to ${newStage.displayName}?'),
        content: Text(
          'This will update the deal stage and probability.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Deal moved to ${newStage.displayName}'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            child: const Text('Move'),
          ),
        ],
      ),
    );
  }

  void _handleMarkLost() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Mark as Lost?'),
        content: const Text(
          'Are you sure you want to mark this deal as lost?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Deal marked as lost'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            child: Text(
              'Mark Lost',
              style: TextStyle(color: AppColors.danger600),
            ),
          ),
        ],
      ),
    );
  }

  void _showMoreOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              margin: const EdgeInsets.only(top: 12),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.gray300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            ListTile(
              leading: const Icon(LucideIcons.copy),
              title: const Text('Duplicate Deal'),
              onTap: () {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Deal duplicated'),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
            ),
            ListTile(
              leading: Icon(LucideIcons.trash2, color: AppColors.danger600),
              title: Text(
                'Delete Deal',
                style: TextStyle(color: AppColors.danger600),
              ),
              onTap: () {
                Navigator.pop(context);
                _confirmDelete();
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  void _confirmDelete() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Deal?'),
        content: const Text(
          'This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              context.pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Deal deleted'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            child: Text(
              'Delete',
              style: TextStyle(color: AppColors.danger600),
            ),
          ),
        ],
      ),
    );
  }

  Color _getProbabilityColor(int probability) {
    if (probability >= 75) return AppColors.success600;
    if (probability >= 50) return AppColors.primary600;
    if (probability >= 25) return AppColors.warning600;
    return AppColors.gray500;
  }

  String _getProbabilityText(int probability) {
    if (probability >= 75) return 'High chance of winning this deal';
    if (probability >= 50) return 'Good progress, keep pushing';
    if (probability >= 25) return 'Still early stage, needs work';
    return 'Low probability, consider next steps';
  }

  String _formatCurrency(double value) {
    if (value >= 1000000) {
      return '\$${(value / 1000000).toStringAsFixed(1)}M';
    } else if (value >= 1000) {
      return '\$${(value / 1000).toStringAsFixed(0)}K';
    } else {
      return '\$${value.toStringAsFixed(0)}';
    }
  }

  String _formatDate(DateTime date) {
    final months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }
}

/// Info item widget
class _InfoItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoItem({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: AppColors.gray400,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: AppTypography.overline.copyWith(
                  color: AppColors.textTertiary,
                  fontSize: 10,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: AppTypography.body,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
