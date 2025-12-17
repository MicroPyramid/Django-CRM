import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

/// Lead status enumeration
enum LeadStatus {
  newLead('New', AppColors.primary500),
  contacted('Contacted', AppColors.warning500),
  qualified('Qualified', AppColors.success500),
  lost('Lost', AppColors.danger500);

  final String label;
  final Color color;

  const LeadStatus(this.label, this.color);

  /// Alias for label
  String get displayName => label;

  static LeadStatus fromString(String value) {
    switch (value.toLowerCase()) {
      case 'new':
        return LeadStatus.newLead;
      case 'contacted':
        return LeadStatus.contacted;
      case 'qualified':
        return LeadStatus.qualified;
      case 'lost':
        return LeadStatus.lost;
      default:
        return LeadStatus.newLead;
    }
  }
}

/// Lead source enumeration
enum LeadSource {
  website('Website', Icons.language),
  referral('Referral', Icons.people),
  linkedin('LinkedIn', Icons.business),
  coldCall('Cold Call', Icons.phone),
  tradeShow('Trade Show', Icons.event);

  final String label;
  final IconData icon;

  const LeadSource(this.label, this.icon);

  /// Alias for label
  String get displayName => label;

  static LeadSource fromString(String value) {
    switch (value.toLowerCase().replaceAll('-', '').replaceAll('_', '')) {
      case 'website':
        return LeadSource.website;
      case 'referral':
        return LeadSource.referral;
      case 'linkedin':
        return LeadSource.linkedin;
      case 'coldcall':
        return LeadSource.coldCall;
      case 'tradeshow':
        return LeadSource.tradeShow;
      default:
        return LeadSource.website;
    }
  }
}

/// Priority enumeration
enum Priority {
  low('Low', AppColors.gray400),
  medium('Medium', AppColors.warning500),
  high('High', AppColors.danger500);

  final String label;
  final Color color;

  const Priority(this.label, this.color);

  /// Alias for label
  String get displayName => label;

  static Priority fromString(String value) {
    switch (value.toLowerCase()) {
      case 'low':
        return Priority.low;
      case 'medium':
        return Priority.medium;
      case 'high':
        return Priority.high;
      default:
        return Priority.medium;
    }
  }
}

/// Lead model for BottleCRM
class Lead {
  final String id;
  final String name;
  final String company;
  final String email;
  final String? phone;
  final LeadStatus status;
  final LeadSource source;
  final Priority priority;
  final String assignedTo;
  final List<String> tags;
  final String? notes;
  final String? avatar;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Lead({
    required this.id,
    required this.name,
    required this.company,
    required this.email,
    this.phone,
    required this.status,
    required this.source,
    required this.priority,
    required this.assignedTo,
    this.tags = const [],
    this.notes,
    this.avatar,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Get lead initials for avatar fallback
  String get initials {
    final parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    } else if (parts.isNotEmpty && parts[0].isNotEmpty) {
      return parts[0][0].toUpperCase();
    }
    return '?';
  }

  /// Get first name
  String get firstName {
    final parts = name.trim().split(' ');
    return parts.isNotEmpty ? parts[0] : name;
  }

  Lead copyWith({
    String? id,
    String? name,
    String? company,
    String? email,
    String? phone,
    LeadStatus? status,
    LeadSource? source,
    Priority? priority,
    String? assignedTo,
    List<String>? tags,
    String? notes,
    String? avatar,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Lead(
      id: id ?? this.id,
      name: name ?? this.name,
      company: company ?? this.company,
      email: email ?? this.email,
      phone: phone ?? this.phone,
      status: status ?? this.status,
      source: source ?? this.source,
      priority: priority ?? this.priority,
      assignedTo: assignedTo ?? this.assignedTo,
      tags: tags ?? this.tags,
      notes: notes ?? this.notes,
      avatar: avatar ?? this.avatar,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Lead && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}
