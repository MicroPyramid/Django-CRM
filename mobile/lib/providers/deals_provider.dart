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

        // Parse deals - handle different response formats
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
          } catch (e) {
            // Skip invalid deals
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
      } else {
        state = state.copyWith(
          isLoading: false,
          error: response.message ?? 'Failed to load deals',
        );
      }
    } catch (e) {
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

  /// Get a single deal by ID
  Future<Deal?> getDeal(String id) async {
    try {
      final url = '${ApiConfig.opportunities}$id/';
      final response = await _apiService.get(url);

      if (response.success && response.data != null) {
        // API returns opportunity wrapped in 'opportunity_obj' key
        final opportunityData = response.data!['opportunity_obj'] as Map<String, dynamic>?;
        if (opportunityData != null) {
          return Deal.fromJson(opportunityData);
        }
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Create a new deal
  Future<({bool success, String? error, Deal? deal})> createDeal(Deal deal) async {
    try {
      final response = await _apiService.post(
        ApiConfig.opportunities,
        deal.toJson(),
      );

      if (response.success && response.data != null) {
        // API returns {"error": false, "message": "..."} on success, not the deal object
        final isError = response.data!['error'] as bool? ?? true;
        if (!isError) {
          // Refresh the deals list to get the new deal
          await fetchDeals(refresh: true);
          return (success: true, error: null, deal: null);
        }
      }

      // Parse error message
      String errorMsg = response.message ?? 'Failed to create deal';
      if (response.data != null && response.data!['errors'] != null) {
        final errors = response.data!['errors'] as Map<String, dynamic>;
        errorMsg = errors.values.map((v) => v is List ? v.join(', ') : v.toString()).join('; ');
      }
      return (success: false, error: errorMsg, deal: null);
    } catch (e) {
      return (success: false, error: 'Failed to create deal: ${e.toString()}', deal: null);
    }
  }

  /// Update an existing deal
  Future<({bool success, String? error, Deal? deal})> updateDeal(String id, Deal deal) async {
    try {
      final url = '${ApiConfig.opportunities}$id/';
      final response = await _apiService.put(
        url,
        deal.toJson(),
      );

      if (response.success && response.data != null) {
        // API returns {"error": false, "message": "..."} on success, not the deal object
        final isError = response.data!['error'] as bool? ?? true;
        if (!isError) {
          // Refresh the deals list to get updated data
          await fetchDeals(refresh: true);
          return (success: true, error: null, deal: null);
        }
      }

      // Parse error message
      String errorMsg = response.message ?? 'Failed to update deal';
      if (response.data != null && response.data!['errors'] != null) {
        final errors = response.data!['errors'] as Map<String, dynamic>;
        errorMsg = errors.values.map((v) => v is List ? v.join(', ') : v.toString()).join('; ');
      }
      return (success: false, error: errorMsg, deal: null);
    } catch (e) {
      return (success: false, error: 'Failed to update deal: ${e.toString()}', deal: null);
    }
  }

  /// Update deal stage (quick action)
  Future<({bool success, String? error})> updateDealStage(String id, DealStage stage) async {
    try {
      final url = '${ApiConfig.opportunities}$id/';
      final response = await _apiService.patch(
        url,
        {
          'stage': stage.value,
          'probability': stage.defaultProbability,
        },
      );

      if (response.success && response.data != null) {
        // API returns {"error": false, "message": "..."} on success
        final isError = response.data!['error'] as bool? ?? true;
        if (!isError) {
          // Update the deal stage locally without full refresh for better UX
          final updatedDeals = state.deals.map((d) {
            if (d.id == id) {
              return d.copyWith(
                stage: stage,
                probability: stage.defaultProbability,
                updatedAt: DateTime.now(),
              );
            }
            return d;
          }).toList();
          state = state.copyWith(deals: updatedDeals);
          return (success: true, error: null);
        }
      }

      return (success: false, error: response.message ?? 'Failed to update stage');
    } catch (e) {
      return (success: false, error: 'Failed to update stage: ${e.toString()}');
    }
  }

  /// Delete a deal
  Future<({bool success, String? error})> deleteDeal(String id) async {
    try {
      final url = '${ApiConfig.opportunities}$id/';
      final response = await _apiService.delete(url);

      if (response.success) {
        // Remove from the list
        final updatedDeals = state.deals.where((d) => d.id != id).toList();
        state = state.copyWith(
          deals: updatedDeals,
          totalCount: state.totalCount - 1,
        );
        return (success: true, error: null);
      }

      return (success: false, error: response.message ?? 'Failed to delete deal');
    } catch (e) {
      return (success: false, error: 'Failed to delete deal: ${e.toString()}');
    }
  }

  /// Get deal from current state by ID
  Deal? getDealFromState(String id) {
    try {
      return state.deals.firstWhere((d) => d.id == id);
    } catch (_) {
      return null;
    }
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
