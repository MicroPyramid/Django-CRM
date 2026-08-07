import 'package:flutter/material.dart';

import 'lead.dart' show Priority;

/// A kanban board, its lanes, and the cards on them.
///
/// A board card is **not** a `Task`. They are separate tables with separate
/// endpoints: a card lives in a column, carries an `order` within it, and has
/// no status, no owner and no reminder. Nothing here appears on the tasks list
/// and nothing there appears on a board.
///
/// The one trap is the priority vocabulary. A card's priority goes on the wire
/// lowercase (`high`), a task's capitalised (`High`), and the two models share
/// the `Priority` enum for display. `wireValue` below is the only place that
/// conversion happens; sending a task's spelling is a 400.

/// The priority string a board card expects. `Priority.label` is the human
/// spelling and also the tasks API's, so it cannot be sent as-is.
String boardPriorityValue(Priority priority) => priority.label.toLowerCase();

/// One board, as `/api/boards/` lists them.
class BoardSummary {
  const BoardSummary({
    required this.id,
    required this.name,
    this.description = '',
    this.taskCount = 0,
    this.myRole,
  });

  final String id;
  final String name;
  final String description;
  final int taskCount;

  /// `owner`, `admin`, `member`, or null. Derived by the server from the
  /// request, never sent by the client.
  final String? myRole;

  /// Whether to *offer* the add-lane control. `BoardColumnListCreateView`
  /// refuses a plain member, so showing them the button would be showing them
  /// a 403. The refusal is the rule; this only keeps the UI honest about it.
  bool get canManageColumns => myRole == 'owner' || myRole == 'admin';

  factory BoardSummary.fromJson(Map<String, dynamic> json) {
    return BoardSummary(
      id: (json['id'] ?? '').toString(),
      name: (json['name'] as String?) ?? 'Untitled board',
      description: (json['description'] as String?) ?? '',
      taskCount: json['task_count'] as int? ?? 0,
      myRole: json['my_role'] as String?,
    );
  }
}

/// One lane, with the cards the columns endpoint nests inside it.
class BoardLane {
  const BoardLane({
    required this.id,
    required this.name,
    required this.order,
    this.color,
    this.limit,
    this.cards = const [],
  });

  final String id;
  final String name;
  final int order;

  /// Hex string from the server (`#EF4444`), or null when it is unusable.
  final String? color;

  /// The lane's WIP limit. Advisory: no endpoint enforces it, so the screen
  /// shows when a lane is over its own limit and never blocks a move.
  final int? limit;

  final List<BoardCard> cards;

  bool get isOverLimit => limit != null && cards.length > limit!;

  Color get swatch {
    final raw = (color ?? '').replaceFirst('#', '');
    if (raw.length != 6) return const Color(0xFF6B7280);
    final value = int.tryParse(raw, radix: 16);
    return value == null ? const Color(0xFF6B7280) : Color(0xFF000000 | value);
  }

  factory BoardLane.fromJson(Map<String, dynamic> json) {
    final id = (json['id'] ?? '').toString();
    final rawCards = json['tasks'];
    final cards = rawCards is List
        ? rawCards
              .whereType<Map<String, dynamic>>()
              .map((c) => BoardCard.fromJson(c, id))
              .toList()
        : <BoardCard>[];
    cards.sort((a, b) => a.order.compareTo(b.order));
    return BoardLane(
      id: id,
      name: (json['name'] as String?) ?? '',
      order: json['order'] as int? ?? 0,
      color: json['color'] as String?,
      limit: json['limit'] as int?,
      cards: cards,
    );
  }
}

/// One card. `laneId` is carried down from the lane that nested it rather than
/// read from the card's own `column`, so a card can always name the lane it is
/// rendered in even if the two ever disagree.
class BoardCard {
  const BoardCard({
    required this.id,
    required this.laneId,
    required this.title,
    required this.order,
    required this.priority,
    this.description = '',
    this.dueDate,
    this.isOverdue = false,
    this.isCompleted = false,
    this.accountName,
    this.assignees = const [],
  });

  final String id;
  final String laneId;
  final String title;
  final int order;
  final Priority priority;
  final String description;
  final DateTime? dueDate;

  /// Both come from the server, which measures them against its own clock.
  /// Recomputing "overdue" on the phone would answer with the device's.
  final bool isOverdue;
  final bool isCompleted;

  final String? accountName;
  final List<String> assignees;

  factory BoardCard.fromJson(Map<String, dynamic> json, String laneId) {
    final account = json['account'];
    final rawDue = json['due_date'] as String?;
    final rawAssignees = json['assigned_to'];
    return BoardCard(
      id: (json['id'] ?? '').toString(),
      laneId: laneId,
      title: (json['title'] as String?) ?? '',
      order: json['order'] as int? ?? 0,
      priority: Priority.fromString(json['priority'] as String?),
      description: (json['description'] as String?) ?? '',
      dueDate: rawDue == null ? null : DateTime.tryParse(rawDue),
      isOverdue: json['is_overdue'] as bool? ?? false,
      isCompleted: json['is_completed'] as bool? ?? false,
      accountName: account is Map<String, dynamic>
          ? (account['name'] as String?)
          : null,
      assignees: rawAssignees is List
          ? rawAssignees
                .whereType<Map<String, dynamic>>()
                .map(_assigneeName)
                .toList()
          : const [],
    );
  }

  /// An assignee is a full profile object with the display name nested under
  /// `user_details`. Someone invited but not yet signed in has no name, so the
  /// email is all there is to call them.
  static String _assigneeName(Map<String, dynamic> profile) {
    final details =
        (profile['user_details'] as Map<String, dynamic>?) ?? const {};
    final name = (details['name'] as String?)?.trim() ?? '';
    if (name.isNotEmpty) return name;
    final email = (details['email'] as String?)?.trim() ?? '';
    return email.isNotEmpty ? email : 'Unknown';
  }
}
