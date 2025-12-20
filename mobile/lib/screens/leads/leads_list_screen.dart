import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/leads_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/cards/lead_card.dart';
import '../../widgets/common/common.dart';

/// Leads List Screen
/// Searchable, filterable list of all leads
class LeadsListScreen extends ConsumerStatefulWidget {
  const LeadsListScreen({super.key});

  @override
  ConsumerState<LeadsListScreen> createState() => _LeadsListScreenState();
}

class _LeadsListScreenState extends ConsumerState<LeadsListScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  String _searchQuery = '';
  LeadStatus? _statusFilter;
  LeadSource? _sourceFilter;
  String _sortBy = 'newest';

  @override
  void initState() {
    super.initState();
    // Fetch leads when screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(leadsProvider.notifier).fetchLeads(refresh: true);
    });

    // Setup scroll listener for pagination
    _scrollController.addListener(_onScroll);
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(leadsProvider.notifier).loadMore();
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  List<Lead> _filterAndSortLeads(List<Lead> leads) {
    var result = List<Lead>.from(leads);

    // Search filter (client-side for already loaded leads)
    if (_searchQuery.isNotEmpty) {
      final query = _searchQuery.toLowerCase();
      result = result.where((lead) {
        return lead.name.toLowerCase().contains(query) ||
            lead.company.toLowerCase().contains(query) ||
            lead.email.toLowerCase().contains(query);
      }).toList();
    }

    // Status filter
    if (_statusFilter != null) {
      result = result.where((lead) => lead.status == _statusFilter).toList();
    }

    // Source filter
    if (_sourceFilter != null) {
      result = result.where((lead) => lead.source == _sourceFilter).toList();
    }

    // Sorting
    switch (_sortBy) {
      case 'newest':
        result.sort((a, b) => b.createdAt.compareTo(a.createdAt));
        break;
      case 'oldest':
        result.sort((a, b) => a.createdAt.compareTo(b.createdAt));
        break;
      case 'name-asc':
        result.sort((a, b) => a.name.compareTo(b.name));
        break;
      case 'name-desc':
        result.sort((a, b) => b.name.compareTo(a.name));
        break;
      case 'hot':
        result.sort((a, b) {
          if (a.rating == LeadRating.hot && b.rating != LeadRating.hot) {
            return -1;
          }
          if (b.rating == LeadRating.hot && a.rating != LeadRating.hot) {
            return 1;
          }
          return 0;
        });
        break;
    }

    return result;
  }

  void _clearFilters() {
    setState(() {
      _searchQuery = '';
      _searchController.clear();
      _statusFilter = null;
      _sourceFilter = null;
      _sortBy = 'newest';
    });
  }

  bool get _hasActiveFilters {
    return _statusFilter != null || _sourceFilter != null || _sortBy != 'newest';
  }

  @override
  Widget build(BuildContext context) {
    final leadsState = ref.watch(leadsProvider);
    final filteredLeads = _filterAndSortLeads(leadsState.leads);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Leads'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.plus),
            onPressed: () => context.push(AppRoutes.leadCreate),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search Bar
          _buildSearchBar(),

          // Filter Bar
          _buildFilterBar(),

          // Results Count
          _buildResultsCount(filteredLeads.length, leadsState.totalCount),

          // Leads List
          Expanded(
            child: _buildLeadsList(leadsState, filteredLeads),
          ),
        ],
      ),
    );
  }

  Widget _buildLeadsList(LeadsState state, List<Lead> filteredLeads) {
    // Initial loading
    if (state.isLoading && state.leads.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    // Error state
    if (state.error != null && state.leads.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(LucideIcons.alertCircle, size: 48, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'Failed to load leads',
              style: AppTypography.label.copyWith(color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Text(
              state.error!,
              style: AppTypography.caption,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () => ref.read(leadsProvider.notifier).refresh(),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    // Empty state
    if (filteredLeads.isEmpty) {
      return _buildEmptyState();
    }

    // Leads list
    return RefreshIndicator(
      onRefresh: () => ref.read(leadsProvider.notifier).refresh(),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.fromLTRB(12, 0, 12, 80),
        itemCount: filteredLeads.length + (state.hasMore && !_hasActiveFilters ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == filteredLeads.length) {
            // Loading indicator at bottom
            return const Padding(
              padding: EdgeInsets.all(12),
              child: Center(child: CircularProgressIndicator()),
            );
          }

          final lead = filteredLeads[index];
          return LeadCard(
            lead: lead,
            onTap: () => context.push('/leads/${lead.id}'),
          );
        },
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      color: AppColors.surfaceDim,
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 6),
      child: TextField(
        controller: _searchController,
        onChanged: (value) => setState(() => _searchQuery = value),
        style: AppTypography.body,
        decoration: InputDecoration(
          hintText: 'Search leads...',
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
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide(color: AppColors.primary500, width: 1),
          ),
        ),
      ),
    );
  }

  Widget _buildFilterBar() {
    return Container(
      color: AppColors.surface,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.fromLTRB(12, 6, 12, 8),
        child: Row(
          children: [
            // Status Filter
            _FilterChip(
              label: _statusFilter?.displayName ?? 'Status',
              isActive: _statusFilter != null,
              onTap: () => _showStatusFilter(),
            ),

            const SizedBox(width: 6),

            // Source Filter
            _FilterChip(
              label: _sourceFilter?.displayName ?? 'Source',
              isActive: _sourceFilter != null,
              onTap: () => _showSourceFilter(),
            ),

            const SizedBox(width: 6),

            // Sort
            _FilterChip(
              label: 'Sort: ${_getSortLabel()}',
              isActive: _sortBy != 'newest',
              icon: LucideIcons.arrowUpDown,
              onTap: () => _showSortOptions(),
            ),

            if (_hasActiveFilters) ...[
              const SizedBox(width: 6),
              GestureDetector(
                onTap: _clearFilters,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.danger100,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        LucideIcons.x,
                        size: 12,
                        color: AppColors.danger600,
                      ),
                      const SizedBox(width: 3),
                      Text(
                        'Clear',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.danger600,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildResultsCount(int filteredCount, int totalCount) {
    return Container(
      width: double.infinity,
      color: AppColors.surfaceDim,
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 8),
      child: Text(
        '$filteredCount lead${filteredCount == 1 ? '' : 's'}${_hasActiveFilters || _searchQuery.isNotEmpty ? ' (filtered)' : ''}',
        style: AppTypography.caption.copyWith(
          color: AppColors.textSecondary,
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    final hasSearchOrFilters = _searchQuery.isNotEmpty || _hasActiveFilters;

    return EmptyState(
      icon: hasSearchOrFilters ? LucideIcons.search : LucideIcons.users,
      title: hasSearchOrFilters ? 'No results found' : 'No leads yet',
      description: hasSearchOrFilters
          ? 'Try adjusting your search or filters'
          : 'Start by adding your first lead',
      actionLabel: hasSearchOrFilters ? 'Clear filters' : 'Add Lead',
      onAction: hasSearchOrFilters
          ? _clearFilters
          : () => context.push(AppRoutes.leadCreate),
    );
  }

  String _getSortLabel() {
    switch (_sortBy) {
      case 'newest':
        return 'Newest';
      case 'oldest':
        return 'Oldest';
      case 'name-asc':
        return 'A-Z';
      case 'name-desc':
        return 'Z-A';
      case 'hot':
        return 'Hot';
      default:
        return 'Newest';
    }
  }

  void _showStatusFilter() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _FilterBottomSheet(
        title: 'Filter by Status',
        options: [
          _FilterOption(
            label: 'All Statuses',
            isSelected: _statusFilter == null,
            onTap: () {
              setState(() => _statusFilter = null);
              Navigator.pop(context);
            },
          ),
          ...LeadStatus.values.map((status) => _FilterOption(
                label: status.displayName,
                isSelected: _statusFilter == status,
                color: status.color,
                onTap: () {
                  setState(() => _statusFilter = status);
                  Navigator.pop(context);
                },
              )),
        ],
      ),
    );
  }

  void _showSourceFilter() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _FilterBottomSheet(
        title: 'Filter by Source',
        options: [
          _FilterOption(
            label: 'All Sources',
            isSelected: _sourceFilter == null,
            onTap: () {
              setState(() => _sourceFilter = null);
              Navigator.pop(context);
            },
          ),
          ...LeadSource.values.where((s) => s != LeadSource.none).map((source) => _FilterOption(
                label: source.displayName,
                isSelected: _sourceFilter == source,
                onTap: () {
                  setState(() => _sourceFilter = source);
                  Navigator.pop(context);
                },
              )),
        ],
      ),
    );
  }

  void _showSortOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _FilterBottomSheet(
        title: 'Sort by',
        options: [
          _FilterOption(
            label: 'Newest First',
            isSelected: _sortBy == 'newest',
            onTap: () {
              setState(() => _sortBy = 'newest');
              Navigator.pop(context);
            },
          ),
          _FilterOption(
            label: 'Oldest First',
            isSelected: _sortBy == 'oldest',
            onTap: () {
              setState(() => _sortBy = 'oldest');
              Navigator.pop(context);
            },
          ),
          _FilterOption(
            label: 'Name (A-Z)',
            isSelected: _sortBy == 'name-asc',
            onTap: () {
              setState(() => _sortBy = 'name-asc');
              Navigator.pop(context);
            },
          ),
          _FilterOption(
            label: 'Name (Z-A)',
            isSelected: _sortBy == 'name-desc',
            onTap: () {
              setState(() => _sortBy = 'name-desc');
              Navigator.pop(context);
            },
          ),
          _FilterOption(
            label: 'Hot Leads First',
            isSelected: _sortBy == 'hot',
            icon: LucideIcons.flame,
            iconColor: AppColors.danger500,
            onTap: () {
              setState(() => _sortBy = 'hot');
              Navigator.pop(context);
            },
          ),
        ],
      ),
    );
  }
}

/// Filter chip widget
class _FilterChip extends StatelessWidget {
  final String label;
  final bool isActive;
  final IconData? icon;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.isActive,
    this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: AppDurations.fast,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
        decoration: BoxDecoration(
          color: isActive ? AppColors.primary100 : AppColors.gray100,
          borderRadius: BorderRadius.circular(4),
          border: isActive
              ? Border.all(color: AppColors.primary300, width: 1)
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(
                icon,
                size: 12,
                color: isActive ? AppColors.primary700 : AppColors.gray600,
              ),
              const SizedBox(width: 3),
            ],
            Text(
              label,
              style: AppTypography.caption.copyWith(
                color: isActive ? AppColors.primary700 : AppColors.gray700,
                fontWeight: isActive ? FontWeight.w600 : FontWeight.w500,
              ),
            ),
            const SizedBox(width: 3),
            Icon(
              LucideIcons.chevronDown,
              size: 12,
              color: isActive ? AppColors.primary700 : AppColors.gray600,
            ),
          ],
        ),
      ),
    );
  }
}

