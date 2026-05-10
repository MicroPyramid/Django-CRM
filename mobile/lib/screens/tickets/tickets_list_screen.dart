import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/ticket.dart';
import '../../providers/tickets_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/cards/ticket_card.dart';
import '../../widgets/common/common.dart';

/// Tickets List Screen
class TicketsListScreen extends ConsumerStatefulWidget {
  const TicketsListScreen({super.key});

  @override
  ConsumerState<TicketsListScreen> createState() => _TicketsListScreenState();
}

class _TicketsListScreenState extends ConsumerState<TicketsListScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  String _searchQuery = '';
  TicketStatus? _statusFilter;
  TicketPriority? _priorityFilter;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(ticketsProvider.notifier).fetchTickets(refresh: true);
    });
    _scrollController.addListener(_onScroll);
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(ticketsProvider.notifier).loadMore();
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  List<Ticket> _filterTickets(List<Ticket> tickets) {
    var result = List<Ticket>.from(tickets);
    if (_searchQuery.isNotEmpty) {
      final q = _searchQuery.toLowerCase();
      result = result.where((c) {
        return c.name.toLowerCase().contains(q) ||
            (c.accountName?.toLowerCase().contains(q) ?? false);
      }).toList();
    }
    if (_statusFilter != null) {
      result = result.where((c) => c.status == _statusFilter).toList();
    }
    if (_priorityFilter != null) {
      result = result.where((c) => c.priority == _priorityFilter).toList();
    }
    return result;
  }

  void _clearFilters() {
    setState(() {
      _searchQuery = '';
      _searchController.clear();
      _statusFilter = null;
      _priorityFilter = null;
    });
  }

  bool get _hasActiveFilters =>
      _statusFilter != null || _priorityFilter != null;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(ticketsProvider);
    final filtered = _filterTickets(state.tickets);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Tickets'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.plus),
            onPressed: () => context.push(AppRoutes.ticketCreate),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildSearchBar(),
          _buildFilterBar(),
          _buildResultsCount(filtered.length, state.totalCount),
          Expanded(child: _buildList(state, filtered)),
        ],
      ),
    );
  }

  Widget _buildList(TicketsState state, List<Ticket> filtered) {
    if (state.isLoading && state.tickets.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null && state.tickets.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(LucideIcons.alertCircle, size: 48, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'Failed to load tickets',
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
              onPressed: () => ref.read(ticketsProvider.notifier).refresh(),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }
    if (filtered.isEmpty) return _buildEmptyState();

    return RefreshIndicator(
      onRefresh: () => ref.read(ticketsProvider.notifier).refresh(),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.fromLTRB(12, 0, 12, 80),
        itemCount:
            filtered.length + (state.hasMore && !_hasActiveFilters ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == filtered.length) {
            return const Padding(
              padding: EdgeInsets.all(12),
              child: Center(child: CircularProgressIndicator()),
            );
          }
          final ticketItem = filtered[index];
          return TicketCard(
            ticketItem: ticketItem,
            onTap: () => context.push('/tickets/${ticketItem.id}'),
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
          hintText: 'Search tickets...',
          hintStyle: AppTypography.body.copyWith(color: AppColors.textTertiary),
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
            _FilterChip(
              label: _statusFilter?.displayName ?? 'Status',
              isActive: _statusFilter != null,
              onTap: _showStatusFilter,
            ),
            const SizedBox(width: 6),
            _FilterChip(
              label: _priorityFilter?.displayName ?? 'Priority',
              isActive: _priorityFilter != null,
              onTap: _showPriorityFilter,
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
                      Icon(LucideIcons.x, size: 12, color: AppColors.danger600),
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
        '$filteredCount ticket${filteredCount == 1 ? '' : 's'}'
        '${_hasActiveFilters || _searchQuery.isNotEmpty ? ' (filtered)' : ''}',
        style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
      ),
    );
  }

  Widget _buildEmptyState() {
    final hasFilters = _searchQuery.isNotEmpty || _hasActiveFilters;
    return EmptyState(
      icon: hasFilters ? LucideIcons.search : LucideIcons.ticket,
      title: hasFilters ? 'No results found' : 'No tickets yet',
      description: hasFilters
          ? 'Try adjusting your search or filters'
          : 'Customer-reported issues will appear here',
      actionLabel: hasFilters ? 'Clear filters' : 'Create ticket',
      onAction: hasFilters
          ? _clearFilters
          : () => context.push(AppRoutes.ticketCreate),
    );
  }

  void _showStatusFilter() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _SimpleFilterSheet(
        title: 'Filter by Status',
        rows: [
          _FilterRow(
            label: 'All Statuses',
            isSelected: _statusFilter == null,
            onTap: () {
              setState(() => _statusFilter = null);
              Navigator.pop(context);
            },
          ),
          ...TicketStatus.values.map(
            (s) => _FilterRow(
              label: s.label,
              isSelected: _statusFilter == s,
              color: s.color,
              onTap: () {
                setState(() => _statusFilter = s);
                Navigator.pop(context);
              },
            ),
          ),
        ],
      ),
    );
  }

  void _showPriorityFilter() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _SimpleFilterSheet(
        title: 'Filter by Priority',
        rows: [
          _FilterRow(
            label: 'All Priorities',
            isSelected: _priorityFilter == null,
            onTap: () {
              setState(() => _priorityFilter = null);
              Navigator.pop(context);
            },
          ),
          ...TicketPriority.values.map(
            (p) => _FilterRow(
              label: p.label,
              isSelected: _priorityFilter == p,
              color: p.color,
              onTap: () {
                setState(() => _priorityFilter = p);
                Navigator.pop(context);
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.isActive,
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

class _SimpleFilterSheet extends StatelessWidget {
  final String title;
  final List<_FilterRow> rows;

  const _SimpleFilterSheet({required this.title, required this.rows});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 8),
            width: 32,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.gray300,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text(title, style: AppTypography.label),
          ),
          ...rows,
          const SizedBox(height: 12),
        ],
      ),
    );
  }
}

class _FilterRow extends StatelessWidget {
  final String label;
  final bool isSelected;
  final Color? color;
  final VoidCallback onTap;

  const _FilterRow({
    required this.label,
    required this.isSelected,
    this.color,
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
                decoration: BoxDecoration(color: color, shape: BoxShape.circle),
              ),
              const SizedBox(width: 10),
            ],
            Expanded(
              child: Text(
                label,
                style: AppTypography.body.copyWith(
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  color: isSelected
                      ? AppColors.primary600
                      : AppColors.textPrimary,
                ),
              ),
            ),
            if (isSelected)
              Icon(LucideIcons.check, size: 18, color: AppColors.primary600),
          ],
        ),
      ),
    );
  }
}
