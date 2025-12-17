import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../data/mock/mock_data.dart';
import '../../widgets/cards/deal_card.dart';
import '../../widgets/misc/kanban_column.dart';
import '../../widgets/common/common.dart';

enum ViewMode { kanban, list }

/// Deals List Screen
/// Pipeline view with Kanban board or list layout
class DealsListScreen extends StatefulWidget {
  const DealsListScreen({super.key});

  @override
  State<DealsListScreen> createState() => _DealsListScreenState();
}

class _DealsListScreenState extends State<DealsListScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _kanbanScrollController = ScrollController();

  bool _showSearch = false;
  String _searchQuery = '';
  ViewMode _viewMode = ViewMode.kanban;

  // Active pipeline stages (excluding closed-lost for Kanban)
  static const List<DealStage> _kanbanStages = [
    DealStage.prospecting,
    DealStage.qualified,
    DealStage.proposal,
    DealStage.negotiation,
    DealStage.closedWon,
  ];

  @override
  void dispose() {
    _searchController.dispose();
    _kanbanScrollController.dispose();
    super.dispose();
  }

  List<Deal> get _filteredDeals {
    var result = List<Deal>.from(MockData.deals);

    if (_searchQuery.isNotEmpty) {
      final query = _searchQuery.toLowerCase();
      result = result.where((deal) {
        return deal.title.toLowerCase().contains(query) ||
            deal.companyName.toLowerCase().contains(query);
      }).toList();
    }

    return result;
  }

  Map<DealStage, List<Deal>> get _dealsByStage {
    final Map<DealStage, List<Deal>> grouped = {};
    for (final stage in _kanbanStages) {
      grouped[stage] =
          _filteredDeals.where((deal) => deal.stage == stage).toList();
    }
    return grouped;
  }

  void _handleDealMoved(Deal deal, DealStage newStage) {
    // In a real app, this would update the backend
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Moved "${deal.title}" to ${newStage.displayName}'),
        behavior: SnackBarBehavior.floating,
        action: SnackBarAction(
          label: 'Undo',
          onPressed: () {},
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Deals'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          // Search toggle
          IconButton(
            icon: Icon(
              _showSearch ? LucideIcons.x : LucideIcons.search,
              size: 22,
            ),
            onPressed: () {
              setState(() {
                _showSearch = !_showSearch;
                if (!_showSearch) {
                  _searchQuery = '';
                  _searchController.clear();
                }
              });
            },
          ),

          // View mode toggle
          IconButton(
            icon: Icon(
              _viewMode == ViewMode.kanban
                  ? LucideIcons.list
                  : LucideIcons.layoutGrid,
              size: 22,
            ),
            onPressed: () {
              setState(() {
                _viewMode = _viewMode == ViewMode.kanban
                    ? ViewMode.list
                    : ViewMode.kanban;
              });
            },
          ),

          // Add new deal
          IconButton(
            icon: const Icon(LucideIcons.plus, size: 22),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Create deal coming soon'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Collapsible Search Bar
          AnimatedCrossFade(
            firstChild: const SizedBox.shrink(),
            secondChild: _buildSearchBar(),
            crossFadeState: _showSearch
                ? CrossFadeState.showSecond
                : CrossFadeState.showFirst,
            duration: AppDurations.normal,
          ),

          // Pipeline Summary
          _buildPipelineSummary(),

          // View Content
          Expanded(
            child: AnimatedSwitcher(
              duration: AppDurations.normal,
              child: _viewMode == ViewMode.kanban
                  ? _buildKanbanView()
                  : _buildListView(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
      child: TextField(
        controller: _searchController,
        autofocus: true,
        onChanged: (value) => setState(() => _searchQuery = value),
        decoration: InputDecoration(
          hintText: 'Search deals...',
          hintStyle: AppTypography.body.copyWith(
            color: AppColors.textTertiary,
          ),
          prefixIcon: Icon(
            LucideIcons.search,
            color: AppColors.textTertiary,
            size: 20,
          ),
          suffixIcon: _searchQuery.isNotEmpty
              ? IconButton(
                  icon: Icon(
                    LucideIcons.x,
                    color: AppColors.textTertiary,
                    size: 18,
                  ),
                  onPressed: () {
                    _searchController.clear();
                    setState(() => _searchQuery = '');
                  },
                )
              : null,
          filled: true,
          fillColor: AppColors.gray100,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 12,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }

  Widget _buildPipelineSummary() {
    final totalValue = _filteredDeals
        .where((d) =>
            d.stage != DealStage.closedLost && d.stage != DealStage.closedWon)
        .fold<double>(0, (sum, deal) => sum + deal.value);

    final activeDeals = _filteredDeals
        .where((d) =>
            d.stage != DealStage.closedLost && d.stage != DealStage.closedWon)
        .length;

    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
      child: Row(
        children: [
          _SummaryChip(
            icon: LucideIcons.dollarSign,
            label: _formatCurrency(totalValue),
            sublabel: 'Pipeline',
          ),
          const SizedBox(width: 12),
          _SummaryChip(
            icon: LucideIcons.briefcase,
            label: '$activeDeals',
            sublabel: 'Active deals',
          ),
        ],
      ),
    );
  }

  Widget _buildKanbanView() {
    final screenWidth = MediaQuery.of(context).size.width;
    final columnWidth = screenWidth * 0.85;

    return RefreshIndicator(
      onRefresh: () async {
        await Future.delayed(const Duration(seconds: 1));
      },
      child: SingleChildScrollView(
        controller: _kanbanScrollController,
        scrollDirection: Axis.horizontal,
        physics: const PageScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(10, 12, 10, 100),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: _kanbanStages.map((stage) {
            return KanbanColumn(
              stage: stage,
              deals: _dealsByStage[stage] ?? [],
              width: columnWidth,
              onDealTap: (deal) => context.push('/deals/${deal.id}'),
              onDealMoved: _handleDealMoved,
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildListView() {
    if (_filteredDeals.isEmpty) {
      return EmptyState(
        icon: LucideIcons.briefcase,
        title: _searchQuery.isNotEmpty ? 'No results found' : 'No deals yet',
        description: _searchQuery.isNotEmpty
            ? 'Try adjusting your search'
            : 'Start by creating your first deal',
        actionLabel: _searchQuery.isNotEmpty ? 'Clear search' : 'Add Deal',
        onAction: _searchQuery.isNotEmpty
            ? () {
                _searchController.clear();
                setState(() => _searchQuery = '');
              }
            : () {},
      );
    }

    return RefreshIndicator(
      onRefresh: () async {
        await Future.delayed(const Duration(seconds: 1));
      },
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
        itemCount: _kanbanStages.length,
        itemBuilder: (context, index) {
          final stage = _kanbanStages[index];
          final stageDeals = _dealsByStage[stage] ?? [];

          if (stageDeals.isEmpty) return const SizedBox.shrink();

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Stage Header
              _buildStageHeader(stage, stageDeals),

              // Stage Deals
              ...stageDeals.map((deal) => DealCard(
                    deal: deal,
                    onTap: () => context.push('/deals/${deal.id}'),
                  )),

              const SizedBox(height: 16),
            ],
          );
        },
      ),
    );
  }

  Widget _buildStageHeader(DealStage stage, List<Deal> deals) {
    final totalValue = deals.fold<double>(0, (sum, deal) => sum + deal.value);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.gray100,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              color: _getStageColor(stage),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 10),
          Text(
            stage.displayName,
            style: AppTypography.label.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: AppColors.gray200,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              '${deals.length}',
              style: AppTypography.caption.copyWith(
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
              ),
            ),
          ),
          const Spacer(),
          Text(
            _formatCurrency(totalValue),
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
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

  String _formatCurrency(double value) {
    if (value >= 1000000) {
      return '\$${(value / 1000000).toStringAsFixed(1)}M';
    } else if (value >= 1000) {
      return '\$${(value / 1000).toStringAsFixed(0)}K';
    } else {
      return '\$${value.toStringAsFixed(0)}';
    }
  }
}

/// Summary chip widget
class _SummaryChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final String sublabel;

  const _SummaryChip({
    required this.icon,
    required this.label,
    required this.sublabel,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.gray50,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 18,
            color: AppColors.primary600,
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: AppTypography.label.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              Text(
                sublabel,
                style: AppTypography.caption.copyWith(
                  color: AppColors.textTertiary,
                  fontSize: 10,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
