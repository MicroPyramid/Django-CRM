import 'lead.dart';

/// Related entity type for polymorphic relations
enum RelatedEntityType {
  lead,
  deal,
  contact;

  String get label {
    switch (this) {
      case RelatedEntityType.lead:
        return 'Lead';
      case RelatedEntityType.deal:
        return 'Deal';
      case RelatedEntityType.contact:
        return 'Contact';
    }
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
}

/// Task model for SalesPro CRM
class Task {
  final String id;
  final String title;
  final String? description;
  final DateTime dueDate;
  final bool completed;
  final Priority priority;
  final String assignedTo;
  final RelatedEntity? relatedTo;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Task({
    required this.id,
    required this.title,
    this.description,
    required this.dueDate,
    this.completed = false,
    required this.priority,
    required this.assignedTo,
    this.relatedTo,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Check if task is overdue
  bool get isOverdue {
    if (completed) return false;
    return dueDate.isBefore(DateTime.now());
  }

  /// Check if task is due today
  bool get isDueToday {
    final now = DateTime.now();
    return dueDate.year == now.year &&
        dueDate.month == now.month &&
        dueDate.day == now.day;
  }

  /// Check if task is due within 2 hours
  bool get isDueSoon {
    if (completed) return false;
    final now = DateTime.now();
    final diff = dueDate.difference(now);
    return diff.inHours >= 0 && diff.inHours <= 2;
  }

  /// Check if task is upcoming (future, not today)
  bool get isUpcoming {
    if (completed) return false;
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final taskDate = DateTime(dueDate.year, dueDate.month, dueDate.day);
    return taskDate.isAfter(today);
  }

  /// Get task due status category
  TaskDueStatus get dueStatus {
    if (completed) return TaskDueStatus.completed;
    if (isOverdue) return TaskDueStatus.overdue;
    if (isDueToday) return TaskDueStatus.today;
    return TaskDueStatus.upcoming;
  }

  /// Days until due (negative if overdue)
  int get daysUntilDue {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final taskDate = DateTime(dueDate.year, dueDate.month, dueDate.day);
    return taskDate.difference(today).inDays;
  }

  Task copyWith({
    String? id,
    String? title,
    String? description,
    DateTime? dueDate,
    bool? completed,
    Priority? priority,
    String? assignedTo,
    RelatedEntity? relatedTo,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Task(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      dueDate: dueDate ?? this.dueDate,
      completed: completed ?? this.completed,
      priority: priority ?? this.priority,
      assignedTo: assignedTo ?? this.assignedTo,
      relatedTo: relatedTo ?? this.relatedTo,
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
  completed;

  String get label {
    switch (this) {
      case TaskDueStatus.overdue:
        return 'Overdue';
      case TaskDueStatus.today:
        return 'Today';
      case TaskDueStatus.upcoming:
        return 'Upcoming';
      case TaskDueStatus.completed:
        return 'Completed';
    }
  }
}
