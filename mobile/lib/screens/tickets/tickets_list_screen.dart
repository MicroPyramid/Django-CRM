import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/lookup_models.dart';
import '../../data/models/ticket.dart';
import '../../providers/lookup_provider.dart';
import '../../providers/tickets_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/cards/ticket_card.dart';
import '../../widgets/common/common.dart';
import '../../widgets/forms/multi_select_sheet.dart';

/// Tickets List Screen — paginated list with server- and client-side filters.
class TicketsListScreen extends ConsumerStatefulWidget {
  const TicketsListScreen({super.key});

  @override
  ConsumerState<TicketsListScreen> createState() => _TicketsListScreenState();
}

class _TicketsListScreenState extends ConsumerState<TicketsListScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  TicketListFilters _filters = const TicketListFilters();
  Timer? _searchDebounce;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    _searchDebounce?.cancel();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      ref.read(ticketsProvider.notifier).loadMore(filters: _filters);
    }
  }

  void _applyFilters(TicketListFilters next) {
    setState(() => _filters = next);
    ref.read(ticketsProvider.notifier).refresh(filters: next);
  }

  void _onSearchChanged(String value) {
    _searchDebounce?.cancel();
    _searchDebounce = Timer(const Duration(milliseconds: 300), () {
      _applyFilters(_filters.copyWith(search: value.trim()));
    });
  }

  void _clearFilters() {
    _searchController.clear();
    _applyFilters(const TicketListFilters());
  }

  @override
  Widget build(BuildContext context) {
    final ticketsAsync = ref.watch(ticketsProvider);
    final data = ticketsAsync.value;
    final tickets = data?.tickets ?? const <Ticket>[];

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Tickets'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          IconButton(
            tooltip: 'Analytics',
            icon: const Icon(LucideIcons.barChart3),
            onPressed: () => context.push(AppRoutes.ticketAnalytics),
          ),
          IconButton(
            tooltip: 'Approvals',
            icon: const Icon(LucideIcons.shieldCheck),
            onPressed: () => context.push(AppRoutes.approvalsInbox),
          ),
          IconButton(
            tooltip: 'Knowledge base',
            icon: const Icon(LucideIcons.bookOpen),
            onPressed: () => context.push(AppRoutes.solutions),
          ),
          IconButton(
            tooltip: 'New ticket',
            icon: const Icon(LucideIcons.plus),
            onPressed: () => context.push(AppRoutes.ticketCreate),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildSearchBar(),
          _buildFilterBar(),
          _buildResultsCount(tickets.length, data?.totalCount ?? 0),
          Expanded(child: _buildList(ticketsAsync, tickets)),
        ],
      ),
    );
  }

  Widget _buildList(AsyncValue<TicketsListData> async, List<Ticket> tickets) {
    final data = async.value;

    if (async.isLoading && (data == null || data.tickets.isEmpty)) {
      return const Center(child: CircularProgressIndicator());
    }
    if (async.hasError && (data == null || data.tickets.isEmpty)) {
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
              async.error.toString(),
              style: AppTypography.caption,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () =>
                  ref.read(ticketsProvider.notifier).refresh(filters: _filters),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }
    if (tickets.isEmpty) return _buildEmptyState();

    final hasMore = data?.hasMore ?? false;

    return RefreshIndicator(
      onRefresh: () =>
          ref.read(ticketsProvider.notifier).refresh(filters: _filters),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.fromLTRB(12, 0, 12, 80),
        itemCount: tickets.length + (hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == tickets.length) {
            return const Padding(
              padding: EdgeInsets.all(12),
              child: Center(child: CircularProgressIndicator()),
            );
          }
          final ticketItem = tickets[index];
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
        onChanged: _onSearchChanged,
        style: AppTypography.body,
        decoration: InputDecoration(
          hintText: 'Search tickets...',
          hintStyle: AppTypography.body.copyWith(color: AppColors.textTertiary),
          prefixIcon: Icon(
            LucideIcons.search,
            color: AppColors.textTertiary,
            size: 18,
          ),
          suffixIcon: _filters.search.isNotEmpty
              ? IconButton(
                  icon: Icon(
                    LucideIcons.x,
                    color: AppColors.textTertiary,
                    size: 16,
                  ),
                  onPressed: () {
                    _searchController.clear();
                    _applyFilters(_filters.copyWith(search: ''));
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
    final accounts = ref.watch(accountsProvider);
    final users = ref.watch(usersProvider);
    final tags = ref.watch(tagsProvider);

    final selectedAccount =
        accounts.where((a) => a.id == _filters.accountId).firstOrNull;
    final assigneeLabels = users
        .where((u) => _filters.assigneeIds.contains(u.id))
        .map((u) => u.displayName)
        .toList();
    final tagLabels = tags
        .where((t) => _filters.tagIds.contains(t.id))
        .map((t) => t.name)
        .toList();

    return Container(
      color: AppColors.surface,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.fromLTRB(12, 6, 12, 8),
        child: Row(
          children: [
            _FilterChip(
              label: _filters.status != null
                  ? TicketStatus.fromString(_filters.status).label
                  : 'Status',
              isActive: _filters.status != null,
              onTap: _pickStatus,
            ),
            const SizedBox(width: 6),
            _FilterChip(
              label: _filters.priority != null
                  ? TicketPriority.fromString(_filters.priority).label
                  : 'Priority',
              isActive: _filters.priority != null,
              onTap: _pickPriority,
            ),
            const SizedBox(width: 6),
            _FilterChip(
              label: selectedAccount?.name ?? 'Account',
              isActive: _filters.accountId != null,
              onTap: () => _pickAccount(accounts),
            ),
            const SizedBox(width: 6),
            _FilterChip(
              label: assigneeLabels.isEmpty
                  ? 'Assignees'
                  : 'Assignees · ${assigneeLabels.length}',
              isActive: assigneeLabels.isNotEmpty,
              onTap: () => _pickAssignees(users),
            ),
            const SizedBox(width: 6),
            _FilterChip(
              label: tagLabels.isEmpty ? 'Tags' : 'Tags · ${tagLabels.length}',
              isActive: tagLabels.isNotEmpty,
              onTap: () => _pickTags(tags),
            ),
            const SizedBox(width: 6),
            _FilterChip(
              label: _formatDateRange(),
              isActive: _filters.createdAfter != null ||
                  _filters.createdBefore != null,
              onTap: _pickDateRange,
            ),
            const SizedBox(width: 6),
            _ToggleChip(
              label: 'Watching',
              icon: LucideIcons.eye,
              isActive: _filters.watchingOnly,
              onTap: () => _applyFilters(
                _filters.copyWith(watchingOnly: !_filters.watchingOnly),
              ),
            ),
            if (_filters.hasAny) ...[
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

  String _formatDateRange() {
    final after = _filters.createdAfter;
    final before = _filters.createdBefore;
    if (after == null && before == null) return 'Date';
    String fmt(DateTime d) =>
        '${d.month.toString().padLeft(2, '0')}/${d.day.toString().padLeft(2, '0')}';
    if (after != null && before != null) return '${fmt(after)} → ${fmt(before)}';
    if (after != null) return 'After ${fmt(after)}';
    return 'Before ${fmt(before!)}';
  }

  Widget _buildResultsCount(int filteredCount, int totalCount) {
    return Container(
      width: double.infinity,
      color: AppColors.surfaceDim,
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 8),
      child: Text(
        '$filteredCount ticket${filteredCount == 1 ? '' : 's'}'
        '${_filters.hasAny ? ' (filtered)' : ''}',
        style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
      ),
    );
  }

  Widget _buildEmptyState() {
    return EmptyState(
      icon: _filters.hasAny ? LucideIcons.search : LucideIcons.ticket,
      title: _filters.hasAny ? 'No results found' : 'No tickets yet',
      description: _filters.hasAny
          ? 'Try adjusting your filters'
          : 'Customer-reported issues will appear here',
      actionLabel: _filters.hasAny ? 'Clear filters' : 'Create ticket',
      onAction: _filters.hasAny
          ? _clearFilters
          : () => context.push(AppRoutes.ticketCreate),
    );
  }

  void _pickStatus() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _SimpleFilterSheet(
        title: 'Filter by Status',
        rows: [
          _FilterRow(
            label: 'All Statuses',
            isSelected: _filters.status == null,
            onTap: () {
              Navigator.pop(context);
              _applyFilters(_filters.copyWith(clearStatus: true));
            },
          ),
          ...TicketStatus.values.map(
            (s) => _FilterRow(
              label: s.label,
              isSelected: _filters.status == s.value,
              color: s.color,
              onTap: () {
                Navigator.pop(context);
                _applyFilters(_filters.copyWith(status: s.value));
              },
            ),
          ),
        ],
      ),
    );
  }

  void _pickPriority() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _SimpleFilterSheet(
        title: 'Filter by Priority',
        rows: [
          _FilterRow(
            label: 'All Priorities',
            isSelected: _filters.priority == null,
            onTap: () {
              Navigator.pop(context);
              _applyFilters(_filters.copyWith(clearPriority: true));
            },
          ),
          ...TicketPriority.values.map(
            (p) => _FilterRow(
              label: p.label,
              isSelected: _filters.priority == p.value,
              color: p.color,
              onTap: () {
                Navigator.pop(context);
                _applyFilters(_filters.copyWith(priority: p.value));
              },
            ),
          ),
        ],
      ),
    );
  }

  void _pickAccount(List<AccountLookup> accounts) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (ctx, controller) => Column(
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
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text('Filter by Account', style: AppTypography.h3),
            ),
            _FilterRow(
              label: 'All Accounts',
              isSelected: _filters.accountId == null,
              onTap: () {
                Navigator.pop(context);
                _applyFilters(_filters.copyWith(clearAccountId: true));
              },
            ),
            Expanded(
              child: ListView.builder(
                controller: controller,
                itemCount: accounts.length,
                itemBuilder: (_, i) {
                  final a = accounts[i];
                  return _FilterRow(
                    label: a.name,
                    isSelected: _filters.accountId == a.id,
                    onTap: () {
                      Navigator.pop(context);
                      _applyFilters(_filters.copyWith(accountId: a.id));
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickAssignees(List<UserLookup> users) async {
    final initial =
        users.where((u) => _filters.assigneeIds.contains(u.id)).toList();
    final result = await MultiSelectSheet.show<UserLookup>(
      context: context,
      title: 'Filter by Assignee',
      items: users,
      initialSelection: initial,
      labelOf: (u) => u.displayName,
      searchText: (u) => '${u.email} ${u.displayName}',
      leadingOf: (u) => UserAvatar(name: u.displayName, size: AvatarSize.xs),
    );
    if (result != null) {
      _applyFilters(
        _filters.copyWith(assigneeIds: result.map((u) => u.id).toList()),
      );
    }
  }

  Future<void> _pickTags(List<TagLookup> tags) async {
    final initial = tags.where((t) => _filters.tagIds.contains(t.id)).toList();
    final result = await MultiSelectSheet.show<TagLookup>(
      context: context,
      title: 'Filter by Tag',
      items: tags,
      initialSelection: initial,
      labelOf: (t) => t.name,
      searchText: (t) => t.name,
    );
    if (result != null) {
      _applyFilters(_filters.copyWith(tagIds: result.map((t) => t.id).toList()));
    }
  }

  Future<void> _pickDateRange() async {
    final now = DateTime.now();
    final initial = (_filters.createdAfter != null ||
            _filters.createdBefore != null)
        ? DateTimeRange(
            start: _filters.createdAfter ??
                now.subtract(const Duration(days: 30)),
            end: _filters.createdBefore ?? now,
          )
        : null;
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2000),
      lastDate: now.add(const Duration(days: 1)),
      initialDateRange: initial,
    );
    if (picked != null) {
      _applyFilters(
        _filters.copyWith(
          createdAfter: picked.start,
          createdBefore: picked.end,
        ),
      );
    }
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

class _ToggleChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool isActive;
  final VoidCallback onTap;

  const _ToggleChip({
    required this.label,
    required this.icon,
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
            Icon(
              icon,
              size: 12,
              color: isActive ? AppColors.primary700 : AppColors.gray600,
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: AppTypography.caption.copyWith(
                color: isActive ? AppColors.primary700 : AppColors.gray700,
                fontWeight: isActive ? FontWeight.w600 : FontWeight.w500,
              ),
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
