import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

enum SupportCategory {
  technical('technical', 'Technical issue'),
  billing('billing', 'Billing'),
  account('account', 'Account access'),
  featureRequest('feature_request', 'Feature request'),
  other('other', 'Other');

  const SupportCategory(this.value, this.label);
  final String value;
  final String label;

  static SupportCategory fromValue(String? value) => values.firstWhere(
    (item) => item.value == value,
    orElse: () => SupportCategory.other,
  );
}

enum SupportStatus {
  open('open', 'Open', AppColors.danger600),
  inProgress('in_progress', 'In progress', AppColors.warning600),
  waitingOnCustomer(
    'waiting_on_customer',
    'Waiting on you',
    AppColors.primary600,
  ),
  resolved('resolved', 'Resolved', AppColors.success600),
  closed('closed', 'Closed', AppColors.gray500);

  const SupportStatus(this.value, this.label, this.color);
  final String value;
  final String label;
  final Color color;

  static SupportStatus fromValue(String? value) => values.firstWhere(
    (item) => item.value == value,
    orElse: () => SupportStatus.open,
  );
}

class SupportMessage {
  const SupportMessage({
    required this.id,
    required this.authorLabel,
    required this.isStaff,
    required this.body,
    this.attachmentName,
    required this.createdAt,
  });

  final String id;
  final String authorLabel;
  final bool isStaff;
  final String body;
  final String? attachmentName;
  final DateTime createdAt;

  bool get hasAttachment => (attachmentName ?? '').isNotEmpty;

  factory SupportMessage.fromJson(Map<String, dynamic> json) => SupportMessage(
    id: json['id']?.toString() ?? '',
    authorLabel: json['author_label']?.toString() ?? 'Unknown',
    isStaff: json['author_type'] == 'staff',
    body: json['body']?.toString() ?? '',
    attachmentName: json['attachment_name']?.toString().isEmpty ?? true
        ? null
        : json['attachment_name'].toString(),
    createdAt:
        DateTime.tryParse(json['created_at']?.toString() ?? '') ??
        DateTime.fromMillisecondsSinceEpoch(0),
  );
}

class SupportTicket {
  const SupportTicket({
    required this.id,
    required this.reference,
    required this.subject,
    required this.category,
    required this.status,
    required this.priorityLabel,
    required this.messageCount,
    required this.assigned,
    this.firstResponseAt,
    required this.lastActivityAt,
    required this.createdAt,
    this.messages = const [],
  });

  final String id;
  final String reference;
  final String subject;
  final SupportCategory category;
  final SupportStatus status;
  final String priorityLabel;
  final int messageCount;
  final bool assigned;
  final DateTime? firstResponseAt;
  final DateTime lastActivityAt;
  final DateTime createdAt;
  final List<SupportMessage> messages;

  bool get canReply => status != SupportStatus.closed;

  factory SupportTicket.fromJson(Map<String, dynamic> json) {
    final rawMessages = json['messages'];
    final messages = rawMessages is List
        ? rawMessages
              .whereType<Map<String, dynamic>>()
              .map(SupportMessage.fromJson)
              .toList()
        : <SupportMessage>[];
    return SupportTicket(
      id: json['id']?.toString() ?? '',
      reference: json['reference']?.toString() ?? '',
      subject: json['subject']?.toString() ?? '',
      category: SupportCategory.fromValue(json['category']?.toString()),
      status: SupportStatus.fromValue(json['status']?.toString()),
      priorityLabel: json['priority_label']?.toString() ?? 'Normal',
      messageCount: json['message_count'] as int? ?? messages.length,
      assigned: json['assigned'] as bool? ?? false,
      firstResponseAt: DateTime.tryParse(
        json['first_response_at']?.toString() ?? '',
      ),
      lastActivityAt:
          DateTime.tryParse(json['last_activity_at']?.toString() ?? '') ??
          DateTime.fromMillisecondsSinceEpoch(0),
      createdAt:
          DateTime.tryParse(json['created_at']?.toString() ?? '') ??
          DateTime.fromMillisecondsSinceEpoch(0),
      messages: messages,
    );
  }
}
