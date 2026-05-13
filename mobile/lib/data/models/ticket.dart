import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import 'comment.dart';

/// Ticket status enumeration matching backend STATUS_CHOICE
enum TicketStatus {
  newStatus('New', 'New', AppColors.primary500),
  assigned('Assigned', 'Assigned', AppColors.primary400),
  pending('Pending', 'Pending', AppColors.warning500),
  closed('Closed', 'Closed', AppColors.success600),
  rejected('Rejected', 'Rejected', AppColors.danger500),
  duplicate('Duplicate', 'Duplicate', AppColors.gray500);

  final String value;
  final String label;
  final Color color;

  const TicketStatus(this.value, this.label, this.color);

  String get displayName => label;

  static TicketStatus fromString(String? value) {
    if (value == null) return TicketStatus.newStatus;
    return TicketStatus.values.firstWhere(
      (s) => s.value == value,
      orElse: () => TicketStatus.newStatus,
    );
  }
}

/// Ticket priority enumeration matching backend PRIORITY_CHOICE
enum TicketPriority {
  low('Low', 'Low', AppColors.success500),
  normal('Normal', 'Normal', AppColors.primary400),
  high('High', 'High', AppColors.warning500),
  urgent('Urgent', 'Urgent', AppColors.danger500);

  final String value;
  final String label;
  final Color color;

  const TicketPriority(this.value, this.label, this.color);

  String get displayName => label;

  static TicketPriority fromString(String? value) {
    if (value == null) return TicketPriority.normal;
    return TicketPriority.values.firstWhere(
      (p) => p.value == value,
      orElse: () => TicketPriority.normal,
    );
  }
}

/// Ticket type enumeration matching backend CASE_TYPE
enum TicketType {
  question('Question', 'Question', Icons.help_outline),
  incident('Incident', 'Incident', Icons.error_outline),
  problem('Problem', 'Problem', Icons.report_problem_outlined);

  final String value;
  final String label;
  final IconData icon;

  const TicketType(this.value, this.label, this.icon);

  String get displayName => label;

  static TicketType fromString(String? value) {
    if (value == null) return TicketType.question;
    return TicketType.values.firstWhere(
      (t) => t.value == value,
      orElse: () => TicketType.question,
    );
  }
}

/// Ticket model for BottleCRM
class Ticket {
  final String id;
  final String name;
  final TicketStatus status;
  final TicketPriority priority;
  final TicketType ticketType;
  final String? description;
  final String? accountId;
  final String? accountName;
  final List<Map<String, dynamic>> assignedTo;
  final List<String> assignedToIds;
  final List<String> tags;
  final DateTime createdAt;
  final DateTime? closedOn;
  final int? slaFirstResponseHours;
  final int? slaResolutionHours;
  final DateTime? firstResponseAt;
  final DateTime? resolvedAt;
  final bool isFirstResponseSlaBreachedFromApi;
  final bool isResolutionSlaBreachedFromApi;
  final List<Comment> comments;

  const Ticket({
    required this.id,
    required this.name,
    required this.status,
    required this.priority,
    required this.ticketType,
    this.description,
    this.accountId,
    this.accountName,
    this.assignedTo = const [],
    this.assignedToIds = const [],
    this.tags = const [],
    required this.createdAt,
    this.closedOn,
    this.slaFirstResponseHours,
    this.slaResolutionHours,
    this.firstResponseAt,
    this.resolvedAt,
    this.isFirstResponseSlaBreachedFromApi = false,
    this.isResolutionSlaBreachedFromApi = false,
    this.comments = const [],
  });

  /// First-response SLA breach.
  ///
  /// Mirrors `Case.is_sla_first_response_breached` on the backend:
  /// breached when no `first_response_at` AND `now > created_at + sla_first_response_hours`.
  /// Both web and mobile compute from the same `created_at + sla_first_response_hours`
  /// so the badge stays consistent across clients.
  bool get isFirstResponseSlaBreached {
    if (isFirstResponseSlaBreachedFromApi) return true;
    if (firstResponseAt != null) return false;
    if (slaFirstResponseHours == null) return false;
    final deadline = createdAt.add(Duration(hours: slaFirstResponseHours!));
    return DateTime.now().isAfter(deadline);
  }

  /// Assigned-to display name (first assignee or "Unassigned").
  String get assignedToName {
    if (assignedTo.isEmpty) return 'Unassigned';
    final first = assignedTo.first;
    final email =
        (first['user_details']?['email'] as String?) ??
        (first['email'] as String?) ??
        '';
    if (email.isEmpty) return 'Unassigned';
    return email.split('@').first;
  }

