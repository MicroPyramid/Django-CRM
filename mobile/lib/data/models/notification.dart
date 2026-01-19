import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import 'task.dart';

/// Notification type enumeration
enum NotificationType {
  taskDue('Task Due', Icons.access_time, AppColors.warning500),
  taskAssigned('Task Assigned', Icons.assignment_outlined, AppColors.primary500),
  dealWon('Deal Won', Icons.emoji_events_outlined, AppColors.success500),
  dealLost('Deal Lost', Icons.cancel_outlined, AppColors.danger500),
  dealStageChanged('Stage Changed', Icons.trending_up, AppColors.primary600),
  leadAssigned('Lead Assigned', Icons.person_add_outlined, AppColors.primary500),
  mention('Mention', Icons.alternate_email, AppColors.purple500),
  reminder('Reminder', Icons.notifications_outlined, AppColors.warning500),
  system('System', Icons.info_outlined, AppColors.gray500);

  final String label;
  final IconData icon;
  final Color color;

  const NotificationType(this.label, this.icon, this.color);

  static NotificationType fromString(String value) {
    switch (value.toLowerCase().replaceAll('-', '').replaceAll('_', '')) {
      case 'taskdue':
        return NotificationType.taskDue;
      case 'taskassigned':
        return NotificationType.taskAssigned;
      case 'dealwon':
        return NotificationType.dealWon;
      case 'deallost':
        return NotificationType.dealLost;
      case 'dealstagechanged':
        return NotificationType.dealStageChanged;
      case 'leadassigned':
        return NotificationType.leadAssigned;
      case 'mention':
        return NotificationType.mention;
      case 'reminder':
        return NotificationType.reminder;
      case 'system':
        return NotificationType.system;
      default:
        return NotificationType.system;
    }
  }
}

/// Notification model for BottleCRM
class AppNotification {
  final String id;
  final String userId;
  final NotificationType type;
  final String title;
  final String message;
  final bool read;
  final RelatedEntity? relatedTo;
  final DateTime timestamp;

  const AppNotification({
    required this.id,
    required this.userId,
    required this.type,
    required this.title,
    required this.message,
    this.read = false,
    this.relatedTo,
    required this.timestamp,
  });

  /// Get relative time string
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

  /// Check if notification is from today
  bool get isToday {
    final now = DateTime.now();
    return timestamp.year == now.year &&
        timestamp.month == now.month &&
        timestamp.day == now.day;
  }

  AppNotification copyWith({
    String? id,
    String? userId,
    NotificationType? type,
    String? title,
    String? message,
    bool? read,
    RelatedEntity? relatedTo,
    DateTime? timestamp,
  }) {
    return AppNotification(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      type: type ?? this.type,
      title: title ?? this.title,
      message: message ?? this.message,
      read: read ?? this.read,
      relatedTo: relatedTo ?? this.relatedTo,
      timestamp: timestamp ?? this.timestamp,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is AppNotification &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}