/// Filter bottom sheet
class _FilterBottomSheet extends StatelessWidget {
  final String title;
  final List<_FilterOption> options;

  const _FilterBottomSheet({
    required this.title,
    required this.options,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle
          Container(
            margin: const EdgeInsets.only(top: 8),
            width: 32,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.gray300,
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // Title
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text(
              title,
              style: AppTypography.label,
            ),
          ),

          // Options
          ...options.map((option) => option),

          const SizedBox(height: 12),
        ],
      ),
    );
  }
}

/// Filter option item
class _FilterOption extends StatelessWidget {
  final String label;
  final bool isSelected;
  final Color? color;
  final IconData? icon;
  final Color? iconColor;
  final VoidCallback onTap;

  const _FilterOption({
    required this.label,
    required this.isSelected,
    this.color,
    this.icon,
    this.iconColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          children: [
            if (color != null) ...[
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 10),
            ],
            if (icon != null) ...[
              Icon(
                icon,
                size: 16,
                color: iconColor ?? AppColors.textSecondary,
              ),
              const SizedBox(width: 10),
            ],
            Expanded(
              child: Text(
                label,
                style: AppTypography.body.copyWith(
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  color: isSelected ? AppColors.primary600 : AppColors.textPrimary,
                ),
              ),
            ),
            if (isSelected)
              Icon(
                LucideIcons.check,
                size: 18,
                color: AppColors.primary600,
              ),
          ],
        ),
      ),
    );
  }
}
