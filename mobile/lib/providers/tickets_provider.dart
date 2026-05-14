import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/ticket.dart';
import '../data/models/comment.dart';
import '../data/models/email_message.dart';
import '../data/models/solution.dart';
import '../data/models/time_entry.dart';
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
  Future<TicketsListData> build() =>
      _fetchPage(offset: 0, filters: const TicketListFilters());

  Future<void> refresh({TicketListFilters filters = const TicketListFilters()}) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetchPage(offset: 0, filters: filters));
  }

  Future<void> loadMore({
    TicketListFilters filters = const TicketListFilters(),
  }) async {
    final current = state.value;
    if (current == null || !current.hasMore) return;
    if (state.isLoading) return;

    state = await AsyncValue.guard(() async {
      final next =
          await _fetchPage(offset: current.currentOffset, filters: filters);
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
    required TicketListFilters filters,
  }) async {
    // Watching-only flips us to a different endpoint that returns the
    // current profile's watched cases. It doesn't paginate the same way, so
    // we ask for one page and treat the whole response as the result.
    if (filters.watchingOnly) {
      return _fetchWatching(filters);
    }

    final queryParams = <String, String>{
      'limit': _pageSize.toString(),
      'offset': offset.toString(),
    };
    if (filters.search.isNotEmpty) queryParams['search'] = filters.search;
    if (filters.status != null) queryParams['status'] = filters.status!;
    if (filters.priority != null) queryParams['priority'] = filters.priority!;
    if (filters.accountId != null) {
      queryParams['account'] = filters.accountId!;
    }
    // Multi-value params must be repeated. http's Uri only takes the last
    // value when keys collide in a Map, so we encode by hand.
    final extra = <String>[];
    for (final id in filters.assigneeIds) {
      extra.add('assigned_to=$id');
    }
    for (final id in filters.tagIds) {
      extra.add('tags=$id');
    }

    final base = Uri.parse(ApiConfig.tickets)
        .replace(queryParameters: queryParams)
        .toString();
    final url = extra.isEmpty ? base : '$base&${extra.join('&')}';

    final response = await _apiService.get(url);

    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load tickets');
    }

    final data = response.data!;
    final ticketsList = data['cases'] as List<dynamic>? ?? [];
    var newTickets = ticketsList
        .map((j) => Ticket.fromJson(j as Map<String, dynamic>))
        .toList();
    final totalCount = data['cases_count'] as int? ?? newTickets.length;

    // Date range is enforced client-side — the list endpoint doesn't expose
    // a created_at filter. Acceptable because the user already paginates.
    newTickets = _applyDateRange(newTickets, filters);

    return TicketsListData(
      tickets: newTickets,
      totalCount: totalCount,
      hasMore: newTickets.length >= _pageSize,
      currentOffset: offset + ticketsList.length,
    );
  }

  Future<TicketsListData> _fetchWatching(TicketListFilters filters) async {
    final response = await _apiService.get(ApiConfig.ticketsWatching);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load watched tickets');
    }
    final list = response.data!['cases'] as List<dynamic>? ?? [];
    var tickets = list
        .map((j) => Ticket.fromJson(j as Map<String, dynamic>))
        .toList();

    // Apply the remaining filters client-side since /watching/ doesn't take
    // query params yet.
    if (filters.search.isNotEmpty) {
      final q = filters.search.toLowerCase();
      tickets = tickets
          .where((t) =>
              t.name.toLowerCase().contains(q) ||
              (t.accountName?.toLowerCase().contains(q) ?? false))
          .toList();
    }
    if (filters.status != null) {
      tickets =
          tickets.where((t) => t.status.value == filters.status).toList();
    }
    if (filters.priority != null) {
      tickets =
          tickets.where((t) => t.priority.value == filters.priority).toList();
    }
    if (filters.accountId != null) {
      tickets =
          tickets.where((t) => t.accountId == filters.accountId).toList();
    }
    if (filters.assigneeIds.isNotEmpty) {
      tickets = tickets
          .where((t) => t.assignedToIds
              .any((aid) => filters.assigneeIds.contains(aid)))
          .toList();
    }
    if (filters.tagIds.isNotEmpty) {
      tickets = tickets
          .where((t) =>
              t.tagIds.any((tid) => filters.tagIds.contains(tid)))
          .toList();
    }
    tickets = _applyDateRange(tickets, filters);

    return TicketsListData(
      tickets: tickets,
      totalCount: tickets.length,
      hasMore: false,
      currentOffset: tickets.length,
    );
  }

  List<Ticket> _applyDateRange(
    List<Ticket> tickets,
    TicketListFilters filters,
  ) {
    if (filters.createdAfter == null && filters.createdBefore == null) {
      return tickets;
    }
    return tickets.where((t) {
      if (filters.createdAfter != null &&
          t.createdAt.isBefore(filters.createdAfter!)) {
        return false;
      }
      if (filters.createdBefore != null &&
          t.createdAt.isAfter(filters.createdBefore!)) {
        return false;
      }
      return true;
    }).toList();
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

      final emails = (response.data!['email_messages'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(EmailMessage.fromJson)
          .toList();

      final mergedFrom = (response.data!['merged_from_cases']
                  as List<dynamic>? ??
              [])
          .whereType<Map<String, dynamic>>()
          .map((m) => MergedFromSummary(
                id: m['id']?.toString() ?? '',
                name: m['name']?.toString() ?? '',
                mergedAt: m['merged_at'] != null
                    ? DateTime.tryParse(m['merged_at'].toString())
                    : null,
              ))
          .toList();

      final linkedSolutions =
          (response.data!['solutions'] as List<dynamic>? ?? [])
              .whereType<Map<String, dynamic>>()
              .map(Solution.fromJson)
              .toList();

      return TicketDetailResult(
        ticketObj: ticketObj,
        activities: activities,
        emails: emails,
        mergedFromCases: mergedFrom,
        linkedSolutions: linkedSolutions,
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

  /// Fetch watcher list for a ticket.
  /// Returns ({watcherCount, isCurrentUserWatching, watchers}) or null on error.
  Future<TicketWatchers?> getWatchers(String id) async {
    try {
      final response = await _apiService.get(ApiConfig.ticketWatchers(id));
      if (!response.success || response.data == null) return null;
      final data = response.data!;
      final list = (data['watchers'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .toList();
      return TicketWatchers(
        watchers: list,
        count: list.length,
        isCurrentUserWatching:
            data['is_current_user_watching'] as bool? ?? false,
      );
    } catch (_) {
      return null;
    }
  }

  /// Fetch all time entries for a ticket (most recent first).
  Future<List<TimeEntry>> fetchTimeEntries(String id) async {
    try {
      // Backend returns a bare array, not an envelope.
      final response = await _apiService.getList(ApiConfig.ticketTimeEntries(id));
      if (!response.success || response.data == null) return const [];
      return response.data!
          .whereType<Map<String, dynamic>>()
          .map(TimeEntry.fromJson)
          .toList();
    } catch (_) {
      return const [];
    }
  }

  /// Fetch ticket time summary (totals + per-profile).
  Future<TimeSummary?> fetchTimeSummary(String id) async {
    try {
      final response = await _apiService.get(ApiConfig.ticketTimeSummary(id));
      if (!response.success || response.data == null) return null;
      return TimeSummary.fromJson(response.data!);
    } catch (_) {
      return null;
    }
  }

  /// Start a running timer on a ticket.
  Future<ApiResponse<Map<String, dynamic>>> startTimer(
    String id, {
    bool billable = false,
    String description = '',
  }) async {
    try {
      return await _apiService.post(
        ApiConfig.ticketTimerStart(id),
        {'billable': billable, 'description': description},
      );
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Stop a running timer by entry id.
  Future<ApiResponse<Map<String, dynamic>>> stopTimer(String entryId) async {
    try {
      return await _apiService.post(
        ApiConfig.timeEntryStop(entryId),
        const {},
      );
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Add a manual completed time entry.
  Future<ApiResponse<Map<String, dynamic>>> addManualTimeEntry(
    String id, {
    required DateTime startedAt,
    required DateTime endedAt,
    bool billable = false,
    String description = '',
  }) async {
    try {
      return await _apiService.post(ApiConfig.ticketTimeEntries(id), {
        'started_at': startedAt.toUtc().toIso8601String(),
        'ended_at': endedAt.toUtc().toIso8601String(),
        'billable': billable,
        'description': description,
      });
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Fetch parent/child tree (rooted at the closest visible ancestor).
  Future<TicketTreeNode?> fetchTree(String id) async {
    try {
      final response = await _apiService.get(ApiConfig.ticketTree(id));
      if (!response.success || response.data == null) return null;
      final root = response.data!['root'] as Map<String, dynamic>?;
      final focusId = response.data!['focus_id']?.toString();
      if (root == null) return null;
      return TicketTreeNode.fromJson(root, focusId: focusId);
    } catch (_) {
      return null;
    }
  }

  /// Link to a parent (pass null to detach).
  Future<ApiResponse<Map<String, dynamic>>> linkParent(
    String id,
    String? parentId,
  ) async {
    try {
      return await _apiService.post(
        ApiConfig.ticketLinkParent(id),
        {'parent_id': parentId},
      );
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Close this ticket; optionally cascade-close descendants.
  Future<ApiResponse<Map<String, dynamic>>> closeWithChildren(
    String id, {
    bool cascade = true,
  }) async {
    try {
      return await _apiService.post(
        ApiConfig.ticketCloseWithChildren(id),
        {'cascade': cascade},
      );
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Merge `sourceId` as a duplicate INTO `intoId`. Source becomes inactive
  /// and its comments/attachments/emails move to the target.
  Future<ApiResponse<Map<String, dynamic>>> mergeInto(
    String sourceId,
    String intoId,
  ) async {
    try {
      return await _apiService.post(
        ApiConfig.ticketMerge(sourceId, intoId),
        const {},
      );
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Reverse a prior merge; called on the source ticket id.
  Future<ApiResponse<Map<String, dynamic>>> unmerge(String sourceId) async {
    try {
      return await _apiService.post(
        ApiConfig.ticketUnmerge(sourceId),
        const {},
      );
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Toggle the current user's watch state on a ticket.
  Future<bool> setWatching(String id, bool watch) async {
    try {
      final response = watch
          ? await _apiService.post(ApiConfig.ticketWatch(id), const {})
          : await _apiService.delete(ApiConfig.ticketWatch(id));
      return response.success;
    } catch (_) {
      return false;
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
  final List<EmailMessage> emails;
  final List<MergedFromSummary> mergedFromCases;
  final List<Solution> linkedSolutions;
  final bool commentPermission;
  final Set<String> internalCommentIds;

  const TicketDetailResult({
    required this.ticketObj,
    required this.activities,
    this.emails = const [],
    this.mergedFromCases = const [],
    this.linkedSolutions = const [],
    required this.commentPermission,
    required this.internalCommentIds,
  });
}

/// Recursive tree node returned by `/api/cases/{id}/tree/`.
class TicketTreeNode {
  final String id;
  final String name;
  final String? status;
  final String? priority;
  final bool isProblem;
  final bool isActive;
  final bool truncated;
  final List<TicketTreeNode> children;
  final String? focusId;

  const TicketTreeNode({
    required this.id,
    required this.name,
    this.status,
    this.priority,
    this.isProblem = false,
    this.isActive = true,
    this.truncated = false,
    this.children = const [],
    this.focusId,
  });

  bool get isFocused => focusId != null && focusId == id;

  factory TicketTreeNode.fromJson(
    Map<String, dynamic> json, {
    String? focusId,
  }) {
    return TicketTreeNode(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      status: json['status'] as String?,
      priority: json['priority'] as String?,
      isProblem: json['is_problem'] as bool? ?? false,
      isActive: json['is_active'] as bool? ?? true,
      truncated: json['truncated'] as bool? ?? false,
      children: ((json['children'] as List<dynamic>?) ?? const [])
          .whereType<Map<String, dynamic>>()
          .map((c) => TicketTreeNode.fromJson(c, focusId: focusId))
          .toList(),
      focusId: focusId,
    );
  }
}

/// Lightweight reference to a ticket that was merged into the current one.
class MergedFromSummary {
  final String id;
  final String name;
  final DateTime? mergedAt;
  const MergedFromSummary({
    required this.id,
    required this.name,
    this.mergedAt,
  });
}

/// Bundle of filters applied to the tickets list.
///
/// Server-supported (passed as query params): status, priority, accountId,
/// assigneeIds, tagIds, search. Client-only: createdAfter/Before (the list
/// endpoint has no date filter) and watchingOnly (separate endpoint).
class TicketListFilters {
  final String search;
  final String? status;
  final String? priority;
  final String? accountId;
  final List<String> assigneeIds;
  final List<String> tagIds;
  final bool watchingOnly;
  final DateTime? createdAfter;
  final DateTime? createdBefore;

  const TicketListFilters({
    this.search = '',
    this.status,
    this.priority,
    this.accountId,
    this.assigneeIds = const [],
    this.tagIds = const [],
    this.watchingOnly = false,
    this.createdAfter,
    this.createdBefore,
  });

  bool get hasAny =>
      search.isNotEmpty ||
      status != null ||
      priority != null ||
      accountId != null ||
      assigneeIds.isNotEmpty ||
      tagIds.isNotEmpty ||
      watchingOnly ||
      createdAfter != null ||
      createdBefore != null;

  TicketListFilters copyWith({
    String? search,
    String? status,
    String? priority,
    String? accountId,
    List<String>? assigneeIds,
    List<String>? tagIds,
    bool? watchingOnly,
    DateTime? createdAfter,
    DateTime? createdBefore,
    bool clearStatus = false,
    bool clearPriority = false,
    bool clearAccountId = false,
    bool clearCreatedAfter = false,
    bool clearCreatedBefore = false,
  }) {
    return TicketListFilters(
      search: search ?? this.search,
      status: clearStatus ? null : (status ?? this.status),
      priority: clearPriority ? null : (priority ?? this.priority),
      accountId: clearAccountId ? null : (accountId ?? this.accountId),
      assigneeIds: assigneeIds ?? this.assigneeIds,
      tagIds: tagIds ?? this.tagIds,
      watchingOnly: watchingOnly ?? this.watchingOnly,
      createdAfter:
          clearCreatedAfter ? null : (createdAfter ?? this.createdAfter),
      createdBefore:
          clearCreatedBefore ? null : (createdBefore ?? this.createdBefore),
    );
  }
}

/// Watcher list response — used by the detail screen's sidebar.
class TicketWatchers {
  final List<Map<String, dynamic>> watchers;
  final int count;
  final bool isCurrentUserWatching;
  const TicketWatchers({
    required this.watchers,
    required this.count,
    required this.isCurrentUserWatching,
  });
}

class _TaggedComment {
  final Comment comment;
  final bool isInternal;
  const _TaggedComment({required this.comment, required this.isInternal});
}
