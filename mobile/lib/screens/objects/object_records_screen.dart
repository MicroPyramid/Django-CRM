import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/custom_object.dart';
import '../../providers/custom_objects_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/common/common.dart';

const _missingObject =
    'This object does not exist, or you do not have access to it.';

/// The records of one custom object, searchable and paged by the server.
class ObjectRecordsScreen extends ConsumerStatefulWidget {
  const ObjectRecordsScreen({super.key, required this.objectKey});

  final String objectKey;

  @override
  ConsumerState<ObjectRecordsScreen> createState() =>
      _ObjectRecordsScreenState();
}

class _ObjectRecordsScreenState extends ConsumerState<ObjectRecordsScreen> {
  final _search = TextEditingController();
  final _scroll = ScrollController();
  Timer? _debounce;

  static const _debounceMs = 300;

  @override
  void initState() {
    super.initState();
    _scroll.addListener(_onScroll);
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scroll.position.pixels >= _scroll.position.maxScrollExtent - 200) {
      ref.read(objectRecordsProvider(widget.objectKey).notifier).loadMore();
    }
  }

  void _onSearchChanged(String value) {
    setState(() {});
    _debounce?.cancel();
    _debounce = Timer(
      const Duration(milliseconds: _debounceMs),
      () => ref
          .read(objectRecordsProvider(widget.objectKey).notifier)
          .setQuery(value),
    );
  }

  void _clearSearch() {
    _search.clear();
    _onSearchChanged('');
  }

  @override
  Widget build(BuildContext context) {
    final definition = ref.watch(objectDefinitionProvider(widget.objectKey));

    return definition.when(
      loading: () => _shell(
        title: 'Records',
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (e, _) => _shell(
        title: 'Records',
        body: _ErrorView(
          message: 'Failed to load this object',
          onRetry: () =>
              ref.invalidate(objectDefinitionProvider(widget.objectKey)),
        ),
      ),
      data: (def) {
        if (def == null) {
          return _shell(
            title: 'Records',
            body: const EmptyState(
              icon: LucideIcons.boxes,
              title: _missingObject,
            ),
          );
        }
        final canWrite =
            shownCustomObjects(
              ref.watch(customObjectsProvider),
            )?.hasCustomObjects ==
            true;
        return _shell(
          title: def.summary.labelPlural,
          body: Column(
            children: [
              _searchBar(def.summary),
              Expanded(child: _list(def)),
            ],
          ),
          fab: canWrite
              ? AppFAB(
                  icon: LucideIcons.plus,
                  label: 'New ${def.summary.label}',
                  onPressed: () => context.push(
                    AppRoutes.objectRecordCreate(widget.objectKey),
                  ),
                )
              : null,
        );
      },
    );
  }

  Widget _shell({required String title, required Widget body, Widget? fab}) {
    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: Text(title),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      body: body,
      floatingActionButton: fab,
    );
  }

  Widget _searchBar(ObjectSummary summary) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 6),
      child: TextField(
        controller: _search,
        onChanged: _onSearchChanged,
        style: AppTypography.body,
        textInputAction: TextInputAction.search,
        decoration: InputDecoration(
          hintText: 'Search ${summary.labelPlural.toLowerCase()}',
          hintStyle: AppTypography.body.copyWith(color: AppColors.textTertiary),
          prefixIcon: Icon(
            LucideIcons.search,
            color: AppColors.textTertiary,
            size: 18,
          ),
          suffixIcon: _search.text.isEmpty
              ? null
              : IconButton(
                  tooltip: 'Clear search',
                  icon: Icon(
                    LucideIcons.x,
                    color: AppColors.textTertiary,
                    size: 16,
                  ),
                  onPressed: _clearSearch,
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

  Widget _list(ObjectDefinition def) {
    final async = ref.watch(objectRecordsProvider(widget.objectKey));
    final notifier = ref.read(objectRecordsProvider(widget.objectKey).notifier);
    final data = async.value;

    if (async.isLoading && (data == null || data.records.isEmpty)) {
      return const Center(child: CircularProgressIndicator());
    }
    if (async.hasError && (data == null || data.records.isEmpty)) {
      return _ErrorView(
        message: 'Failed to load records',
        onRetry: notifier.refresh,
      );
    }
    final records = data?.records ?? const <ObjectRecord>[];
    if (records.isEmpty) {
      final searching = (data?.query ?? '').isNotEmpty;
      return RefreshIndicator(
        onRefresh: notifier.refresh,
        child: LayoutBuilder(
          builder: (context, box) => SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: SizedBox(
              height: box.maxHeight,
              child: EmptyState(
                icon: LucideIcons.boxes,
                title: searching
                    ? 'No matching ${def.summary.labelPlural.toLowerCase()}'
                    : 'No ${def.summary.labelPlural.toLowerCase()} yet',
              ),
            ),
          ),
        ),
      );
    }

    final hasMore = data?.hasMore ?? false;
    return RefreshIndicator(
      onRefresh: notifier.refresh,
      child: ListView.builder(
        controller: _scroll,
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(12, 0, 12, 80),
        itemCount: records.length + (hasMore ? 1 : 0),
        itemBuilder: (context, i) {
          if (i == records.length) {
            return const Padding(
              padding: EdgeInsets.all(12),
              child: Center(child: CircularProgressIndicator()),
            );
          }
          return _RecordRow(
            record: records[i],
            fields: def.customFields,
            onTap: () => context.push(
              AppRoutes.objectRecord(widget.objectKey, records[i].id),
            ),
          );
        },
      ),
    );
  }
}

class _RecordRow extends StatelessWidget {
  const _RecordRow({
    required this.record,
    required this.fields,
    required this.onTap,
  });

  final ObjectRecord record;
  final List<ObjectField> fields;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final shown = [
      for (final f in fields)
        if (hasFieldValue(record.customFields[f.key]))
          '${f.label}: ${displayValue(f, record.customFields[f.key])}',
    ].take(2).toList();
    final assignees = record.assignedTo.length;

    return Container(
      margin: const EdgeInsets.only(top: 8),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.gray200),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      record.name,
                      style: AppTypography.body.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    for (final line in shown)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(
                          line,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: AppTypography.caption.copyWith(
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
              if (assignees > 0) ...[
                const SizedBox(width: 12),
                Icon(
                  LucideIcons.users,
                  size: 16,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(width: 4),
                Text(
                  '$assignees',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(LucideIcons.alertCircle, size: 48, color: AppColors.gray400),
          const SizedBox(height: 16),
          Text(message, style: AppTypography.label),
          const SizedBox(height: 8),
          TextButton(onPressed: onRetry, child: const Text('Retry')),
        ],
      ),
    );
  }
}
