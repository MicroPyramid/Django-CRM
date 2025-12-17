import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import 'lead.dart';

/// Deal stage enumeration
enum DealStage {
  prospecting('Prospecting', AppColors.gray400, 10),
  qualified('Qualified', AppColors.primary500, 25),
  proposal('Proposal', AppColors.purple500, 50),
  negotiation('Negotiation', AppColors.warning500, 75),
  closedWon('Closed Won', AppColors.success500, 100),
  closedLost('Closed Lost', AppColors.danger500, 0);

  final String label;
  final Color color;
  final int defaultProbability;

  const DealStage(this.label, this.color, this.defaultProbability);

  /// Short label for compact displays
  String get shortLabel {
    switch (this) {
      case DealStage.prospecting:
        return 'Prospect';
      case DealStage.qualified:
        return 'Qualified';
      case DealStage.proposal:
        return 'Proposal';
      case DealStage.negotiation:
        return 'Negotiate';
      case DealStage.closedWon:
        return 'Won';
      case DealStage.closedLost:
        return 'Lost';
    }
  }

  /// Get icon for this stage
  IconData get icon {
    switch (this) {
      case DealStage.prospecting:
        return Icons.search;
      case DealStage.qualified:
        return Icons.check_circle_outline;
      case DealStage.proposal:
        return Icons.description_outlined;
      case DealStage.negotiation:
        return Icons.chat_outlined;
      case DealStage.closedWon:
        return Icons.emoji_events_outlined;
      case DealStage.closedLost:
        return Icons.cancel_outlined;
    }
  }

  /// Check if this is a closed stage
  bool get isClosed =>
      this == DealStage.closedWon || this == DealStage.closedLost;

  /// Check if this is a won deal
  bool get isWon => this == DealStage.closedWon;

  /// Get the next stage (for progression)
  DealStage? get nextStage {
    switch (this) {
      case DealStage.prospecting:
        return DealStage.qualified;
      case DealStage.qualified:
        return DealStage.proposal;
      case DealStage.proposal:
        return DealStage.negotiation;
      case DealStage.negotiation:
        return DealStage.closedWon;
      case DealStage.closedWon:
      case DealStage.closedLost:
        return null;
    }
  }

  /// Get stage index (0-based)
  int get stageIndex {
    switch (this) {
      case DealStage.prospecting:
        return 0;
      case DealStage.qualified:
        return 1;
      case DealStage.proposal:
        return 2;
      case DealStage.negotiation:
        return 3;
      case DealStage.closedWon:
        return 4;
      case DealStage.closedLost:
        return 5;
    }
  }

  /// Get display name (alias for label)
  String get displayName => label;

  static DealStage fromString(String? value) {
    if (value == null) return DealStage.prospecting;
    switch (value.toLowerCase().replaceAll('-', '').replaceAll('_', '').replaceAll(' ', '')) {
      case 'prospecting':
        return DealStage.prospecting;
      case 'qualified':
      case 'qualification': // Backend uses QUALIFICATION
        return DealStage.qualified;
      case 'proposal':
        return DealStage.proposal;
      case 'negotiation':
        return DealStage.negotiation;
      case 'closedwon':
        return DealStage.closedWon;
      case 'closedlost':
        return DealStage.closedLost;
      default:
        return DealStage.prospecting;
    }
  }

  /// Get all active stages (not closed)
  static List<DealStage> get activeStages => [
        DealStage.prospecting,
        DealStage.qualified,
        DealStage.proposal,
        DealStage.negotiation,
      ];

  /// Get pipeline stages for kanban view
  static List<DealStage> get pipelineStages => [
        DealStage.prospecting,
        DealStage.qualified,
        DealStage.proposal,
        DealStage.negotiation,
        DealStage.closedWon,
      ];
}

/// Product in a deal
class DealProduct {
  final String id;
  final String name;
  final int quantity;
  final double unitPrice;

  const DealProduct({
    required this.id,
    required this.name,
    required this.quantity,
    required this.unitPrice,
  });

  double get totalPrice => quantity * unitPrice;
}

