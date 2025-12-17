import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/deal.dart';
import '../services/api_service.dart';

/// Deals list state
class DealsState {
  final List<Deal> deals;
  final bool isLoading;
  final String? error;
  final int totalCount;
  final bool hasMore;
  final int currentOffset;

  const DealsState({
    this.deals = const [],
    this.isLoading = false,
    this.error,
    this.totalCount = 0,
    this.hasMore = true,
    this.currentOffset = 0,
  });

  const DealsState.initial()
      : deals = const [],
        isLoading = false,
        error = null,
        totalCount = 0,
        hasMore = true,
        currentOffset = 0;

  DealsState copyWith({
    List<Deal>? deals,
    bool? isLoading,
    String? error,
    int? totalCount,
    bool? hasMore,
    int? currentOffset,
    bool clearError = false,
  }) {
    return DealsState(
      deals: deals ?? this.deals,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      totalCount: totalCount ?? this.totalCount,
      hasMore: hasMore ?? this.hasMore,
      currentOffset: currentOffset ?? this.currentOffset,
    );
  }
}

/// Deals notifier for managing deals state
class DealsNotifier extends StateNotifier<DealsState> {
  DealsNotifier() : super(const DealsState.initial());

  final ApiService _apiService = ApiService();
  static const int _pageSize = 20;

  /// Fetch deals from API
  Future<void> fetchDeals({
    String? search,
    String? stage,
    bool refresh = false,
  }) async {
    if (state.isLoading) return;

    if (refresh) {
      state = state.copyWith(
        currentOffset: 0,
        hasMore: true,
        clearError: true,
      );
    }

    debugPrint('DealsNotifier: Fetching deals (offset: ${state.currentOffset})...');
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      // Build query parameters
      final queryParams = <String, String>{
        'limit': _pageSize.toString(),
        'offset': state.currentOffset.toString(),
      };

      if (search != null && search.isNotEmpty) {
        queryParams['name'] = search;
      }
      if (stage != null && stage.isNotEmpty) {
        queryParams['stage'] = stage;
      }

      final url = Uri.parse(ApiConfig.opportunities).replace(queryParameters: queryParams).toString();
      final response = await _apiService.get(url);

      if (response.success && response.data != null) {
        final data = response.data!;

        debugPrint('DealsNotifier: API response keys: ${data.keys.toList()}');
        debugPrint('DealsNotifier: Full response data: $data');

        // Parse deals - handle different response formats
        List<dynamic> dealsList = [];
        int dealsCount = 0;

        if (data['opportunities'] != null) {
          dealsList = data['opportunities'] as List<dynamic>? ?? [];
          dealsCount = data['opportunities_count'] as int? ?? dealsList.length;
          debugPrint('DealsNotifier: Found opportunities key with ${dealsList.length} items');
        } else if (data['results'] != null) {
          // Handle paginated response format
          dealsList = data['results'] as List<dynamic>? ?? [];
          dealsCount = data['count'] as int? ?? dealsList.length;
          debugPrint('DealsNotifier: Found results key with ${dealsList.length} items');
        } else {
          debugPrint('DealsNotifier: No opportunities or results key found!');
          // Try to find any list in the response
          for (final key in data.keys) {
            if (data[key] is List) {
              debugPrint('DealsNotifier: Found list at key "$key" with ${(data[key] as List).length} items');
            }
          }
        }

        debugPrint('DealsNotifier: Found ${dealsList.length} deals in response');

        final newDeals = <Deal>[];
        for (int i = 0; i < dealsList.length; i++) {
          final item = dealsList[i];
          try {
            if (item is Map<String, dynamic>) {
              debugPrint('DealsNotifier: Parsing deal $i: name=${item['name']}, stage=${item['stage']}');
              final deal = Deal.fromJson(item);
              debugPrint('DealsNotifier: Successfully parsed deal: ${deal.title} (stage: ${deal.stage})');
              newDeals.add(deal);
            } else {
              debugPrint('DealsNotifier: Skipping non-map item at index $i: ${item.runtimeType}');
            }
          } catch (e, stack) {
            debugPrint('DealsNotifier: Error parsing deal at index $i: $e');
            debugPrint('DealsNotifier: Stack trace: $stack');
            debugPrint('DealsNotifier: Deal data: $item');
          }
        }

        // Update state
        final updatedDeals = refresh ? newDeals : [...state.deals, ...newDeals];

        state = state.copyWith(
          deals: updatedDeals,
          isLoading: false,
          totalCount: dealsCount,
          hasMore: newDeals.length >= _pageSize,
          currentOffset: state.currentOffset + newDeals.length,
        );

        debugPrint('DealsNotifier: Loaded ${newDeals.length} deals (total: ${updatedDeals.length})');
      } else {
        state = state.copyWith(
          isLoading: false,
          error: response.message ?? 'Failed to load deals',
        );
        debugPrint('DealsNotifier: API error - ${response.message}');
      }
    } catch (e) {
      debugPrint('DealsNotifier: Exception - $e');
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load deals: ${e.toString()}',
      );
    }
  }

  /// Refresh deals (reset and fetch first page)
  Future<void> refresh() async {
    state = const DealsState.initial();
    await fetchDeals(refresh: true);
  }

  /// Load more deals
  Future<void> loadMore() async {
    if (!state.hasMore || state.isLoading) return;
    await fetchDeals();
  }

  /// Clear deals data
  void clear() {
    state = const DealsState.initial();
  }
}

/// Deals provider
final dealsProvider = StateNotifierProvider<DealsNotifier, DealsState>((ref) {
  return DealsNotifier();
});

/// Convenience providers
final dealsListProvider = Provider<List<Deal>>((ref) {
  return ref.watch(dealsProvider).deals;
});

final dealsLoadingProvider = Provider<bool>((ref) {
  return ref.watch(dealsProvider).isLoading;
});

final dealsErrorProvider = Provider<String?>((ref) {
  return ref.watch(dealsProvider).error;
});

/// Grouped deals by stage providers
final dealsByStageProvider = Provider<Map<DealStage, List<Deal>>>((ref) {
  final deals = ref.watch(dealsListProvider);
  final Map<DealStage, List<Deal>> grouped = {};

  for (final stage in DealStage.values) {
    grouped[stage] = deals.where((deal) => deal.stage == stage).toList();
  }

  return grouped;
});

/// Pipeline value (active deals only)
final pipelineValueProvider = Provider<double>((ref) {
  final deals = ref.watch(dealsListProvider);
  return deals
      .where((d) => !d.stage.isClosed)
      .fold<double>(0, (sum, deal) => sum + deal.value);
});

/// Active deals count
final activeDealsCountProvider = Provider<int>((ref) {
  final deals = ref.watch(dealsListProvider);
  return deals.where((d) => !d.stage.isClosed).length;
});
