import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/solution.dart';
import '../../providers/solutions_provider.dart';
import '../../widgets/common/common.dart';

/// Standalone Solutions (Knowledge Base) list screen.
class SolutionsListScreen extends ConsumerStatefulWidget {
  const SolutionsListScreen({super.key});

  @override
  ConsumerState<SolutionsListScreen> createState() =>
      _SolutionsListScreenState();
}

class _SolutionsListScreenState extends ConsumerState<SolutionsListScreen> {
  final _searchController = TextEditingController();
  Timer? _debounce;
  String _search = '';
  SolutionStatus? _status;
  bool _publishedOnly = false;

  @override
  void dispose() {
    _searchController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  void _applyFilters() {
    ref.read(solutionsProvider.notifier).refresh(
          search: _search.isEmpty ? null : _search,
          status: _status,
          publishedOnly: _publishedOnly ? true : null,
        );
  }

  void _onSearchChanged(String v) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      setState(() => _search = v.trim());
      _applyFilters();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(solutionsProvider);
    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Solutions'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        leading: IconButton(
          icon: const Icon(LucideIcons.chevronLeft),
          onPressed: () => context.pop(),
        ),
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.plus),
            onPressed: () => context.push('/solutions/new'),
          ),
        ],
      ),
      body: Column(
        children: [
          _searchBar(),
          _filterBar(),
          Expanded(child: _body(state)),
        ],
      ),
    );
  }

  Widget _searchBar() {
    return Container(
      color: AppColors.surfaceDim,
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 6),
      child: TextField(
        controller: _searchController,
        onChanged: _onSearchChanged,
        style: AppTypography.body,
        decoration: InputDecoration(
          hintText: 'Search the knowledge base…',
          hintStyle: AppTypography.body.copyWith(color: AppColors.textTertiary),
          prefixIcon: Icon(
            LucideIcons.search,
            color: AppColors.textTertiary,
            size: 18,
          ),
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

  Widget _filterBar() {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 8),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            for (final s in [null, ...SolutionStatus.values])
              Padding(
                padding: const EdgeInsets.only(right: 6),
                child: ChoiceChip(
                  label: Text(s == null ? 'All' : s.label),
                  selected: _status == s,
                  onSelected: (_) {
                    setState(() => _status = s);
                    _applyFilters();
                  },
                ),
              ),
            const SizedBox(width: 6),
            FilterChip(
              label: const Text('Published only'),
              selected: _publishedOnly,
              onSelected: (v) {
                setState(() => _publishedOnly = v);
                _applyFilters();
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _body(SolutionsListData state) {
    if (state.isLoading && state.solutions.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null && state.solutions.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(LucideIcons.alertCircle, size: 48, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(state.error!, style: AppTypography.body),
            const SizedBox(height: 16),
            TextButton(onPressed: _applyFilters, child: const Text('Retry')),
          ],
        ),
      );
    }
    if (state.solutions.isEmpty) {
      return EmptyState(
        icon: LucideIcons.bookOpen,
        title: 'No solutions yet',
        description: 'Reusable answers for common issues live here.',
        actionLabel: 'Create solution',
        onAction: () => context.push('/solutions/new'),
      );
    }
    return RefreshIndicator(
      onRefresh: () async => _applyFilters(),
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(12, 0, 12, 80),
        itemCount: state.solutions.length,
        itemBuilder: (_, i) => _SolutionTile(
          solution: state.solutions[i],
          onTap: () => context.push('/solutions/${state.solutions[i].id}'),
        ),
      ),
    );
  }
}

class _SolutionTile extends StatelessWidget {
  final Solution solution;
  final VoidCallback onTap;
  const _SolutionTile({required this.solution, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppLayout.borderRadiusLg,
        border: Border.all(color: AppColors.border),
      ),
      child: InkWell(
        borderRadius: AppLayout.borderRadiusLg,
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      solution.title,
                      style: AppTypography.label.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  StatusBadge(
                    label: solution.status.label,
                    color: solution.status.color,
                  ),
                  if (solution.isPublished) ...[
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 6,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.primary100,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        'Published',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.primary700,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 6),
              Text(
                solution.description,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 6),
              Row(
                children: [
                  Icon(LucideIcons.link, size: 12, color: AppColors.gray400),
                  const SizedBox(width: 4),
                  Text(
                    '${solution.caseCount} linked',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textTertiary,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
