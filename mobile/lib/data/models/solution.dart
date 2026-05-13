import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

/// Knowledge Base solution: a reusable answer that can be linked to tickets.
/// Mirrors `cases.models.Solution`.
class Solution {
  final String id;
  final String title;
  final String description;
  final SolutionStatus status;
  final bool isPublished;
  final int caseCount;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const Solution({
    required this.id,
    required this.title,
    required this.description,
    required this.status,
    this.isPublished = false,
    this.caseCount = 0,
    this.createdAt,
    this.updatedAt,
  });

  factory Solution.fromJson(Map<String, dynamic> json) {
    return Solution(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      status: SolutionStatus.fromString(json['status'] as String?),
      isPublished: json['is_published'] as bool? ?? false,
      caseCount: json['case_count'] as int? ?? 0,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'].toString())
          : null,
    );
  }

  Map<String, dynamic> toCreatePayload() => {
        'title': title,
        'description': description,
        'status': status.value,
        'is_published': isPublished,
      };

  Solution copyWith({
    String? id,
    String? title,
    String? description,
    SolutionStatus? status,
    bool? isPublished,
    int? caseCount,
  }) {
    return Solution(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      status: status ?? this.status,
      isPublished: isPublished ?? this.isPublished,
      caseCount: caseCount ?? this.caseCount,
      createdAt: createdAt,
      updatedAt: updatedAt,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Solution && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

enum SolutionStatus {
  draft('draft', 'Draft', AppColors.gray500),
  reviewed('reviewed', 'Reviewed', AppColors.warning500),
  approved('approved', 'Approved', AppColors.success600);

  final String value;
  final String label;
  final Color color;
  const SolutionStatus(this.value, this.label, this.color);

  static SolutionStatus fromString(String? value) {
    return SolutionStatus.values.firstWhere(
      (s) => s.value == value,
      orElse: () => SolutionStatus.draft,
    );
  }
}
