import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/ticket.dart';
import '../data/models/comment.dart';
import '../services/api_service.dart';

/// Paginated tickets snapshot — wrapped by AsyncValue.
class TicketsListData {
  final List<Ticket> tickets;
  final int totalCount;
  final bool hasMore;
  final int currentOffset;

  const TicketsListData({
    this.tickets = const [],
    this.totalCount = 0,
    this.hasMore = true,
    this.currentOffset = 0,
  });

  TicketsListData copyWith({
    List<Ticket>? tickets,
    int? totalCount,
    bool? hasMore,
    int? currentOffset,
  }) {
    return TicketsListData(
      tickets: tickets ?? this.tickets,
      totalCount: totalCount ?? this.totalCount,
      hasMore: hasMore ?? this.hasMore,
      currentOffset: currentOffset ?? this.currentOffset,
    );
  }
}

class TicketsNotifier extends AsyncNotifier<TicketsListData> {
  final ApiService _apiService = ApiService();
  static const int _pageSize = 20;

  @override
  Future<TicketsListData> build() => _fetchPage(offset: 0);

  Future<void> refresh({
    String? search,
    String? status,
    String? priority,
    String? assignedTo,
  }) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => _fetchPage(
        offset: 0,
        search: search,
        status: status,
        priority: priority,
        assignedTo: assignedTo,
      ),
    );
  }

  Future<void> loadMore({
    String? search,
    String? status,
    String? priority,
    String? assignedTo,
  }) async {
    final current = state.value;
    if (current == null || !current.hasMore) return;
    if (state.isLoading) return;

    state = await AsyncValue.guard(() async {
      final next = await _fetchPage(
        offset: current.currentOffset,
        search: search,
        status: status,
        priority: priority,
        assignedTo: assignedTo,
      );
      return current.copyWith(
        tickets: [...current.tickets, ...next.tickets],
        totalCount: next.totalCount,
        hasMore: next.hasMore,
        currentOffset: next.currentOffset,
      );
    });
  }

  Future<TicketsListData> _fetchPage({
    required int offset,
    String? search,
    String? status,
    String? priority,
    String? assignedTo,
  }) async {
    final queryParams = <String, String>{
      'limit': _pageSize.toString(),
      'offset': offset.toString(),
    };
    if (search != null && search.isNotEmpty) queryParams['search'] = search;
    if (status != null && status.isNotEmpty) queryParams['status'] = status;
    if (priority != null && priority.isNotEmpty) {
      queryParams['priority'] = priority;
    }
    if (assignedTo != null && assignedTo.isNotEmpty) {
      queryParams['assigned_to'] = assignedTo;
    }

    final url = Uri.parse(
      ApiConfig.tickets,
    ).replace(queryParameters: queryParams).toString();
    final response = await _apiService.get(url);

    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load tickets');
    }

    final data = response.data!;
    final ticketsList = data['cases'] as List<dynamic>? ?? [];
    final newTickets = ticketsList
        .map((j) => Ticket.fromJson(j as Map<String, dynamic>))
        .toList();
    final totalCount = data['cases_count'] as int? ?? newTickets.length;

    return TicketsListData(
      tickets: newTickets,
      totalCount: totalCount,
      hasMore: newTickets.length >= _pageSize,
      currentOffset: offset + newTickets.length,
    );
  }

  /// Fetch a single ticket (just the Ticket object).
  Future<Ticket?> getTicketById(String id) async {
    final detail = await getTicketDetail(id);
    return detail?.ticketObj;
  }

  /// Fetch the full ticket detail (incl. comments + activities + permissions).
  Future<TicketDetailResult?> getTicketDetail(String id) async {
    try {
      final response = await _apiService.get(ApiConfig.ticketDetail(id));
      if (!response.success || response.data == null) return null;

      final ticketData = response.data!['cases_obj'] as Map<String, dynamic>?;
      if (ticketData == null) return null;
      var ticketObj = Ticket.fromJson(ticketData);

      // Public + internal comments are sent in two separate arrays. We tag
      // each so the UI can render an "Internal" badge without an extra
      // round-trip — `Comment` itself doesn't carry that flag yet.
      final List<_TaggedComment> tagged = [];
      for (final c in (response.data!['comments'] as List<dynamic>? ?? [])) {
        tagged.add(
          _TaggedComment(
            comment: Comment.fromJson(c as Map<String, dynamic>),
            isInternal: false,
          ),
        );
      }
      for (final c
          in (response.data!['internal_notes'] as List<dynamic>? ?? [])) {
        tagged.add(
          _TaggedComment(
            comment: Comment.fromJson(c as Map<String, dynamic>),
            isInternal: true,
          ),
        );
      }
      tagged.sort(
        (a, b) => b.comment.commentedOn.compareTo(a.comment.commentedOn),
      );
      if (tagged.isNotEmpty) {
        ticketObj = ticketObj.copyWith(
          comments: tagged.map((t) => t.comment).toList(),
        );
      }

      final activities = (response.data!['activities'] as List<dynamic>? ?? [])
          .map((a) => a as Map<String, dynamic>)
          .toList();

      return TicketDetailResult(
        ticketObj: ticketObj,
        activities: activities,
        commentPermission:
            response.data!['comment_permission'] as bool? ?? false,
        internalCommentIds: tagged
            .where((t) => t.isInternal)
            .map((t) => t.comment.id)
            .toSet(),
      );
    } catch (_) {
      return null;
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> createTicket(
    Map<String, dynamic> ticketData,
  ) async {
    try {
      final response = await _apiService.post(ApiConfig.tickets, ticketData);
      if (response.success) await refresh();
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> updateTicket(
    String id,
    Map<String, dynamic> ticketData,
  ) async {
    try {
      final response = await _apiService.put(
        ApiConfig.ticketDetail(id),
        ticketData,
      );
      if (response.success) await refresh();
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> addComment(
    String ticketId,
    String comment, {
    bool isInternal = false,
  }) async {
    try {
      final response = await _apiService.post(
        ApiConfig.ticketDetail(ticketId),
        {'comment': comment, 'is_internal': isInternal},
      );
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> deleteTicket(String id) async {
    try {
      final response = await _apiService.delete(ApiConfig.ticketDetail(id));
      if (response.success) {
        final current = state.value;
        if (current != null) {
          state = AsyncValue.data(
            current.copyWith(
              tickets: current.tickets.where((t) => t.id != id).toList(),
              totalCount: current.totalCount > 0 ? current.totalCount - 1 : 0,
            ),
          );
        }
      }
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }
}

final ticketsProvider =
    AsyncNotifierProvider<TicketsNotifier, TicketsListData>(
      TicketsNotifier.new,
    );

/// Convenience providers — read from the AsyncValue.
final ticketsListProvider = Provider<List<Ticket>>((ref) {
  return ref.watch(ticketsProvider).value?.tickets ?? const [];
});

final ticketsLoadingProvider = Provider<bool>((ref) {
  return ref.watch(ticketsProvider).isLoading;
});

final ticketsErrorProvider = Provider<String?>((ref) {
  return ref.watch(ticketsProvider).error?.toString();
});

/// Bundled detail-fetch result. The mobile detail screen needs more than
/// just the Ticket object — also activities and the per-user permission to
/// add comments.
class TicketDetailResult {
  final Ticket ticketObj;
  final List<Map<String, dynamic>> activities;
  final bool commentPermission;
  final Set<String> internalCommentIds;

  const TicketDetailResult({
    required this.ticketObj,
    required this.activities,
    required this.commentPermission,
    required this.internalCommentIds,
  });
}

class _TaggedComment {
  final Comment comment;
  final bool isInternal;
  const _TaggedComment({required this.comment, required this.isInternal});
}
