import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/models/board.dart';
import '../services/api_service.dart';

export '../services/api_service.dart' show ApiResponse;

/// One board, read in the two calls it takes: the list (for the picker and to
/// resolve which board is open) and that board's lanes with their cards
/// nested.
class BoardData {
  const BoardData({this.boards = const [], this.active, this.lanes = const []});

  final List<BoardSummary> boards;

  /// The board on screen. Null only when the org has none.
  final BoardSummary? active;

  final List<BoardLane> lanes;

  bool get hasNoBoards => boards.isEmpty;

  /// Whether to offer the add-lane control. The server is the boundary; this
  /// is the courtesy that stops a member tapping into a 403.
  bool get canManageLanes => active?.canManageColumns ?? false;

  int get cardCount =>
      lanes.fold(0, (total, lane) => total + lane.cards.length);

  BoardLane? laneById(String id) {
    for (final lane in lanes) {
      if (lane.id == id) return lane;
    }
    return null;
  }
}

/// The board screen's state and its four writes.
///
/// Every write refreshes on success and leaves the board alone on failure, so
/// a refused move never shows a card in a lane the server did not put it in.
/// The screen surfaces the server's own message: it is the one that knows a
/// lane name is taken or that a member may not add a lane.
class BoardNotifier extends AsyncNotifier<BoardData> {
  final ApiService _apiService = ApiService();

  /// Which board the picker chose. Kept across refreshes; a board that has
  /// since gone falls back to the most recent one rather than an error.
  String? _selectedId;

  @override
  Future<BoardData> build() => _fetch();

  Future<BoardData> _fetch() async {
    final listResponse = await _apiService.get(
      ApiConfig.boards,
      queryParams: const {'archived': 'false'},
    );
    if (!listResponse.success || listResponse.data == null) {
      throw Exception(listResponse.message ?? 'Could not load your boards.');
    }
    final rows = listResponse.data!['results'];
    final boards = rows is List
        ? rows
              .whereType<Map<String, dynamic>>()
              .map(BoardSummary.fromJson)
              .toList()
        : <BoardSummary>[];
    if (boards.isEmpty) return const BoardData();

    final active = boards.firstWhere(
      (b) => b.id == _selectedId,
      orElse: () => boards.first,
    );
    // Keep the selection pointing at what is actually on screen, so a stale id
    // does not silently reselect itself on the next refresh.
    _selectedId = active.id;

    final lanesResponse = await _apiService.getList(
      ApiConfig.boardLanes(active.id),
    );
    if (!lanesResponse.success || lanesResponse.data == null) {
      throw Exception(lanesResponse.message ?? 'Could not load that board.');
    }
    final lanes =
        lanesResponse.data!
            .whereType<Map<String, dynamic>>()
            .map(BoardLane.fromJson)
            .toList()
          ..sort((a, b) => a.order.compareTo(b.order));

    return BoardData(boards: boards, active: active, lanes: lanes);
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  /// Open another board. A no-op when it is already the open one, so tapping
  /// the current board in the picker does not throw the screen back to a
  /// spinner.
  Future<void> select(String boardId) async {
    if (boardId == _selectedId) return;
    _selectedId = boardId;
    await refresh();
  }

  /// Create a board. The server derives org, owner and creator from the JWT,
  /// enrols the caller as owner, and seeds the To Do / In Progress / Done
  /// lanes, so the whole write surface is a name and an optional description
  /// and the new board is usable immediately.
  Future<ApiResponse<Map<String, dynamic>>> createBoard({
    required String name,
  }) async {
    final response = await _apiService.post(ApiConfig.boards, {'name': name});
    if (response.success) {
      // Open what was just created rather than whatever sorts first.
      final id = response.data?['id']?.toString();
      if (id != null && id.isNotEmpty) _selectedId = id;
      await refresh();
    }
    return response;
  }

  /// Add a lane to the open board. Owner and admin only, refused server-side
  /// for anyone else and for a name the board already uses.
  Future<ApiResponse<Map<String, dynamic>>> createLane({
    required String name,
  }) async {
    final board = state.value?.active;
    if (board == null) {
      return const ApiResponse(
        success: false,
        message: 'Open a board first.',
        statusCode: 0,
      );
    }
    // Past the last lane, not at `lanes.length`: lane order is not a dense
    // sequence (a seeded board starts at 0 and a hand-made one at 1), so
    // counting would put the new lane on top of an existing one.
    final orders = state.value!.lanes.map((l) => l.order);
    final nextOrder = orders.isEmpty
        ? 0
        : orders.reduce((a, b) => a > b ? a : b) + 1;
    final response = await _apiService.post(ApiConfig.boardLanes(board.id), {
      'name': name,
      'order': nextOrder,
    });
    if (response.success) await refresh();
    return response;
  }

  /// Add a card to the end of a lane.
  ///
  /// `order` is sent explicitly. The create endpoint does not resequence, and
  /// the field defaults to 0, so leaving it out files every new card at the
  /// top of the lane tied with whatever is already there, and a tie is broken
  /// differently on each read.
  Future<ApiResponse<Map<String, dynamic>>> createCard({
    required String laneId,
    required String title,
    String? description,
    String? priority,
  }) async {
    final lane = state.value?.laneById(laneId);
    final response = await _apiService.post(ApiConfig.boardLaneCards(laneId), {
      'title': title,
      'order': lane?.cards.length ?? 0,
      if (description != null && description.isNotEmpty)
        'description': description,
      'priority': ?priority,
    });
    if (response.success) await refresh();
    return response;
  }

  /// Move a card, either into another lane or to another position in its own.
  ///
  /// `index` is the position among the lane's *other* cards, which is what the
  /// server splices at. Moving to the end of a lane means passing that lane's
  /// card count.
  Future<ApiResponse<Map<String, dynamic>>> moveCard({
    required String cardId,
    required String laneId,
    required int index,
  }) async {
    final response = await _apiService.put(ApiConfig.boardCard(cardId), {
      'column': laneId,
      'order': index,
    });
    if (response.success) await refresh();
    return response;
  }

  Future<ApiResponse<Map<String, dynamic>>> deleteCard(String cardId) async {
    final response = await _apiService.delete(ApiConfig.boardCard(cardId));
    if (response.success) await refresh();
    return response;
  }
}

final boardProvider = AsyncNotifierProvider<BoardNotifier, BoardData>(
  BoardNotifier.new,
);
