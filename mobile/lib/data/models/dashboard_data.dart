// Dashboard data models for BottleCRM
import 'package:flutter/foundation.dart';

/// Urgent counts from dashboard API
class UrgentCounts {
  final int overdueTasks;
  final int tasksDueToday;
  final int followupsToday;
  final int hotLeads;

  const UrgentCounts({
    this.overdueTasks = 0,
    this.tasksDueToday = 0,
    this.followupsToday = 0,
    this.hotLeads = 0,
  });

  factory UrgentCounts.fromJson(Map<String, dynamic> json) {
    return UrgentCounts(
      overdueTasks: json['overdue_tasks'] as int? ?? 0,
      tasksDueToday: json['tasks_due_today'] as int? ?? 0,
      followupsToday: json['followups_today'] as int? ?? 0,
      hotLeads: json['hot_leads'] as int? ?? 0,
    );
  }
}

/// Pipeline stage data
class PipelineStage {
  final String code;
  final String label;
  final int count;
  final double value;

  const PipelineStage({
    required this.code,
    required this.label,
    this.count = 0,
    this.value = 0,
  });

  factory PipelineStage.fromJson(String code, Map<String, dynamic> json) {
    return PipelineStage(
      code: code,
      label: json['label'] as String? ?? code,
      count: json['count'] as int? ?? 0,
      value: (json['value'] as num?)?.toDouble() ?? 0,
    );
  }
}

/// Revenue metrics from dashboard API
class RevenueMetrics {
  final double pipelineValue;
  final double weightedPipeline;
  final double wonThisMonth;
  final double conversionRate;
  final String currency;
  final int otherCurrencyCount;

  const RevenueMetrics({
    this.pipelineValue = 0,
    this.weightedPipeline = 0,
    this.wonThisMonth = 0,
    this.conversionRate = 0,
    this.currency = 'USD',
    this.otherCurrencyCount = 0,
  });

  factory RevenueMetrics.fromJson(Map<String, dynamic> json) {
    return RevenueMetrics(
      pipelineValue: (json['pipeline_value'] as num?)?.toDouble() ?? 0,
      weightedPipeline: (json['weighted_pipeline'] as num?)?.toDouble() ?? 0,
      wonThisMonth: (json['won_this_month'] as num?)?.toDouble() ?? 0,
      conversionRate: (json['conversion_rate'] as num?)?.toDouble() ?? 0,
      currency: json['currency'] as String? ?? 'USD',
      otherCurrencyCount: json['other_currency_count'] as int? ?? 0,
    );
  }
}

/// Hot lead from dashboard API
class HotLead {
  final String id;
  final String firstName;
  final String lastName;
  final String? company;
  final String? rating;
  final DateTime? nextFollowUp;
  final DateTime? lastContacted;

  const HotLead({
    required this.id,
    required this.firstName,
    required this.lastName,
    this.company,
    this.rating,
    this.nextFollowUp,
    this.lastContacted,
  });

  String get fullName => '$firstName $lastName'.trim();

  factory HotLead.fromJson(Map<String, dynamic> json) {
    return HotLead(
      id: json['id']?.toString() ?? '',
      firstName: json['first_name'] as String? ?? '',
      lastName: json['last_name'] as String? ?? '',
      company: json['company'] as String?,
      rating: json['rating'] as String?,
      nextFollowUp: json['next_follow_up'] != null
          ? DateTime.tryParse(json['next_follow_up'] as String)
          : null,
      lastContacted: json['last_contacted'] != null
          ? DateTime.tryParse(json['last_contacted'] as String)
          : null,
    );
  }
}

/// Dashboard task from API
class DashboardTask {
  final String id;
  final String title;
  final String? description;
  final String status;
  final String priority;
  final DateTime? dueDate;
  final String? accountName;
  final String? leadName;

  const DashboardTask({
    required this.id,
    required this.title,
    this.description,
    this.status = 'New',
    this.priority = 'Medium',
    this.dueDate,
    this.accountName,
    this.leadName,
  });

  bool get isCompleted => status.toLowerCase() == 'completed';

  String? get relatedTo => accountName ?? leadName;

  factory DashboardTask.fromJson(Map<String, dynamic> json) {
    return DashboardTask(
      id: json['id']?.toString() ?? '',
      title: json['title'] as String? ?? 'Untitled',
      description: json['description'] as String?,
      status: json['status'] as String? ?? 'New',
      priority: json['priority'] as String? ?? 'Medium',
      dueDate: json['due_date'] != null
          ? DateTime.tryParse(json['due_date'] as String)
          : null,
      accountName: json['account']?['name'] as String?,
      leadName: json['lead'] != null
          ? '${json['lead']['first_name'] ?? ''} ${json['lead']['last_name'] ?? ''}'.trim()
          : null,
    );
  }
}

/// Dashboard activity from API
class DashboardActivity {
  final String id;
  final String activityType;
  final String description;
  final DateTime createdAt;
  final String? userName;
  final String? entityType;
  final String? entityName;

  const DashboardActivity({
    required this.id,
    required this.activityType,
    required this.description,
    required this.createdAt,
    this.userName,
    this.entityType,
    this.entityName,
  });

  String get relativeTime {
    final now = DateTime.now();
    final diff = now.difference(createdAt);

    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return '${(diff.inDays / 7).floor()}w ago';
  }

