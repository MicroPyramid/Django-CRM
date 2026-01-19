import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import 'lead.dart';

/// Opportunity type enumeration
enum OpportunityType {
  newBusiness('NEW_BUSINESS', 'New Business'),
  existingBusiness('EXISTING_BUSINESS', 'Existing Business'),
  renewal('RENEWAL', 'Renewal'),
  upsell('UPSELL', 'Upsell'),
  crossSell('CROSS_SELL', 'Cross Sell');

  final String value;
  final String label;

  const OpportunityType(this.value, this.label);

  static OpportunityType fromString(String? value) {
    if (value == null) return OpportunityType.newBusiness;
    return OpportunityType.values.firstWhere(
      (e) => e.value.toLowerCase() == value.toLowerCase().replaceAll(' ', '_'),
      orElse: () => OpportunityType.newBusiness,
    );
  }
}

/// Opportunity lead source enumeration (different from Lead's source)
enum OpportunitySource {
  none('NONE', 'None'),
  call('CALL', 'Call'),
  email('EMAIL', 'Email'),
  existingCustomer('EXISTING CUSTOMER', 'Existing Customer'),
  partner('PARTNER', 'Partner'),
  publicRelations('PUBLIC RELATIONS', 'Public Relations'),
  campaign('CAMPAIGN', 'Campaign'),
  website('WEBSITE', 'Website'),
  other('OTHER', 'Other');

  final String value;
  final String label;

  const OpportunitySource(this.value, this.label);

  static OpportunitySource fromString(String? value) {
    if (value == null) return OpportunitySource.none;
    return OpportunitySource.values.firstWhere(
      (e) => e.value.toLowerCase() == value.toLowerCase(),
      orElse: () => OpportunitySource.none,
    );
  }
}

/// Currency enumeration
enum Currency {
  usd('USD', 'USD', '\$'),
  eur('EUR', 'EUR', '€'),
  gbp('GBP', 'GBP', '£'),
  inr('INR', 'INR', '₹'),
  cad('CAD', 'CAD', 'C\$'),
  aud('AUD', 'AUD', 'A\$'),
  jpy('JPY', 'JPY', '¥'),
  cny('CNY', 'CNY', '¥'),
  chf('CHF', 'CHF', 'CHF'),
  sgd('SGD', 'SGD', 'S\$'),
  aed('AED', 'AED', 'د.إ'),
  brl('BRL', 'BRL', 'R\$'),
  mxn('MXN', 'MXN', '\$');

  final String value;
  final String label;
  final String symbol;

  const Currency(this.value, this.label, this.symbol);

  static Currency fromString(String? value) {
    if (value == null) return Currency.usd;
    return Currency.values.firstWhere(
      (e) => e.value.toLowerCase() == value.toLowerCase(),
      orElse: () => Currency.usd,
    );
  }
}

/// Deal stage enumeration
enum DealStage {
  prospecting('PROSPECTING', 'Prospecting', AppColors.gray400, 10),
  qualified('QUALIFICATION', 'Qualified', AppColors.primary500, 25),
  proposal('PROPOSAL', 'Proposal', AppColors.purple500, 50),
  negotiation('NEGOTIATION', 'Negotiation', AppColors.warning500, 75),
  closedWon('CLOSED_WON', 'Closed Won', AppColors.success500, 100),
  closedLost('CLOSED_LOST', 'Closed Lost', AppColors.danger500, 0);

  final String value;
  final String label;
  final Color color;
  final int defaultProbability;

