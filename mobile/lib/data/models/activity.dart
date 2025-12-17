import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import 'task.dart';

/// Activity type enumeration
enum ActivityType {
  call('Call', Icons.phone_outlined, AppColors.primary500),
  email('Email', Icons.email_outlined, AppColors.purple500),
  note('Note', Icons.sticky_note_2_outlined, AppColors.gray500),
  meeting('Meeting', Icons.event_outlined, AppColors.warning500),
  stageChange('Stage Change', Icons.trending_up_outlined, AppColors.primary600),
  dealWon('Deal Won', Icons.emoji_events_outlined, AppColors.success500),
  dealLost('Deal Lost', Icons.cancel_outlined, AppColors.danger500),
  taskCompleted('Task Completed', Icons.check_circle_outline, AppColors.success500),
  leadCreated('Lead Created', Icons.person_add_outlined, AppColors.primary500),
  dealCreated('Deal Created', Icons.add_business_outlined, AppColors.primary500);

  final String label;
  final IconData icon;
  final Color color;

  const ActivityType(this.label, this.icon, this.color);

  static ActivityType fromString(String value) {
    switch (value.toLowerCase().replaceAll('-', '').replaceAll('_', '')) {
      case 'call':
        return ActivityType.call;
      case 'email':
        return ActivityType.email;
      case 'note':
        return ActivityType.note;
      case 'meeting':
        return ActivityType.meeting;
      case 'stagechange':
        return ActivityType.stageChange;
      case 'dealwon':
        return ActivityType.dealWon;
      case 'deallost':
        return ActivityType.dealLost;
      case 'taskcompleted':
        return ActivityType.taskCompleted;
      case 'leadcreated':
        return ActivityType.leadCreated;
      case 'dealcreated':
        return ActivityType.dealCreated;
      default:
        return ActivityType.note;
    }
  }
}

/// Activity model for BottleCRM
class Activity {
  final String id;
  final ActivityType type;
  final String title;
  final String? description;
  final DateTime timestamp;
  final String userId;
  final String? userName;
  final RelatedEntity? relatedTo;
  final Map<String, dynamic>? metadata;

  const Activity({
    required this.id,
    required this.type,
    required this.title,
    this.description,
    required this.timestamp,
    required this.userId,
    this.userName,
    this.relatedTo,
    this.metadata,
  });

  /// Get relative time string (e.g., "2 hours ago")
  String get relativeTime {
    final now = DateTime.now();
    final diff = now.difference(timestamp);

    if (diff.inMinutes < 1) {
      return 'Just now';
    } else if (diff.inMinutes < 60) {
      return '${diff.inMinutes}m ago';
    } else if (diff.inHours < 24) {
      return '${diff.inHours}h ago';
    } else if (diff.inDays < 7) {
      return '${diff.inDays}d ago';
    } else if (diff.inDays < 30) {
      final weeks = (diff.inDays / 7).floor();
      return '${weeks}w ago';
    } else {
      final months = (diff.inDays / 30).floor();
      return '${months}mo ago';
    }
  }

  /// Check if activity is from today
  bool get isToday {
    final now = DateTime.now();
    return timestamp.year == now.year &&
        timestamp.month == now.month &&
        timestamp.day == now.day;
  }

  Activity copyWith({
    String? id,
    ActivityType? type,
    String? title,
    String? description,
    DateTime? timestamp,
    String? userId,
    String? userName,
    RelatedEntity? relatedTo,
    Map<String, dynamic>? metadata,
  }) {
    return Activity(
      id: id ?? this.id,
      type: type ?? this.type,
      title: title ?? this.title,
      description: description ?? this.description,
      timestamp: timestamp ?? this.timestamp,
      userId: userId ?? this.userId,
      userName: userName ?? this.userName,
      relatedTo: relatedTo ?? this.relatedTo,
      metadata: metadata ?? this.metadata,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Activity && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}
