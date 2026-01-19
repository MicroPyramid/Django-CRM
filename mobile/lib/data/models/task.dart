import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import 'lead.dart';

/// Related entity type for polymorphic relations
enum RelatedEntityType {
  lead('lead', 'Lead', Icons.person_outline),
  account('account', 'Account', Icons.business),
  opportunity('opportunity', 'Opportunity', Icons.trending_up),
  case_('case', 'Case', Icons.support_agent),
  contact('contact', 'Contact', Icons.contacts);

  final String value;
  final String label;
  final IconData icon;

  const RelatedEntityType(this.value, this.label, this.icon);

  static RelatedEntityType fromString(String? value) {
    if (value == null) return RelatedEntityType.lead;
    return RelatedEntityType.values.firstWhere(
      (t) => t.value == value.toLowerCase(),
      orElse: () => RelatedEntityType.lead,
    );
  }
}

/// Related entity reference
class RelatedEntity {
  final String id;
  final RelatedEntityType type;
  final String title;

  const RelatedEntity({
    required this.id,
    required this.type,
    required this.title,
  });

  String get displayLabel => '${type.label}: $title';

  factory RelatedEntity.fromJson(Map<String, dynamic> json, RelatedEntityType type) {
    String title = '';
    if (type == RelatedEntityType.lead) {
      final firstName = json['first_name'] as String? ?? '';
      final lastName = json['last_name'] as String? ?? '';
      title = '$firstName $lastName'.trim();
      if (title.isEmpty) title = json['email'] as String? ?? 'Unknown';
    } else {
      title = json['name'] as String? ?? 'Unknown';
    }

    return RelatedEntity(
      id: json['id']?.toString() ?? '',
      type: type,
      title: title,
    );
  }
}

/// Task status enumeration matching backend STATUS_CHOICES
enum TaskStatus {
  newTask('New', 'New', AppColors.primary500),
  inProgress('In Progress', 'In Progress', AppColors.warning500),
  completed('Completed', 'Completed', AppColors.success500);

  final String value;
  final String label;
  final Color color;

  const TaskStatus(this.value, this.label, this.color);

  static TaskStatus fromString(String? value) {
    if (value == null) return TaskStatus.newTask;
    return TaskStatus.values.firstWhere(
      (s) => s.value.toLowerCase() == value.toLowerCase(),
      orElse: () => TaskStatus.newTask,
    );
  }
}

/// Task model for BottleCRM
class Task {
  final String id;
  final String title;
  final String? description;
  final DateTime? dueDate;
  final TaskStatus status;
  final Priority priority;
  final List<Map<String, dynamic>>? assignedTo;
  final RelatedEntity? relatedTo;
  final List<String> tags;
  final DateTime createdAt;
  final DateTime? updatedAt;

  const Task({
    required this.id,
    required this.title,
    this.description,
    this.dueDate,
    required this.status,
    required this.priority,
    this.assignedTo,
    this.relatedTo,
    this.tags = const [],
    required this.createdAt,
    this.updatedAt,
  });

  /// Check if task is completed
  bool get completed => status == TaskStatus.completed;

  /// Check if task is overdue
  bool get isOverdue {
    if (completed || dueDate == null) return false;
    return dueDate!.isBefore(DateTime.now());
  }

  /// Check if task is due today
  bool get isDueToday {
    if (dueDate == null) return false;
    final now = DateTime.now();
    return dueDate!.year == now.year &&
        dueDate!.month == now.month &&
        dueDate!.day == now.day;
  }

  /// Check if task is due within 2 hours
  bool get isDueSoon {
    if (completed || dueDate == null) return false;
    final now = DateTime.now();
    final diff = dueDate!.difference(now);
    return diff.inHours >= 0 && diff.inHours <= 2;
  }

  /// Check if task is upcoming (future, not today)
  bool get isUpcoming {
    if (completed || dueDate == null) return false;
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final taskDate = DateTime(dueDate!.year, dueDate!.month, dueDate!.day);
    return taskDate.isAfter(today);
  }

  /// Get task due status category
  TaskDueStatus get dueStatus {
    if (completed) return TaskDueStatus.completed;
    if (isOverdue) return TaskDueStatus.overdue;
    if (isDueToday) return TaskDueStatus.today;
    if (dueDate == null) return TaskDueStatus.noDueDate;
    return TaskDueStatus.upcoming;
  }