  const DealStage(this.value, this.label, this.color, this.defaultProbability);

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
  final String? accountId;
  final List<DealProduct> products;
  final String assignedTo;
  final List<String> assignedToIds;
  final Priority priority;
  final List<String> labels;
  final List<String> tagIds;
  final List<String> contactIds;
  final String? notes;
  final OpportunityType opportunityType;
  final OpportunitySource leadSource;
  final Currency currency;
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
    this.accountId,
    this.products = const [],
    required this.assignedTo,
    this.assignedToIds = const [],
    required this.priority,
    this.labels = const [],
    this.tagIds = const [],
    this.contactIds = const [],
    this.notes,
    this.opportunityType = OpportunityType.newBusiness,
    this.leadSource = OpportunitySource.none,
    this.currency = Currency.usd,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Factory constructor to create Deal from JSON (backend API)
  factory Deal.fromJson(Map<String, dynamic> json) {
    // Parse tags - both names and IDs
    List<String> parsedTags = [];
    List<String> parsedTagIds = [];
    if (json['tags'] != null) {
      final tagsList = json['tags'] as List<dynamic>? ?? [];
      for (final t in tagsList) {
        if (t is Map<String, dynamic>) {
          final name = t['name'] as String? ?? '';
          final id = t['id']?.toString() ?? '';
          if (name.isNotEmpty) parsedTags.add(name);
          if (id.isNotEmpty) parsedTagIds.add(id);
        }
      }
    }

    // Parse assigned_to - get first person's email for display and all IDs
    String assignedToName = 'Unassigned';
    List<String> assignedToIds = [];
    if (json['assigned_to'] != null) {
      final assignedList = json['assigned_to'] as List<dynamic>? ?? [];
      for (final item in assignedList) {
        if (item is Map<String, dynamic>) {
          final id = item['id']?.toString() ?? '';
          if (id.isNotEmpty) assignedToIds.add(id);
          if (assignedToName == 'Unassigned') {
            final email = item['user']?['email'] as String? ??
                          item['user__email'] as String? ?? '';
            assignedToName = email.split('@').first;
            if (assignedToName.isEmpty) assignedToName = 'Assigned';
          }
        }
      }
    }

    // Parse contacts - get IDs
    List<String> contactIds = [];
    if (json['contacts'] != null) {
      final contactsList = json['contacts'] as List<dynamic>? ?? [];
      for (final c in contactsList) {
        if (c is Map<String, dynamic>) {
          final id = c['id']?.toString() ?? '';
          if (id.isNotEmpty) contactIds.add(id);
        }
      }
    }

    // Parse account/company name and ID
    String companyName = 'No Account';
    String? accountId;
    if (json['account'] != null && json['account'] is Map<String, dynamic>) {
      companyName = json['account']['name'] as String? ?? 'No Account';
      accountId = json['account']['id']?.toString();
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
      accountId: accountId,
      products: products,
      assignedTo: assignedToName,
      assignedToIds: assignedToIds,
      priority: Priority.medium, // API doesn't have priority, default to medium
      labels: parsedTags,
      tagIds: parsedTagIds,
      contactIds: contactIds,
      notes: json['description'] as String?,
      opportunityType: OpportunityType.fromString(json['opportunity_type'] as String?),
      leadSource: OpportunitySource.fromString(json['lead_source'] as String?),
      currency: Currency.fromString(json['currency'] as String?),
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  /// Convert Deal to JSON for API requests (create/update)
  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {
      'name': title,
      'stage': stage.value,
      'probability': probability,
    };

    if (value > 0) {
      data['amount'] = value.toStringAsFixed(2);
    }
    if (accountId != null && accountId!.isNotEmpty) {
      data['account'] = accountId;
    }
    if (closeDate != null) {
      data['closed_on'] = '${closeDate!.year}-${closeDate!.month.toString().padLeft(2, '0')}-${closeDate!.day.toString().padLeft(2, '0')}';
    }
    if (notes != null && notes!.isNotEmpty) {
      data['description'] = notes;
    }
    if (assignedToIds.isNotEmpty) {
      data['assigned_to'] = assignedToIds;
    }
    if (contactIds.isNotEmpty) {
      data['contacts'] = contactIds;
    }
    if (tagIds.isNotEmpty) {
      data['tags'] = tagIds;
    }
    data['opportunity_type'] = opportunityType.value;
    data['lead_source'] = leadSource.value;
    data['currency'] = currency.value;

    return data;
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
    String? accountId,
    List<DealProduct>? products,
    String? assignedTo,
    List<String>? assignedToIds,
    Priority? priority,
    List<String>? labels,
    List<String>? tagIds,
    List<String>? contactIds,
    String? notes,
    OpportunityType? opportunityType,
    OpportunitySource? leadSource,
    Currency? currency,
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
      accountId: accountId ?? this.accountId,
      products: products ?? this.products,
      assignedTo: assignedTo ?? this.assignedTo,
      assignedToIds: assignedToIds ?? this.assignedToIds,
      priority: priority ?? this.priority,
      labels: labels ?? this.labels,
      tagIds: tagIds ?? this.tagIds,
      contactIds: contactIds ?? this.contactIds,
      notes: notes ?? this.notes,
      opportunityType: opportunityType ?? this.opportunityType,
      leadSource: leadSource ?? this.leadSource,
      currency: currency ?? this.currency,
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
