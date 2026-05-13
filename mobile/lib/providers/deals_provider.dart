import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/deal.dart';
import '../services/api_service.dart';

/// Paginated deals snapshot — wrapped by AsyncValue for loading/error.
class DealsListData {
  final List<Deal> deals;
  final int totalCount;
  final bool hasMore;
  final int currentOffset;

  const DealsListData({
    this.deals = const [],
    this.totalCount = 0,
    this.hasMore = true,
    this.currentOffset = 0,
  });

  DealsListData copyWith({
    List<Deal>? deals,
    int? totalCount,
    bool? hasMore,
    int? currentOffset,
  }) {
    return DealsListData(
      deals: deals ?? this.deals,
      totalCount: totalCount ?? this.totalCount,
      hasMore: hasMore ?? this.hasMore,
      currentOffset: currentOffset ?? this.currentOffset,
    );
  }
}

/// AsyncNotifier driving the deals list + CRUD. The list page is the only
/// place that watches this; detail/form screens use the notifier directly
/// for one-shot fetches and mutations.
class DealsNotifier extends AsyncNotifier<DealsListData> {
  final ApiService _apiService = ApiService();
  static const int _pageSize = 20;

  @override
  Future<DealsListData> build() => _fetchPage(offset: 0);

  /// Reload the first page (pull-to-refresh / after CRUD).
  Future<void> refresh({String? search, String? stage}) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => _fetchPage(offset: 0, search: search, stage: stage),
    );
  }

  /// Append the next page if there's more and we're not already loading.
  Future<void> loadMore({String? search, String? stage}) async {
    final current = state.value;
    if (current == null || !current.hasMore) return;
    if (state.isLoading) return;

    state = await AsyncValue.guard(() async {
      final next = await _fetchPage(
        offset: current.currentOffset,
        search: search,
        stage: stage,
      );
      return current.copyWith(
        deals: [...current.deals, ...next.deals],
        totalCount: next.totalCount,
        hasMore: next.hasMore,
        currentOffset: next.currentOffset,
      );
    });
  }

  Future<DealsListData> _fetchPage({
    required int offset,
    String? search,
    String? stage,
  }) async {
    final queryParams = <String, String>{
      'limit': _pageSize.toString(),
      'offset': offset.toString(),
    };
    if (search != null && search.isNotEmpty) queryParams['name'] = search;
    if (stage != null && stage.isNotEmpty) queryParams['stage'] = stage;

    final url = Uri.parse(
      ApiConfig.opportunities,
    ).replace(queryParameters: queryParams).toString();
    final response = await _apiService.get(url);

    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load deals');
    }

    final data = response.data!;
    List<dynamic> dealsList = [];
    int dealsCount = 0;

    if (data['opportunities'] != null) {
      dealsList = data['opportunities'] as List<dynamic>? ?? [];
      dealsCount = data['opportunities_count'] as int? ?? dealsList.length;
    } else if (data['results'] != null) {
      dealsList = data['results'] as List<dynamic>? ?? [];
      dealsCount = data['count'] as int? ?? dealsList.length;
    }

    final newDeals = <Deal>[];
    for (final item in dealsList) {
      try {
        if (item is Map<String, dynamic>) {
          newDeals.add(Deal.fromJson(item));
        }
      } catch (_) {
        // Skip invalid deals
      }
    }

    return DealsListData(
      deals: newDeals,
      totalCount: dealsCount,
      hasMore: newDeals.length >= _pageSize,
      currentOffset: offset + newDeals.length,
    );
  }

  /// Fetch a single deal from the API (detail/form screens).
  Future<Deal?> getDeal(String id) async {
    try {
      final url = '${ApiConfig.opportunities}$id/';
      final response = await _apiService.get(url);

      if (response.success && response.data != null) {
        final opportunityData =
            response.data!['opportunity_obj'] as Map<String, dynamic>?;
        if (opportunityData != null) {
          return Deal.fromJson(opportunityData);
        }
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Create a new deal — list refreshes on success.
  Future<({bool success, String? error, Deal? deal})> createDeal(
    Deal deal,
  ) async {
    try {
      final response = await _apiService.post(
        ApiConfig.opportunities,
        deal.toJson(),
      );

      if (response.success && response.data != null) {
        final isError = response.data!['error'] as bool? ?? true;
        if (!isError) {
          await refresh();
          return (success: true, error: null, deal: null);
        }
      }

      String errorMsg = response.message ?? 'Failed to create deal';
      if (response.data != null && response.data!['errors'] != null) {
        final errors = response.data!['errors'] as Map<String, dynamic>;
        errorMsg = errors.values
            .map((v) => v is List ? v.join(', ') : v.toString())
            .join('; ');
      }
      return (success: false, error: errorMsg, deal: null);
    } catch (e) {
      return (
        success: false,
        error: 'Failed to create deal: ${e.toString()}',
        deal: null,
      );
    }
  }

  /// Update an existing deal — list refreshes on success.
  Future<({bool success, String? error, Deal? deal})> updateDeal(
    String id,
    Deal deal,
  ) async {
    try {
      final url = '${ApiConfig.opportunities}$id/';
      final response = await _apiService.put(url, deal.toJson());

      if (response.success && response.data != null) {
        final isError = response.data!['error'] as bool? ?? true;
        if (!isError) {
          await refresh();
          return (success: true, error: null, deal: null);
        }
      }

      String errorMsg = response.message ?? 'Failed to update deal';
      if (response.data != null && response.data!['errors'] != null) {
        final errors = response.data!['errors'] as Map<String, dynamic>;
        errorMsg = errors.values
            .map((v) => v is List ? v.join(', ') : v.toString())
            .join('; ');
      }
      return (success: false, error: errorMsg, deal: null);
    } catch (e) {
      return (
        success: false,
        error: 'Failed to update deal: ${e.toString()}',
        deal: null,
      );
    }
  }

  /// Quick stage change — optimistic local update for snappy UX.
  Future<({bool success, String? error})> updateDealStage(
    String id,
    DealStage stage,
  ) async {
    try {
      final url = '${ApiConfig.opportunities}$id/';
      final response = await _apiService.patch(url, {
        'stage': stage.value,
        'probability': stage.defaultProbability,
      });

      if (response.success && response.data != null) {
        final isError = response.data!['error'] as bool? ?? true;
        if (!isError) {
          final current = state.value;
          if (current != null) {
            final updatedDeals = current.deals.map((d) {
              if (d.id == id) {
                return d.copyWith(
                  stage: stage,
                  probability: stage.defaultProbability,
                  updatedAt: DateTime.now(),
                );
              }
              return d;
            }).toList();
            state = AsyncValue.data(current.copyWith(deals: updatedDeals));
          }
          return (success: true, error: null);
        }
      }

      return (
        success: false,
        error: response.message ?? 'Failed to update stage',
      );
    } catch (e) {
      return (success: false, error: 'Failed to update stage: ${e.toString()}');
    }
  }

  /// Delete a deal — local state mutation (no full refresh).
  Future<({bool success, String? error})> deleteDeal(String id) async {
    try {
      final url = '${ApiConfig.opportunities}$id/';
      final response = await _apiService.delete(url);

      if (response.success) {
        final current = state.value;
        if (current != null) {
          state = AsyncValue.data(
            current.copyWith(
              deals: current.deals.where((d) => d.id != id).toList(),
              totalCount: current.totalCount - 1,
            ),
          );
        }
        return (success: true, error: null);
      }

      return (
        success: false,
        error: response.message ?? 'Failed to delete deal',
      );
    } catch (e) {
      return (success: false, error: 'Failed to delete deal: ${e.toString()}');
    }
  }
}

final dealsProvider = AsyncNotifierProvider<DealsNotifier, DealsListData>(
  DealsNotifier.new,
);

/// Convenience providers — read from the AsyncValue so screen code stays the
/// same shape as before the riverpod 3 migration.
final dealsListProvider = Provider<List<Deal>>((ref) {
  return ref.watch(dealsProvider).value?.deals ?? const [];
});

final dealsLoadingProvider = Provider<bool>((ref) {
  return ref.watch(dealsProvider).isLoading;
});

final dealsErrorProvider = Provider<String?>((ref) {
  return ref.watch(dealsProvider).error?.toString();
});

/// Grouped deals by stage — derived.
final dealsByStageProvider = Provider<Map<DealStage, List<Deal>>>((ref) {
  final deals = ref.watch(dealsListProvider);
  final Map<DealStage, List<Deal>> grouped = {};
  for (final stage in DealStage.values) {
    grouped[stage] = deals.where((deal) => deal.stage == stage).toList();
  }
  return grouped;
});

/// Pipeline value (active deals only).
final pipelineValueProvider = Provider<double>((ref) {
  final deals = ref.watch(dealsListProvider);
  return deals
      .where((d) => !d.stage.isClosed)
      .fold<double>(0, (sum, deal) => sum + deal.value);
});

/// Active deals count.
final activeDealsCountProvider = Provider<int>((ref) {
  final deals = ref.watch(dealsListProvider);
  return deals.where((d) => !d.stage.isClosed).length;
});
