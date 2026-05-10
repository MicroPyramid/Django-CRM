import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/dashboard_data.dart';
import '../services/api_service.dart';

/// Async notifier owning the dashboard fetch.
///
/// `build()` runs on first watch and seeds the AsyncValue with the result of
/// the initial fetch — no separate `fetchDashboard()` call from the screen.
/// `refresh()` is the pull-to-refresh / retry entrypoint.
class DashboardNotifier extends AsyncNotifier<DashboardData> {
  final ApiService _apiService = ApiService();

  @override
  Future<DashboardData> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<DashboardData> _fetch() async {
    debugPrint('DashboardNotifier: Fetching dashboard data...');
    final response = await _apiService.get(ApiConfig.dashboard);
    debugPrint('DashboardNotifier: Response status: ${response.statusCode}');
    if (!response.success || response.data == null) {
      debugPrint('DashboardNotifier: API error - ${response.message}');
      throw Exception(response.message ?? 'Failed to load dashboard data');
    }
    final dashboardData = DashboardData.fromJson(response.data!);
    debugPrint(
      'DashboardNotifier: loaded leads=${dashboardData.leadsCount} '
      'opps=${dashboardData.opportunitiesCount} '
      'stages=${dashboardData.pipelineByStage.length} '
      'tasks=${dashboardData.tasks.length}',
    );
    return dashboardData;
  }
}

final dashboardProvider =
    AsyncNotifierProvider<DashboardNotifier, DashboardData>(
      DashboardNotifier.new,
    );