  factory DashboardActivity.fromJson(Map<String, dynamic> json) {
    return DashboardActivity(
      id: json['id']?.toString() ?? '',
      activityType: json['activity_type'] as String? ?? 'update',
      description: json['description'] as String? ?? '',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
      userName: json['created_by']?['user__email'] as String?,
      entityType: json['entity_type'] as String?,
      entityName: json['entity_name'] as String?,
    );
  }
}

/// Complete dashboard data response
class DashboardData {
  final int accountsCount;
  final int contactsCount;
  final int leadsCount;
  final int opportunitiesCount;
  final UrgentCounts urgentCounts;
  final List<PipelineStage> pipelineByStage;
  final RevenueMetrics revenueMetrics;
  final List<HotLead> hotLeads;
  final List<DashboardTask> tasks;
  final List<DashboardActivity> activities;

  const DashboardData({
    this.accountsCount = 0,
    this.contactsCount = 0,
    this.leadsCount = 0,
    this.opportunitiesCount = 0,
    this.urgentCounts = const UrgentCounts(),
    this.pipelineByStage = const [],
    this.revenueMetrics = const RevenueMetrics(),
    this.hotLeads = const [],
    this.tasks = const [],
    this.activities = const [],
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    debugPrint('DashboardData.fromJson: Starting to parse...');
    debugPrint('DashboardData.fromJson: Keys: ${json.keys.toList()}');

    // Parse pipeline by stage
    debugPrint('DashboardData.fromJson: Parsing pipeline_by_stage...');
    final pipelineMap = json['pipeline_by_stage'] as Map<String, dynamic>? ?? {};
    final pipelineStages = pipelineMap.entries
        .map((e) => PipelineStage.fromJson(e.key, e.value as Map<String, dynamic>))
        .toList();

    // Sort pipeline stages in order
    final stageOrder = ['PROSPECTING', 'QUALIFICATION', 'PROPOSAL', 'NEGOTIATION', 'CLOSED_WON', 'CLOSED_LOST'];
    pipelineStages.sort((a, b) {
      final aIndex = stageOrder.indexOf(a.code);
      final bIndex = stageOrder.indexOf(b.code);
      return aIndex.compareTo(bIndex);
    });
    debugPrint('DashboardData.fromJson: Pipeline stages parsed: ${pipelineStages.length}');

    // Parse urgent counts
    debugPrint('DashboardData.fromJson: Parsing urgent_counts...');
    final urgentCounts = json['urgent_counts'] != null
        ? UrgentCounts.fromJson(json['urgent_counts'] as Map<String, dynamic>)
        : const UrgentCounts();
    debugPrint('DashboardData.fromJson: Urgent counts parsed');

    // Parse revenue metrics
    debugPrint('DashboardData.fromJson: Parsing revenue_metrics...');
    final revenueMetrics = json['revenue_metrics'] != null
        ? RevenueMetrics.fromJson(json['revenue_metrics'] as Map<String, dynamic>)
        : const RevenueMetrics();
    debugPrint('DashboardData.fromJson: Revenue metrics parsed');

    // Parse hot leads
    debugPrint('DashboardData.fromJson: Parsing hot_leads...');
    final hotLeadsList = <HotLead>[];
    if (json['hot_leads'] != null) {
      for (final item in json['hot_leads'] as List<dynamic>) {
        try {
          hotLeadsList.add(HotLead.fromJson(item as Map<String, dynamic>));
        } catch (e) {
          debugPrint('DashboardData.fromJson: Error parsing hot lead: $e');
          debugPrint('DashboardData.fromJson: Hot lead data: $item');
        }
      }
    }
    debugPrint('DashboardData.fromJson: Hot leads parsed: ${hotLeadsList.length}');

    // Parse tasks
    debugPrint('DashboardData.fromJson: Parsing tasks...');
    final tasksList = <DashboardTask>[];
    if (json['tasks'] != null) {
      for (final item in json['tasks'] as List<dynamic>) {
        try {
          tasksList.add(DashboardTask.fromJson(item as Map<String, dynamic>));
        } catch (e) {
          debugPrint('DashboardData.fromJson: Error parsing task: $e');
          debugPrint('DashboardData.fromJson: Task data: $item');
        }
      }
    }
    debugPrint('DashboardData.fromJson: Tasks parsed: ${tasksList.length}');

    // Parse activities
    debugPrint('DashboardData.fromJson: Parsing activities...');
    final activitiesList = <DashboardActivity>[];
    if (json['activities'] != null) {
      for (final item in json['activities'] as List<dynamic>) {
        try {
          activitiesList.add(DashboardActivity.fromJson(item as Map<String, dynamic>));
        } catch (e) {
          debugPrint('DashboardData.fromJson: Error parsing activity: $e');
          debugPrint('DashboardData.fromJson: Activity data: $item');
        }
      }
    }
    debugPrint('DashboardData.fromJson: Activities parsed: ${activitiesList.length}');

    debugPrint('DashboardData.fromJson: All parsing complete!');

    return DashboardData(
      accountsCount: json['accounts_count'] as int? ?? 0,
      contactsCount: json['contacts_count'] as int? ?? 0,
      leadsCount: json['leads_count'] as int? ?? 0,
      opportunitiesCount: json['opportunities_count'] as int? ?? 0,
      urgentCounts: urgentCounts,
      pipelineByStage: pipelineStages,
      revenueMetrics: revenueMetrics,
      hotLeads: hotLeadsList,
      tasks: tasksList,
      activities: activitiesList,
    );
  }
}
