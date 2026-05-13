import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/lead.dart';
import '../data/models/comment.dart';
import '../services/api_service.dart';

/// Paginated leads snapshot — wrapped by AsyncValue.
class LeadsListData {
  final List<Lead> leads;
  final int totalCount;
  final bool hasMore;
  final int currentOffset;

  const LeadsListData({
    this.leads = const [],
    this.totalCount = 0,
    this.hasMore = true,
    this.currentOffset = 0,
  });

  LeadsListData copyWith({
    List<Lead>? leads,
    int? totalCount,
    bool? hasMore,
    int? currentOffset,
  }) {
    return LeadsListData(
      leads: leads ?? this.leads,
      totalCount: totalCount ?? this.totalCount,
      hasMore: hasMore ?? this.hasMore,
      currentOffset: currentOffset ?? this.currentOffset,
    );
  }
}

class LeadsNotifier extends AsyncNotifier<LeadsListData> {
  final ApiService _apiService = ApiService();
  static const int _pageSize = 20;

  @override
  Future<LeadsListData> build() => _fetchPage(offset: 0);

  Future<void> refresh({String? search, String? status, String? source}) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => _fetchPage(
        offset: 0,
        search: search,
        status: status,
        source: source,
      ),
    );
  }

  Future<void> loadMore({
    String? search,
    String? status,
    String? source,
  }) async {
    final current = state.value;
    if (current == null || !current.hasMore) return;
    if (state.isLoading) return;

    state = await AsyncValue.guard(() async {
      final next = await _fetchPage(
        offset: current.currentOffset,
        search: search,
        status: status,
        source: source,
      );
      return current.copyWith(
        leads: [...current.leads, ...next.leads],
        totalCount: next.totalCount,
        hasMore: next.hasMore,
        currentOffset: next.currentOffset,
      );
    });
  }

  Future<LeadsListData> _fetchPage({
    required int offset,
    String? search,
    String? status,
    String? source,
  }) async {
    final queryParams = <String, String>{
      'limit': _pageSize.toString(),
      'offset': offset.toString(),
    };
    if (search != null && search.isNotEmpty) queryParams['search'] = search;
    if (status != null && status.isNotEmpty) queryParams['status'] = status;
    if (source != null && source.isNotEmpty) queryParams['source'] = source;

    final url = Uri.parse(
      ApiConfig.leads,
    ).replace(queryParameters: queryParams).toString();
    final response = await _apiService.get(url);

    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load leads');
    }

    final data = response.data!;

    // Backend returns open_leads + close_leads in two sub-objects.
    final openLeadsData = data['open_leads'] as Map<String, dynamic>?;
    final openLeadsList =
        openLeadsData?['open_leads'] as List<dynamic>? ?? [];
    final openLeadsCount = openLeadsData?['leads_count'] as int? ?? 0;

    final closeLeadsData = data['close_leads'] as Map<String, dynamic>?;
    final closeLeadsList =
        closeLeadsData?['close_leads'] as List<dynamic>? ?? [];

    final allLeadsList = [...openLeadsList, ...closeLeadsList];
    final newLeads = allLeadsList
        .map((json) => Lead.fromJson(json as Map<String, dynamic>))
        .toList();

    final totalCount =
        openLeadsCount + (closeLeadsData?['leads_count'] as int? ?? 0);

    return LeadsListData(
      leads: newLeads,
      totalCount: totalCount,
      hasMore: newLeads.length >= _pageSize,
      currentOffset: offset + newLeads.length,
    );
  }

  /// Fetch a single lead from the API (with comments).
  Future<Lead?> getLeadById(String id) async {
    try {
      final url = '${ApiConfig.leads}$id/';
      final response = await _apiService.get(url);

      if (response.success && response.data != null) {
        final leadData = response.data!['lead_obj'] as Map<String, dynamic>?;
        if (leadData != null) {
          final lead = Lead.fromJson(leadData);

          final commentsData = response.data!['comments'] as List<dynamic>?;
          if (commentsData != null && commentsData.isNotEmpty) {
            final comments = commentsData
                .map((c) => Comment.fromJson(c as Map<String, dynamic>))
                .toList();
            return lead.copyWith(comments: comments);
          }
          return lead;
        }
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> createLead(
    Map<String, dynamic> leadData,
  ) async {
    try {
      final response = await _apiService.post(ApiConfig.leads, leadData);
      if (response.success) await refresh();
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> updateLead(
    String id,
    Map<String, dynamic> leadData,
  ) async {
    try {
      final url = '${ApiConfig.leads}$id/';
      final response = await _apiService.put(url, leadData);
      if (response.success) await refresh();
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Quick status change — optimistic local update.
  Future<ApiResponse<Map<String, dynamic>>> updateLeadStatus(
    String id,
    LeadStatus status,
  ) async {
    try {
      final url = '${ApiConfig.leads}$id/';
      final response = await _apiService.patch(url, {'status': status.value});

      if (response.success) {
        final current = state.value;
        if (current != null) {
          final updatedLeads = current.leads.map((l) {
            if (l.id == id) return l.copyWith(status: status);
            return l;
          }).toList();
          state = AsyncValue.data(current.copyWith(leads: updatedLeads));
        }
      }
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> deleteLead(String id) async {
    try {
      final url = '${ApiConfig.leads}$id/';
      final response = await _apiService.delete(url);
      if (response.success) {
        final current = state.value;
        if (current != null) {
          state = AsyncValue.data(
            current.copyWith(
              leads: current.leads.where((l) => l.id != id).toList(),
              totalCount: current.totalCount > 0
                  ? current.totalCount - 1
                  : 0,
            ),
          );
        }
      }
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> addComment(
    String leadId,
    String comment,
  ) async {
    try {
      final url = '${ApiConfig.leads}$leadId/';
      return await _apiService.post(url, {'comment': comment});
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> deleteComment(
    String commentId,
  ) async {
    try {
      final url = ApiConfig.leadComment(commentId);
      return await _apiService.delete(url);
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }
}

final leadsProvider = AsyncNotifierProvider<LeadsNotifier, LeadsListData>(
  LeadsNotifier.new,
);

/// Convenience providers — read from the AsyncValue.
final leadsListProvider = Provider<List<Lead>>((ref) {
  return ref.watch(leadsProvider).value?.leads ?? const [];
});

final leadsLoadingProvider = Provider<bool>((ref) {
  return ref.watch(leadsProvider).isLoading;
});

final leadsErrorProvider = Provider<String?>((ref) {
  return ref.watch(leadsProvider).error?.toString();
});