  /// Days until due (negative if overdue)
  int? get daysUntilDue {
    if (dueDate == null) return null;
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final taskDate = DateTime(dueDate!.year, dueDate!.month, dueDate!.day);
    return taskDate.difference(today).inDays;
  }

  /// Get assigned user name (first one if multiple)
  String get assignedToName {
    if (assignedTo == null || assignedTo!.isEmpty) return 'Unassigned';
    final first = assignedTo!.first;
    final email = first['user__email'] as String? ?? '';
    return email.split('@').first;
  }

  /// Factory constructor to create Task from JSON
  factory Task.fromJson(Map<String, dynamic> json) {
    // Parse tags
    List<String> parsedTags = [];
    if (json['tags'] != null) {
      final tagsList = json['tags'] as List<dynamic>;
      parsedTags = tagsList.map((t) {
        if (t is Map<String, dynamic>) {
          return t['name'] as String? ?? '';
        }
        return t.toString();
      }).where((t) => t.isNotEmpty).toList();
    }

    // Parse assigned_to
    List<Map<String, dynamic>>? parsedAssignedTo;
    if (json['assigned_to'] != null) {
      final assignedList = json['assigned_to'] as List<dynamic>;
      parsedAssignedTo = assignedList
          .map((a) => a is Map<String, dynamic> ? a : <String, dynamic>{})
          .toList();
    }

    // Parse related entity (account, lead, opportunity, case)
    // Handle both full objects and ID references
    RelatedEntity? relatedEntity;
    if (json['account'] != null && json['account'] is Map<String, dynamic>) {
      relatedEntity = RelatedEntity.fromJson(
        json['account'] as Map<String, dynamic>,
        RelatedEntityType.account,
      );
    } else if (json['lead'] != null && json['lead'] is Map<String, dynamic>) {
      relatedEntity = RelatedEntity.fromJson(
        json['lead'] as Map<String, dynamic>,
        RelatedEntityType.lead,
      );
    } else if (json['opportunity'] != null && json['opportunity'] is Map<String, dynamic>) {
      relatedEntity = RelatedEntity.fromJson(
        json['opportunity'] as Map<String, dynamic>,
        RelatedEntityType.opportunity,
      );
    } else if (json['case'] != null && json['case'] is Map<String, dynamic>) {
      relatedEntity = RelatedEntity.fromJson(
        json['case'] as Map<String, dynamic>,
        RelatedEntityType.case_,
      );
    }

    return Task(
      id: json['id']?.toString() ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String?,
      dueDate: json['due_date'] != null
          ? DateTime.tryParse(json['due_date'] as String)
          : null,
      status: TaskStatus.fromString(json['status'] as String?),
      priority: Priority.fromString(json['priority'] as String?),
      assignedTo: parsedAssignedTo,
      relatedTo: relatedEntity,
      tags: parsedTags,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'] as String)
          : null,
    );
  }

  /// Convert Task to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'due_date': dueDate?.toIso8601String().split('T').first,
      'status': status.value,
      'priority': priority.label,
    };
  }

  Task copyWith({
    String? id,
    String? title,
    String? description,
    DateTime? dueDate,
    TaskStatus? status,
    Priority? priority,
    List<Map<String, dynamic>>? assignedTo,
    RelatedEntity? relatedTo,
    List<String>? tags,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Task(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      dueDate: dueDate ?? this.dueDate,
      status: status ?? this.status,
      priority: priority ?? this.priority,
      assignedTo: assignedTo ?? this.assignedTo,
      relatedTo: relatedTo ?? this.relatedTo,
      tags: tags ?? this.tags,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Task && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Task due status for grouping
enum TaskDueStatus {
  overdue,
  today,
  upcoming,
  noDueDate,
  completed;

  String get label {
    switch (this) {
      case TaskDueStatus.overdue:
        return 'Overdue';
      case TaskDueStatus.today:
        return 'Today';
      case TaskDueStatus.upcoming:
        return 'Upcoming';
      case TaskDueStatus.noDueDate:
        return 'No Due Date';
      case TaskDueStatus.completed:
        return 'Completed';
    }
  }
}
