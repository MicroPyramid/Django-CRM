import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/auth_provider.dart';
import '../../providers/deals_provider.dart';
import '../../widgets/common/common.dart';
import '../../widgets/misc/stage_stepper.dart';

/// Deal Detail Screen
/// Shows deal information with stage stepper and progression actions
class DealDetailScreen extends ConsumerStatefulWidget {
  final String dealId;

  const DealDetailScreen({
    super.key,
    required this.dealId,
  });

  @override
  ConsumerState<DealDetailScreen> createState() => _DealDetailScreenState();
}

class _DealDetailScreenState extends ConsumerState<DealDetailScreen> {
  Deal? _deal;
  bool _isLoading = true;
  String? _error;
  bool _isUpdatingStage = false;

  @override
  void initState() {
    super.initState();
    _fetchDeal();
  }

  Future<void> _fetchDeal() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final deal = await ref.read(dealsProvider.notifier).getDeal(widget.dealId);

    if (mounted) {
      setState(() {
        _isLoading = false;
        _deal = deal;
        if (deal == null) {
          _error = 'Failed to load deal';
        }
      });
    }
  }

  static const List<DealStage> _stageOrder = [
    DealStage.prospecting,
    DealStage.qualified,
    DealStage.proposal,
    DealStage.negotiation,
    DealStage.closedWon,
  ];

  DealStage? get nextStage {
    if (_deal == null) return null;
    final currentIndex = _stageOrder.indexOf(_deal!.stage);
    if (currentIndex < _stageOrder.length - 1 && currentIndex >= 0) {
      return _stageOrder[currentIndex + 1];
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        backgroundColor: AppColors.surfaceDim,
        appBar: AppBar(
          leading: IconButton(
            icon: const Icon(LucideIcons.chevronLeft),
            onPressed: () => context.pop(),
          ),
        ),
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_error != null || _deal == null) {
      return Scaffold(
        appBar: AppBar(
          leading: IconButton(
            icon: const Icon(LucideIcons.chevronLeft),
            onPressed: () => context.pop(),
          ),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const EmptyState(
                icon: LucideIcons.briefcase,
                title: 'Deal not found',
                description: 'This deal may have been deleted',
              ),
              const SizedBox(height: 16),
              TextButton(
                onPressed: _fetchDeal,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      body: CustomScrollView(
        slivers: [
          // App Bar + Header
          SliverAppBar(
            expandedHeight: 260,
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
                onPressed: () => _navigateToEdit(),
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
                    currentStage: _deal!.stage,
                    onStageChange: _handleStageChange,
                  ),
                ),

                // Deal Info Card
                _buildInfoCard(),

                // Probability Indicator
                _buildProbabilityCard(),

                // Products Section
                if (_deal!.products.isNotEmpty) _buildProductsCard(),

                // Notes Section
                if (_deal!.notes != null && _deal!.notes!.isNotEmpty)
                  _buildNotesCard(),

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
          padding: const EdgeInsets.fromLTRB(24, 56, 24, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.end,
            mainAxisSize: MainAxisSize.min,
            children: [
              // Deal Title
              Text(
                _deal!.title,
                style: AppTypography.h2.copyWith(
                  color: AppColors.textPrimary,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),

              const SizedBox(height: 2),

              // Company Name
              Text(
                _deal!.companyName,
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),

              const SizedBox(height: 8),

              // Deal Value
              Text(
                _formatCurrency(_deal!.value),
                style: AppTypography.display.copyWith(
                  color: AppColors.primary600,
                  fontSize: 28,
                ),
              ),

              const SizedBox(height: 6),

              // Badges
              Row(
                children: [
                  // Stage badge
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: _deal!.stage.color.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      _deal!.stage.label,
                      style: AppTypography.caption.copyWith(
                        color: _deal!.stage.color,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Tags
                  ..._deal!.labels.take(2).map((label) => Padding(
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
                    value: _formatCurrency(_deal!.value),
                  ),
                ),
                Expanded(
                  child: _InfoItem(
                    icon: LucideIcons.percent,
                    label: 'PROBABILITY',
                    value: '${_deal!.probability}%',
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
                    value: _deal!.closeDate != null
                        ? _formatDate(_deal!.closeDate!)
                        : 'Not set',
                  ),
                ),
                Expanded(
                  child: _InfoItem(
                    icon: LucideIcons.clock,
                    label: 'CREATED',
                    value: _formatDate(_deal!.createdAt),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Additional Info
            Row(
              children: [
                Expanded(
                  child: _InfoItem(
                    icon: LucideIcons.tag,
                    label: 'TYPE',
                    value: _deal!.opportunityType.label,
                  ),
                ),
                Expanded(
                  child: _InfoItem(
                    icon: LucideIcons.compass,
                    label: 'SOURCE',
                    value: _deal!.leadSource.label,
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
                          name: _deal!.assignedTo,
                          size: AvatarSize.xs,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _deal!.assignedTo,
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
                  '${_deal!.probability}%',
                  style: AppTypography.h3.copyWith(
                    color: _getProbabilityColor(_deal!.probability),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: _deal!.probability / 100,
                minHeight: 8,
                backgroundColor: AppColors.gray200,
                valueColor: AlwaysStoppedAnimation(
                  _getProbabilityColor(_deal!.probability),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _getProbabilityText(_deal!.probability),
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
    final totalProductValue = _deal!.products
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
                    CountBadge(count: _deal!.products.length),
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
            ..._deal!.products.map((product) => Padding(
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

  Widget _buildNotesCard() {
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
            Text(
              'NOTES',
              style: AppTypography.overline.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              _deal!.notes!,
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    final isWon = _deal!.stage == DealStage.closedWon;
    final isLost = _deal!.stage == DealStage.closedLost;
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
                label: _isUpdatingStage ? 'Updating...' : 'Move to ${nextStage!.displayName}',
                icon: LucideIcons.arrowRight,
                iconRight: true,
                onPressed: _isUpdatingStage ? null : () => _handleStageChange(nextStage!),
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

            if (isLost)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  color: AppColors.danger100,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      LucideIcons.xCircle,
                      color: AppColors.danger600,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Deal Lost',
                      style: AppTypography.label.copyWith(
                        color: AppColors.danger600,
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

  void _navigateToEdit() async {
    final result = await context.push('/deals/${widget.dealId}/edit');
    if (result == true) {
      _fetchDeal();
    }
  }

  Future<void> _handleStageChange(DealStage newStage) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Move to ${newStage.displayName}?'),
        content: const Text(
          'This will update the deal stage and probability.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Move'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _isUpdatingStage = true);

    final result = await ref.read(dealsProvider.notifier).updateDealStage(
      widget.dealId,
      newStage,
    );

    if (mounted) {
      setState(() => _isUpdatingStage = false);

      if (result.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Deal moved to ${newStage.displayName}'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        _fetchDeal();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.error ?? 'Failed to update stage'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppColors.danger600,
          ),
        );
      }
    }
  }

  Future<void> _handleMarkLost() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Mark as Lost?'),
        content: const Text(
          'Are you sure you want to mark this deal as lost?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(
              'Mark Lost',
              style: TextStyle(color: AppColors.danger600),
            ),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _isUpdatingStage = true);

    final result = await ref.read(dealsProvider.notifier).updateDealStage(
      widget.dealId,
      DealStage.closedLost,
    );

    if (mounted) {
      setState(() => _isUpdatingStage = false);

      if (result.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Deal marked as lost'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        _fetchDeal();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.error ?? 'Failed to update stage'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppColors.danger600,
          ),
        );
      }
    }
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

  Future<void> _confirmDelete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Deal?'),
        content: const Text(
          'This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(
              'Delete',
              style: TextStyle(color: AppColors.danger600),
            ),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    final result = await ref.read(dealsProvider.notifier).deleteDeal(widget.dealId);

    if (mounted) {
      if (result.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Deal deleted'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        context.pop();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.error ?? 'Failed to delete deal'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppColors.danger600,
          ),
        );
      }
    }
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
    final symbol = ref.read(authProvider).selectedOrganization?.currencySymbol ?? '\$';
    if (value >= 1000000) {
      return '$symbol${(value / 1000000).toStringAsFixed(1)}M';
    } else if (value >= 1000) {
      return '$symbol${(value / 1000).toStringAsFixed(0)}K';
    } else {
      return '$symbol${value.toStringAsFixed(0)}';
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
