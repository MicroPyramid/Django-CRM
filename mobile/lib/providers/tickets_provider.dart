import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/ticket.dart';
import '../data/models/comment.dart';
import '../services/api_service.dart';

/// Tickets list state
class TicketsState {
  final List<Ticket> tickets;
  final bool isLoading;
  final String? error;
  final int totalCount;
  final bool hasMore;
  final int currentOffset;

  const TicketsState({
    this.tickets = const [],
    this.isLoading = false,
    this.error,
    this.totalCount = 0,
    this.hasMore = true,
    this.currentOffset = 0,
  });

  const TicketsState.initial()
    : tickets = const [],
      isLoading = false,
      error = null,
      totalCount = 0,
      hasMore = true,
      currentOffset = 0;

  TicketsState copyWith({
    List<Ticket>? tickets,
    bool? isLoading,
    String? error,
    int? totalCount,
    bool? hasMore,
    int? currentOffset,
    bool clearError = false,
  }) {
    return TicketsState(
      tickets: tickets ?? this.tickets,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      totalCount: totalCount ?? this.totalCount,
      hasMore: hasMore ?? this.hasMore,
      currentOffset: currentOffset ?? this.currentOffset,
    );
  }
}

/// Tickets notifier mirroring the leads notifier
class TicketsNotifier extends StateNotifier<TicketsState> {
  TicketsNotifier() : super(const TicketsState.initial());

  final ApiService _apiService = ApiService();
  static const int _pageSize = 20;

  /// Get a single ticket by ID, returning the full detail (incl. comments).
  Future<Ticket?> getTicketById(String id) async {
    final detail = await getTicketDetail(id);
    return detail?.ticketObj;
  }

  /// Get the full ticket detail including activities + comment permission.
  /// Returns null if the ticket can't be loaded.
  Future<TicketDetailResult?> getTicketDetail(String id) async {
    try {
      final response = await _apiService.get(ApiConfig.ticketDetail(id));
      if (!response.success || response.data == null) return null;

      final ticketData = response.data!['cases_obj'] as Map<String, dynamic>?;
      if (ticketData == null) return null;
      var ticketObj = Ticket.fromJson(ticketData);

      // Public + internal comments are sent in two separate arrays. We tag
      // each one so the UI can render an "Internal" badge without an extra
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

  /// Create a new ticket
  Future<ApiResponse<Map<String, dynamic>>> createTicket(
    Map<String, dynamic> ticketData,
  ) async {
    try {
      final response = await _apiService.post(ApiConfig.tickets, ticketData);
      if (response.success) {
        await refresh();
      }
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Update an existing ticket
  Future<ApiResponse<Map<String, dynamic>>> updateTicket(
    String id,
    Map<String, dynamic> ticketData,
  ) async {
    try {
      final response = await _apiService.put(
        ApiConfig.ticketDetail(id),
        ticketData,
      );
      if (response.success) {
        await refresh();
      }
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Add a comment (or internal note) to a ticket.
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

  /// Delete a ticket
  Future<ApiResponse<Map<String, dynamic>>> deleteTicket(String id) async {
    try {
      final response = await _apiService.delete(ApiConfig.ticketDetail(id));
      if (response.success) {
        state = state.copyWith(
          tickets: state.tickets.where((c) => c.id != id).toList(),
          totalCount: state.totalCount > 0 ? state.totalCount - 1 : 0,
        );
      }
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Fetch the tickets list with optional filters.
  Future<void> fetchTickets({
    String? search,
    String? status,
    String? priority,
    String? assignedTo,
    bool refresh = false,
  }) async {
    if (state.isLoading) return;

    if (refresh) {
      state = state.copyWith(currentOffset: 0, hasMore: true, clearError: true);
    }

    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final queryParams = <String, String>{
        'limit': _pageSize.toString(),
        'offset': state.currentOffset.toString(),
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

      if (response.success && response.data != null) {
        final data = response.data!;
        final ticketsList = data['cases'] as List<dynamic>? ?? [];
        final newTickets = ticketsList
            .map((j) => Ticket.fromJson(j as Map<String, dynamic>))
            .toList();

        final updatedTickets = refresh
            ? newTickets
            : [...state.tickets, ...newTickets];
        final totalCount = data['cases_count'] as int? ?? updatedTickets.length;

        state = state.copyWith(
          tickets: updatedTickets,
          isLoading: false,
          totalCount: totalCount,
          hasMore: newTickets.length >= _pageSize,
          currentOffset: state.currentOffset + newTickets.length,
        );
      } else {
        state = state.copyWith(
          isLoading: false,
          error: response.message ?? 'Failed to load tickets',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load tickets: ${e.toString()}',
      );
    }
  }

  Future<void> refresh() async {
    state = const TicketsState.initial();
    await fetchTickets(refresh: true);
  }

  Future<void> loadMore() async {
    if (!state.hasMore || state.isLoading) return;
    await fetchTickets();
  }

  void clear() {
    state = const TicketsState.initial();
  }
}

final ticketsProvider = StateNotifierProvider<TicketsNotifier, TicketsState>((
  ref,
) {
  return TicketsNotifier();
});

final ticketsListProvider = Provider<List<Ticket>>((ref) {
  return ref.watch(ticketsProvider).tickets;
});

final ticketsLoadingProvider = Provider<bool>((ref) {
  return ref.watch(ticketsProvider).isLoading;
});

final ticketsErrorProvider = Provider<String?>((ref) {
  return ref.watch(ticketsProvider).error;
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
