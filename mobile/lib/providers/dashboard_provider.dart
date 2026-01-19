import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/dashboard_data.dart';
import '../services/api_service.dart';

/// Dashboard state
class DashboardState {
  final DashboardData? data;
  final bool isLoading;
  final String? error;
  final DateTime? lastUpdated;

  const DashboardState({
    this.data,
    this.isLoading = false,
    this.error,
    this.lastUpdated,
  });

  const DashboardState.initial()
      : data = null,
        isLoading = false,
        error = null,
        lastUpdated = null;

  DashboardState copyWith({
    DashboardData? data,
    bool? isLoading,
    String? error,
    DateTime? lastUpdated,
    bool clearError = false,
  }) {
    return DashboardState(
      data: data ?? this.data,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      lastUpdated: lastUpdated ?? this.lastUpdated,
    );
  }
}

/// Dashboard notifier for managing dashboard state
class DashboardNotifier extends StateNotifier<DashboardState> {
  DashboardNotifier() : super(const DashboardState.initial());

  final ApiService _apiService = ApiService();

  /// Fetch dashboard data from API
  Future<void> fetchDashboard({bool forceRefresh = false}) async {
    // Skip if already loading
    if (state.isLoading) return;

    // Skip if we have recent data (less than 1 minute old) and not forcing refresh
    if (!forceRefresh && state.data != null && state.lastUpdated != null) {
      final age = DateTime.now().difference(state.lastUpdated!);
      if (age.inMinutes < 1) {
        debugPrint('DashboardNotifier: Using cached data (${age.inSeconds}s old)');
        return;
      }
    }

    debugPrint('DashboardNotifier: Fetching dashboard data...');
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _apiService.get(ApiConfig.dashboard);

      if (response.success && response.data != null) {
        final dashboardData = DashboardData.fromJson(response.data!);
        state = state.copyWith(
          data: dashboardData,
          isLoading: false,
          lastUpdated: DateTime.now(),
        );
        debugPrint('DashboardNotifier: Dashboard data loaded successfully');
        debugPrint('  - Leads: ${dashboardData.leadsCount}');
        debugPrint('  - Opportunities: ${dashboardData.opportunitiesCount}');
        debugPrint('  - Pipeline stages: ${dashboardData.pipelineByStage.length}');
        debugPrint('  - Tasks: ${dashboardData.tasks.length}');
      } else {
        state = state.copyWith(
          isLoading: false,
          error: response.message ?? 'Failed to load dashboard data',
        );
        debugPrint('DashboardNotifier: API error - ${response.message}');
      }
    } catch (e) {
      debugPrint('DashboardNotifier: Exception - $e');
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load dashboard: ${e.toString()}',
      );
    }
  }

  /// Refresh dashboard data
  Future<void> refresh() async {
    await fetchDashboard(forceRefresh: true);
  }

  /// Clear dashboard data (e.g., on logout)
  void clear() {
    state = const DashboardState.initial();
  }
}

/// Dashboard provider
final dashboardProvider =
    StateNotifierProvider<DashboardNotifier, DashboardState>((ref) {
  return DashboardNotifier();
});

/// Convenience providers for specific dashboard data
final dashboardDataProvider = Provider<DashboardData?>((ref) {
  return ref.watch(dashboardProvider).data;
});

final dashboardLoadingProvider = Provider<bool>((ref) {
  return ref.watch(dashboardProvider).isLoading;
});

final dashboardErrorProvider = Provider<String?>((ref) {
  return ref.watch(dashboardProvider).error;
});
