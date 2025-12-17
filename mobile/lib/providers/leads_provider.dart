import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/lead.dart';
import '../services/api_service.dart';

/// Leads list state
class LeadsState {
  final List<Lead> leads;
  final bool isLoading;
  final String? error;
  final int totalCount;
  final bool hasMore;
  final int currentOffset;

  const LeadsState({
    this.leads = const [],
    this.isLoading = false,
    this.error,
    this.totalCount = 0,
    this.hasMore = true,
    this.currentOffset = 0,
  });

  const LeadsState.initial()
      : leads = const [],
        isLoading = false,
        error = null,
        totalCount = 0,
        hasMore = true,
        currentOffset = 0;

  LeadsState copyWith({
    List<Lead>? leads,
    bool? isLoading,
    String? error,
    int? totalCount,
    bool? hasMore,
    int? currentOffset,
    bool clearError = false,
  }) {
    return LeadsState(
      leads: leads ?? this.leads,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      totalCount: totalCount ?? this.totalCount,
      hasMore: hasMore ?? this.hasMore,
      currentOffset: currentOffset ?? this.currentOffset,
    );
  }
}

/// Leads notifier for managing leads state
class LeadsNotifier extends StateNotifier<LeadsState> {
  LeadsNotifier() : super(const LeadsState.initial());

  final ApiService _apiService = ApiService();
  static const int _pageSize = 20;

  /// Fetch leads from API
  Future<void> fetchLeads({
    String? search,
    String? status,
    String? source,
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

    debugPrint('LeadsNotifier: Fetching leads (offset: ${state.currentOffset})...');
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      // Build query parameters
      final queryParams = <String, String>{
        'limit': _pageSize.toString(),
        'offset': state.currentOffset.toString(),
      };

      if (search != null && search.isNotEmpty) {
        queryParams['search'] = search;
      }
      if (status != null && status.isNotEmpty) {
        queryParams['status'] = status;
      }
      if (source != null && source.isNotEmpty) {
        queryParams['source'] = source;
      }

      final url = Uri.parse(ApiConfig.leads).replace(queryParameters: queryParams).toString();
      final response = await _apiService.get(url);

      if (response.success && response.data != null) {
        final data = response.data!;

        // Parse open leads
        final openLeadsData = data['open_leads'] as Map<String, dynamic>?;
        final openLeadsList = openLeadsData?['open_leads'] as List<dynamic>? ?? [];
        final openLeadsCount = openLeadsData?['leads_count'] as int? ?? 0;

        // Parse close leads
        final closeLeadsData = data['close_leads'] as Map<String, dynamic>?;
        final closeLeadsList = closeLeadsData?['close_leads'] as List<dynamic>? ?? [];

        // Combine all leads
        final allLeadsList = [...openLeadsList, ...closeLeadsList];
        final newLeads = allLeadsList
            .map((json) => Lead.fromJson(json as Map<String, dynamic>))
            .toList();

        // Update state
        final updatedLeads = refresh ? newLeads : [...state.leads, ...newLeads];
        final totalCount = openLeadsCount + (closeLeadsData?['leads_count'] as int? ?? 0);

        state = state.copyWith(
          leads: updatedLeads,
          isLoading: false,
          totalCount: totalCount,
          hasMore: newLeads.length >= _pageSize,
          currentOffset: state.currentOffset + newLeads.length,
        );

        debugPrint('LeadsNotifier: Loaded ${newLeads.length} leads (total: ${updatedLeads.length})');
      } else {
        state = state.copyWith(
          isLoading: false,
          error: response.message ?? 'Failed to load leads',
        );
        debugPrint('LeadsNotifier: API error - ${response.message}');
      }
    } catch (e) {
      debugPrint('LeadsNotifier: Exception - $e');
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load leads: ${e.toString()}',
      );
    }
  }

  /// Refresh leads (reset and fetch first page)
  Future<void> refresh() async {
    state = const LeadsState.initial();
    await fetchLeads(refresh: true);
  }

  /// Load more leads
  Future<void> loadMore() async {
    if (!state.hasMore || state.isLoading) return;
    await fetchLeads();
  }

  /// Clear leads data
  void clear() {
    state = const LeadsState.initial();
  }
}

/// Leads provider
final leadsProvider = StateNotifierProvider<LeadsNotifier, LeadsState>((ref) {
  return LeadsNotifier();
});

/// Convenience providers
final leadsListProvider = Provider<List<Lead>>((ref) {
  return ref.watch(leadsProvider).leads;
});

final leadsLoadingProvider = Provider<bool>((ref) {
  return ref.watch(leadsProvider).isLoading;
});

final leadsErrorProvider = Provider<String?>((ref) {
  return ref.watch(leadsProvider).error;
});