  factory Ticket.fromJson(Map<String, dynamic> json) {
    String? accountId;
    String? accountName;
    final accountJson = json['account'];
    if (accountJson is Map<String, dynamic>) {
      accountId = accountJson['id']?.toString();
      accountName = accountJson['name'] as String?;
    } else if (accountJson != null) {
      accountId = accountJson.toString();
    }

    List<Map<String, dynamic>> parsedAssignedTo = [];
    List<String> parsedAssignedToIds = [];
    if (json['assigned_to'] is List) {
      for (final a in (json['assigned_to'] as List)) {
        if (a is Map<String, dynamic>) {
          parsedAssignedTo.add(a);
          final id = a['id']?.toString() ?? '';
          if (id.isNotEmpty) parsedAssignedToIds.add(id);
        }
      }
    }

    final List<String> parsedTags = [];
    if (json['tags'] is List) {
      for (final t in (json['tags'] as List)) {
        if (t is Map<String, dynamic>) {
          final n = t['name'] as String?;
          if (n != null && n.isNotEmpty) parsedTags.add(n);
        } else if (t is String) {
          parsedTags.add(t);
        }
      }
    }

    return Ticket(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      status: TicketStatus.fromString(json['status'] as String?),
      priority: TicketPriority.fromString(json['priority'] as String?),
      ticketType: TicketType.fromString(json['case_type'] as String?),
      description: json['description'] as String?,
      accountId: accountId,
      accountName: accountName,
      assignedTo: parsedAssignedTo,
      assignedToIds: parsedAssignedToIds,
      tags: parsedTags,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
      closedOn: json['closed_on'] != null
          ? DateTime.tryParse(json['closed_on'] as String)
          : null,
      slaFirstResponseHours: json['sla_first_response_hours'] as int?,
      slaResolutionHours: json['sla_resolution_hours'] as int?,
      firstResponseAt: json['first_response_at'] != null
          ? DateTime.tryParse(json['first_response_at'] as String)
          : null,
      resolvedAt: json['resolved_at'] != null
          ? DateTime.tryParse(json['resolved_at'] as String)
          : null,
      isFirstResponseSlaBreachedFromApi:
          json['is_sla_first_response_breached'] as bool? ?? false,
      isResolutionSlaBreachedFromApi:
          json['is_sla_resolution_breached'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'status': status.value,
      'priority': priority.value,
      'case_type': ticketType.value,
      'description': description,
      'account': accountId,
    };
  }

  Ticket copyWith({
    String? id,
    String? name,
    TicketStatus? status,
    TicketPriority? priority,
    TicketType? ticketType,
    String? description,
    String? accountId,
    String? accountName,
    List<Map<String, dynamic>>? assignedTo,
    List<String>? assignedToIds,
    List<String>? tags,
    DateTime? createdAt,
    DateTime? closedOn,
    int? slaFirstResponseHours,
    int? slaResolutionHours,
    DateTime? firstResponseAt,
    DateTime? resolvedAt,
    bool? isFirstResponseSlaBreachedFromApi,
    bool? isResolutionSlaBreachedFromApi,
    List<Comment>? comments,
  }) {
    return Ticket(
      id: id ?? this.id,
      name: name ?? this.name,
      status: status ?? this.status,
      priority: priority ?? this.priority,
      ticketType: ticketType ?? this.ticketType,
      description: description ?? this.description,
      accountId: accountId ?? this.accountId,
      accountName: accountName ?? this.accountName,
      assignedTo: assignedTo ?? this.assignedTo,
      assignedToIds: assignedToIds ?? this.assignedToIds,
      tags: tags ?? this.tags,
      createdAt: createdAt ?? this.createdAt,
      closedOn: closedOn ?? this.closedOn,
      slaFirstResponseHours:
          slaFirstResponseHours ?? this.slaFirstResponseHours,
      slaResolutionHours: slaResolutionHours ?? this.slaResolutionHours,
      firstResponseAt: firstResponseAt ?? this.firstResponseAt,
      resolvedAt: resolvedAt ?? this.resolvedAt,
      isFirstResponseSlaBreachedFromApi:
          isFirstResponseSlaBreachedFromApi ??
          this.isFirstResponseSlaBreachedFromApi,
      isResolutionSlaBreachedFromApi:
          isResolutionSlaBreachedFromApi ?? this.isResolutionSlaBreachedFromApi,
      comments: comments ?? this.comments,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Ticket && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}