/// Deal model for BottleCRM
class Deal {
  final String id;
  final String title;
  final double value;
  final DealStage stage;
  final int probability;
  final DateTime? closeDate;
  final String? leadId;
  final String companyName;
  final List<DealProduct> products;
  final String assignedTo;
  final Priority priority;
  final List<String> labels;
  final String? notes;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Deal({
    required this.id,
    required this.title,
    required this.value,
    required this.stage,
    required this.probability,
    this.closeDate,
    this.leadId,
    required this.companyName,
    this.products = const [],
    required this.assignedTo,
    required this.priority,
    this.labels = const [],
    this.notes,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Factory constructor to create Deal from JSON (backend API)
  factory Deal.fromJson(Map<String, dynamic> json) {
    // Parse tags
    List<String> parsedTags = [];
    if (json['tags'] != null) {
      final tagsList = json['tags'] as List<dynamic>? ?? [];
      parsedTags = tagsList.map((t) {
        if (t is Map<String, dynamic>) {
          return t['name'] as String? ?? '';
        }
        return t.toString();
      }).where((t) => t.isNotEmpty).toList();
    }

    // Parse assigned_to - get first person's email for display
    String assignedToName = 'Unassigned';
    if (json['assigned_to'] != null) {
      final assignedList = json['assigned_to'] as List<dynamic>? ?? [];
      if (assignedList.isNotEmpty) {
        final first = assignedList.first;
        if (first is Map<String, dynamic>) {
          final email = first['user']?['email'] as String? ??
                        first['user__email'] as String? ?? '';
          assignedToName = email.split('@').first;
          if (assignedToName.isEmpty) assignedToName = 'Assigned';
        }
      }
    }

    // Parse account/company name
    String companyName = 'No Account';
    if (json['account'] != null && json['account'] is Map<String, dynamic>) {
      companyName = json['account']['name'] as String? ?? 'No Account';
    }

    // Parse products/line_items
    List<DealProduct> products = [];
    if (json['line_items'] != null) {
      final lineItems = json['line_items'] as List<dynamic>? ?? [];
      products = lineItems.map((item) {
        if (item is Map<String, dynamic>) {
          // Parse quantity - can be num or string
          int qty = 1;
          if (item['quantity'] != null) {
            if (item['quantity'] is num) {
              qty = (item['quantity'] as num).toInt();
            } else if (item['quantity'] is String) {
              qty = int.tryParse(item['quantity'] as String) ?? 1;
            }
          }
          // Parse unit_price - can be num or string
          double price = 0.0;
          if (item['unit_price'] != null) {
            if (item['unit_price'] is num) {
              price = (item['unit_price'] as num).toDouble();
            } else if (item['unit_price'] is String) {
              price = double.tryParse(item['unit_price'] as String) ?? 0.0;
            }
          }
          return DealProduct(
            id: item['id']?.toString() ?? '',
            name: item['name'] as String? ?? '',
            quantity: qty,
            unitPrice: price,
          );
        }
        return const DealProduct(id: '', name: '', quantity: 0, unitPrice: 0);
      }).where((p) => p.id.isNotEmpty).toList();
    }

    // Parse close date
    DateTime? closeDate;
    if (json['closed_on'] != null) {
      closeDate = DateTime.tryParse(json['closed_on'] as String);
    }

    // Parse amount - can be num or string
    double amount = 0.0;
    if (json['amount'] != null) {
      if (json['amount'] is num) {
        amount = (json['amount'] as num).toDouble();
      } else if (json['amount'] is String) {
        amount = double.tryParse(json['amount'] as String) ?? 0.0;
      }
    }

    // Parse probability - can be num or string
    int probability = 0;
    if (json['probability'] != null) {
      if (json['probability'] is num) {
        probability = (json['probability'] as num).toInt();
      } else if (json['probability'] is String) {
        probability = int.tryParse(json['probability'] as String) ?? 0;
      }
    }

    return Deal(
      id: json['id']?.toString() ?? '',
      title: json['name'] as String? ?? '',
      value: amount,
      stage: DealStage.fromString(json['stage'] as String?),
      probability: probability,
      closeDate: closeDate,
      leadId: null, // API doesn't have lead reference directly
      companyName: companyName,
      products: products,
      assignedTo: assignedToName,
      priority: Priority.medium, // API doesn't have priority, default to medium
      labels: parsedTags,
      notes: json['description'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
      updatedAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  /// Get weighted value based on probability
  double get weightedValue => value * (probability / 100);

  /// Check if deal is closing soon (within 7 days)
  bool get isClosingSoon {
    if (closeDate == null) return false;
    final daysUntilClose = closeDate!.difference(DateTime.now()).inDays;
    return daysUntilClose >= 0 && daysUntilClose <= 7;
  }

  /// Check if deal is overdue
  bool get isOverdue {
    if (closeDate == null || stage.isClosed) return false;
    return closeDate!.isBefore(DateTime.now());
  }

  /// Days until close date
  int? get daysUntilClose {
    if (closeDate == null) return null;
    return closeDate!.difference(DateTime.now()).inDays;
  }

  Deal copyWith({
    String? id,
    String? title,
    double? value,
    DealStage? stage,
    int? probability,
    DateTime? closeDate,
    String? leadId,
    String? companyName,
    List<DealProduct>? products,
    String? assignedTo,
    Priority? priority,
    List<String>? labels,
    String? notes,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Deal(
      id: id ?? this.id,
      title: title ?? this.title,
      value: value ?? this.value,
      stage: stage ?? this.stage,
      probability: probability ?? this.probability,
      closeDate: closeDate ?? this.closeDate,
      leadId: leadId ?? this.leadId,
      companyName: companyName ?? this.companyName,
      products: products ?? this.products,
      assignedTo: assignedTo ?? this.assignedTo,
      priority: priority ?? this.priority,
      labels: labels ?? this.labels,
      notes: notes ?? this.notes,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Deal && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}
