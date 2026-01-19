import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/lead.dart';
import '../data/models/comment.dart';
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

  /// Get a single lead by ID
  Future<Lead?> getLeadById(String id) async {
    try {
      final url = '${ApiConfig.leads}$id/';
      final response = await _apiService.get(url);

      if (response.success && response.data != null) {
        final leadData = response.data!['lead_obj'] as Map<String, dynamic>?;
        if (leadData != null) {
          final lead = Lead.fromJson(leadData);

          // Parse comments from separate field in response
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

  /// Create a new lead
  Future<ApiResponse<Map<String, dynamic>>> createLead(Map<String, dynamic> leadData) async {
    try {
      final response = await _apiService.post(ApiConfig.leads, leadData);
      if (response.success) {
        await refresh();
      }
      return response;
    } catch (e) {
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Update an existing lead
  Future<ApiResponse<Map<String, dynamic>>> updateLead(String id, Map<String, dynamic> leadData) async {
    try {
      final url = '${ApiConfig.leads}$id/';
      final response = await _apiService.put(url, leadData);
      if (response.success) {
        await refresh();
      }
      return response;
    } catch (e) {
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Update lead status (quick action)
  Future<ApiResponse<Map<String, dynamic>>> updateLeadStatus(String id, LeadStatus status) async {
    try {
      final url = '${ApiConfig.leads}$id/';
      final response = await _apiService.patch(url, {'status': status.value});

      if (response.success) {
        // Update local state
        final updatedLeads = state.leads.map((l) {
          if (l.id == id) {
            return l.copyWith(status: status);
          }
          return l;
        }).toList();
        state = state.copyWith(leads: updatedLeads);
      }

      return response;
    } catch (e) {
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Delete a lead
  Future<ApiResponse<Map<String, dynamic>>> deleteLead(String id) async {
    try {
      final url = '${ApiConfig.leads}$id/';
      final response = await _apiService.delete(url);
      if (response.success) {
        state = state.copyWith(
          leads: state.leads.where((l) => l.id != id).toList(),
          totalCount: state.totalCount > 0 ? state.totalCount - 1 : 0,
        );
      }
      return response;
    } catch (e) {
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Add a comment to a lead
  Future<ApiResponse<Map<String, dynamic>>> addComment(String leadId, String comment) async {
    try {
      final url = '${ApiConfig.leads}$leadId/';
      final response = await _apiService.post(url, {'comment': comment});
      return response;
    } catch (e) {
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Delete a comment from a lead
  Future<ApiResponse<Map<String, dynamic>>> deleteComment(String commentId) async {
    try {
      final url = ApiConfig.leadComment(commentId);
      final response = await _apiService.delete(url);
      return response;
    } catch (e) {
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

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
      } else {
        state = state.copyWith(
          isLoading: false,
          error: response.message ?? 'Failed to load leads',
        );
      }
    } catch (e) {
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
