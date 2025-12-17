import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../data/mock/mock_data.dart';
import '../../routes/app_router.dart';
import '../../widgets/cards/lead_card.dart';
import '../../widgets/common/common.dart';

/// Leads List Screen
/// Searchable, filterable list of all leads
class LeadsListScreen extends StatefulWidget {
  const LeadsListScreen({super.key});

  @override
  State<LeadsListScreen> createState() => _LeadsListScreenState();
}

class _LeadsListScreenState extends State<LeadsListScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  String _searchQuery = '';
  LeadStatus? _statusFilter;
  LeadSource? _sourceFilter;
  String _sortBy = 'newest';

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  List<Lead> get _filteredLeads {
    var result = List<Lead>.from(MockData.leads);

    // Search filter
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
          if (a.priority == Priority.high && b.priority != Priority.high) {
            return -1;
          }
          if (b.priority == Priority.high && a.priority != Priority.high) {
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
          _buildResultsCount(),

          // Leads List
          Expanded(
            child: _filteredLeads.isEmpty
                ? _buildEmptyState()
                : RefreshIndicator(
                    onRefresh: () async {
                      // Simulate refresh
                      await Future.delayed(const Duration(seconds: 1));
                    },
                    child: ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
                      itemCount: _filteredLeads.length,
                      itemBuilder: (context, index) {
                        final lead = _filteredLeads[index];
                        return LeadCard(
                          lead: lead,
                          onTap: () => context.push('/leads/${lead.id}'),
                        );
                      },
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      color: AppColors.surfaceDim,
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      child: TextField(
        controller: _searchController,
        onChanged: (value) => setState(() => _searchQuery = value),
        decoration: InputDecoration(
          hintText: 'Search leads...',
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
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: AppColors.primary500, width: 1.5),
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
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        child: Row(
          children: [
            // Status Filter
            _FilterChip(
              label: _statusFilter?.displayName ?? 'Status',
              isActive: _statusFilter != null,
              onTap: () => _showStatusFilter(),
            ),

            const SizedBox(width: 8),

            // Source Filter
            _FilterChip(
              label: _sourceFilter?.displayName ?? 'Source',
              isActive: _sourceFilter != null,
              onTap: () => _showSourceFilter(),
            ),

            const SizedBox(width: 8),

            // Sort
            _FilterChip(
              label: 'Sort: ${_getSortLabel()}',
              isActive: _sortBy != 'newest',
              icon: LucideIcons.arrowUpDown,
              onTap: () => _showSortOptions(),
            ),

            if (_hasActiveFilters) ...[
              const SizedBox(width: 8),
              GestureDetector(
                onTap: _clearFilters,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.danger100,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        LucideIcons.x,
                        size: 14,
                        color: AppColors.danger600,
                      ),
                      const SizedBox(width: 4),
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

  Widget _buildResultsCount() {
    return Container(
      width: double.infinity,
      color: AppColors.surfaceDim,
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
      child: Text(
        '${_filteredLeads.length} lead${_filteredLeads.length == 1 ? '' : 's'}',
        style: AppTypography.caption.copyWith(
          color: AppColors.textSecondary,
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    final hasSearchOrFilters =
        _searchQuery.isNotEmpty || _hasActiveFilters;

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
                color: _getStatusColor(status),
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
          ...LeadSource.values.map((source) => _FilterOption(
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

  Color _getStatusColor(LeadStatus status) {
    switch (status) {
      case LeadStatus.newLead:
        return AppColors.primary600;
      case LeadStatus.contacted:
        return AppColors.warning600;
      case LeadStatus.qualified:
        return AppColors.success600;
      case LeadStatus.lost:
        return AppColors.danger600;
    }
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
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? AppColors.primary100 : AppColors.gray100,
          borderRadius: BorderRadius.circular(20),
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
                size: 14,
                color: isActive ? AppColors.primary700 : AppColors.gray600,
              ),
              const SizedBox(width: 4),
            ],
            Text(
              label,
              style: AppTypography.caption.copyWith(
                color: isActive ? AppColors.primary700 : AppColors.gray700,
                fontWeight: isActive ? FontWeight.w600 : FontWeight.w500,
              ),
            ),
            const SizedBox(width: 4),
            Icon(
              LucideIcons.chevronDown,
              size: 14,
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
            margin: const EdgeInsets.only(top: 12),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.gray300,
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // Title
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              title,
              style: AppTypography.h3,
            ),
          ),

          // Options
          ...options.map((option) => option),

          const SizedBox(height: 16),
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
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            if (color != null) ...[
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 12),
            ],
            if (icon != null) ...[
              Icon(
                icon,
                size: 18,
                color: iconColor ?? AppColors.textSecondary,
              ),
              const SizedBox(width: 12),
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
                size: 20,
                color: AppColors.primary600,
              ),
          ],
        ),
      ),
    );
  }
}
