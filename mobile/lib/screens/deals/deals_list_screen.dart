import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/auth_provider.dart';
import '../../providers/deals_provider.dart';
import '../../widgets/cards/deal_card.dart';
import '../../widgets/misc/kanban_column.dart';
import '../../widgets/common/common.dart';

enum ViewMode { kanban, list }

/// Deals List Screen
/// Pipeline view with Kanban board or list layout
class DealsListScreen extends ConsumerStatefulWidget {
  const DealsListScreen({super.key});

  @override
  ConsumerState<DealsListScreen> createState() => _DealsListScreenState();
}

class _DealsListScreenState extends ConsumerState<DealsListScreen> {
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
  void initState() {
    super.initState();
    // Fetch deals on screen load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(dealsProvider.notifier).fetchDeals(refresh: true);
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    _kanbanScrollController.dispose();
    super.dispose();
  }

  List<Deal> get _filteredDeals {
    final deals = ref.watch(dealsListProvider);
    var result = List<Deal>.from(deals);

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
            onPressed: () async {
              final result = await context.push('/deals/create');
              if (result == true) {
                ref.read(dealsProvider.notifier).refresh();
              }
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
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 8),
      child: TextField(
        controller: _searchController,
        autofocus: true,
        style: AppTypography.body,
        onChanged: (value) => setState(() => _searchQuery = value),
        decoration: InputDecoration(
          hintText: 'Search deals...',
          hintStyle: AppTypography.body.copyWith(
            color: AppColors.textTertiary,
          ),
          prefixIcon: Icon(
            LucideIcons.search,
            color: AppColors.textTertiary,
            size: 18,
          ),
          suffixIcon: _searchQuery.isNotEmpty
              ? IconButton(
                  icon: Icon(
                    LucideIcons.x,
                    color: AppColors.textTertiary,
                    size: 16,
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
            horizontal: 12,
            vertical: 10,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }

  Widget _buildPipelineSummary() {
    final totalValue = ref.watch(pipelineValueProvider);
    final activeDeals = ref.watch(activeDealsCountProvider);

    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 8),
      child: Row(
        children: [
          _SummaryChip(
            icon: LucideIcons.dollarSign,
            label: _formatCurrency(totalValue),
            sublabel: 'Pipeline',
          ),
          const SizedBox(width: 8),
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
    final isLoading = ref.watch(dealsLoadingProvider);
    final error = ref.watch(dealsErrorProvider);
    final screenWidth = MediaQuery.of(context).size.width;
    final columnWidth = screenWidth * 0.85;

    // Show loading indicator on first load
    if (isLoading && _filteredDeals.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    // Show error if any
    if (error != null && _filteredDeals.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(LucideIcons.alertCircle, size: 48, color: AppColors.danger500),
            const SizedBox(height: 16),
            Text(error, style: AppTypography.body.copyWith(color: AppColors.textSecondary)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => ref.read(dealsProvider.notifier).refresh(),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    // RefreshIndicator needs vertical scroll, so wrap in CustomScrollView
    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(dealsProvider.notifier).refresh();
      },
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverFillRemaining(
            child: SingleChildScrollView(
              controller: _kanbanScrollController,
              scrollDirection: Axis.horizontal,
              physics: const PageScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(8, 8, 8, 80),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: _kanbanStages.map((stage) {
                  final currencySymbol = ref.read(authProvider).selectedOrganization?.currencySymbol ?? '\$';
                  return KanbanColumn(
                    stage: stage,
                    deals: _dealsByStage[stage] ?? [],
                    width: columnWidth,
                    onDealTap: (deal) => context.push('/deals/${deal.id}'),
                    onDealMoved: _handleDealMoved,
                    currencySymbol: currencySymbol,
                  );
                }).toList(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildListView() {
    final isLoading = ref.watch(dealsLoadingProvider);
    final error = ref.watch(dealsErrorProvider);

    // Show loading indicator on first load
    if (isLoading && _filteredDeals.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    // Show error if any
    if (error != null && _filteredDeals.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(LucideIcons.alertCircle, size: 48, color: AppColors.danger500),
            const SizedBox(height: 16),
            Text(error, style: AppTypography.body.copyWith(color: AppColors.textSecondary)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => ref.read(dealsProvider.notifier).refresh(),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

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
            : () async {
                final result = await context.push('/deals/create');
                if (result == true) {
                  ref.read(dealsProvider.notifier).refresh();
                }
              },
      );
    }

    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(dealsProvider.notifier).refresh();
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
              ...stageDeals.map((deal) {
                final currencySymbol = ref.read(authProvider).selectedOrganization?.currencySymbol ?? '\$';
                return DealCard(
                  deal: deal,
                  onTap: () => context.push('/deals/${deal.id}'),
                  currencySymbol: currencySymbol,
                );
              }),

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
    final symbol = ref.read(authProvider).selectedOrganization?.currencySymbol ?? '\$';
    if (value >= 1000000) {
      return '$symbol${(value / 1000000).toStringAsFixed(1)}M';
    } else if (value >= 1000) {
      return '$symbol${(value / 1000).toStringAsFixed(0)}K';
    } else {
      return '$symbol${value.toStringAsFixed(0)}';
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
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
