import '../models/models.dart';

/// Mock data for BottleCRM
/// Comprehensive realistic data for all screens
class MockData {
  MockData._();

  // ============================================
  // USERS
  // ============================================

  static final List<User> users = [
    User(
      id: 'user-1',
      name: 'Alex Johnson',
      email: 'alex.johnson@bottlecrm.io',
      phone: '+1 (555) 123-4567',
      role: 'Sales Manager',
      avatar: null,
      isAdmin: true,
      createdAt: DateTime(2024, 1, 15),
      updatedAt: DateTime.now(),
    ),
    User(
      id: 'user-2',
      name: 'Sarah Williams',
      email: 'sarah.williams@bottlecrm.io',
      phone: '+1 (555) 234-5678',
      role: 'Account Executive',
      avatar: null,
      isAdmin: false,
      createdAt: DateTime(2024, 2, 1),
      updatedAt: DateTime.now(),
    ),
    User(
      id: 'user-3',
      name: 'Michael Chen',
      email: 'michael.chen@bottlecrm.io',
      phone: '+1 (555) 345-6789',
      role: 'Sales Representative',
      avatar: null,
      isAdmin: false,
      createdAt: DateTime(2024, 3, 10),
      updatedAt: DateTime.now(),
    ),
    User(
      id: 'user-4',
      name: 'Emily Davis',
      email: 'emily.davis@bottlecrm.io',
      phone: '+1 (555) 456-7890',
      role: 'Business Development',
      avatar: null,
      isAdmin: false,
      createdAt: DateTime(2024, 4, 5),
      updatedAt: DateTime.now(),
    ),
  ];

  static User get currentUser => users[0];

  // ============================================
  // LEADS
  // ============================================

  static final List<Lead> leads = [
    Lead(
      id: 'lead-1',
      firstName: 'John',
      lastName: 'Smith',
      companyName: 'TechCorp Industries',
      email: 'john.smith@techcorp.com',
      phone: '+1 (555) 111-2222',
      status: LeadStatus.inProcess,
      source: LeadSource.email,
      rating: LeadRating.hot,
      tags: ['Enterprise', 'Software'],
      description: 'Very interested in our enterprise solution. Follow up scheduled for next week.',
      createdAt: DateTime.now().subtract(const Duration(days: 5)),
      updatedAt: DateTime.now().subtract(const Duration(hours: 2)),
    ),
    Lead(
      id: 'lead-2',
      firstName: 'Emma',
      lastName: 'Wilson',
      companyName: 'Global Solutions Ltd',
      email: 'emma.wilson@globalsolutions.com',
      phone: '+1 (555) 222-3333',
      status: LeadStatus.inProcess,
      source: LeadSource.partner,
      rating: LeadRating.warm,
      tags: ['SMB', 'Consulting'],
      description: 'Referred by existing client. Initial call went well.',
      createdAt: DateTime.now().subtract(const Duration(days: 3)),
      updatedAt: DateTime.now().subtract(const Duration(days: 1)),
    ),
    Lead(
      id: 'lead-3',
      firstName: 'Robert',
      lastName: 'Martinez',
      companyName: 'Innovate Labs',
      email: 'robert.m@innovatelabs.io',
      phone: '+1 (555) 333-4444',
      status: LeadStatus.assigned,
      source: LeadSource.publicRelations,
      rating: LeadRating.hot,
      tags: ['Startup', 'Technology'],
      description: 'Connected on LinkedIn, interested in demo.',
      createdAt: DateTime.now().subtract(const Duration(days: 1)),
      updatedAt: DateTime.now().subtract(const Duration(hours: 5)),
    ),
    Lead(
      id: 'lead-4',
      firstName: 'Lisa',
      lastName: 'Anderson',
      companyName: 'Metro Financial',
      email: 'l.anderson@metrofinancial.com',
      phone: '+1 (555) 444-5555',
      status: LeadStatus.inProcess,
      source: LeadSource.campaign,
      rating: LeadRating.warm,
      tags: ['Finance', 'Enterprise'],
      description: 'Met at FinTech Summit. Ready for proposal.',
      createdAt: DateTime.now().subtract(const Duration(days: 7)),
      updatedAt: DateTime.now().subtract(const Duration(days: 2)),
    ),
    Lead(
      id: 'lead-5',
      firstName: 'David',
      lastName: 'Thompson',
      companyName: 'Retail Plus',
      email: 'david.t@retailplus.com',
      phone: '+1 (555) 555-6666',
      status: LeadStatus.inProcess,
      source: LeadSource.call,
      rating: LeadRating.cold,
      tags: ['Retail', 'SMB'],
      description: 'Initial call completed. Scheduling follow-up.',
      createdAt: DateTime.now().subtract(const Duration(days: 10)),
      updatedAt: DateTime.now().subtract(const Duration(days: 3)),
    ),
    Lead(
      id: 'lead-6',
      firstName: 'Jennifer',
      lastName: 'Lee',
      companyName: 'HealthFirst',
      email: 'jlee@healthfirst.org',
      phone: '+1 (555) 666-7777',
      status: LeadStatus.assigned,
      source: LeadSource.email,
      rating: LeadRating.hot,
      tags: ['Healthcare', 'Enterprise'],
      description: 'Downloaded whitepaper, requesting demo.',
      createdAt: DateTime.now().subtract(const Duration(hours: 12)),
      updatedAt: DateTime.now().subtract(const Duration(hours: 12)),
    ),
    Lead(
      id: 'lead-7',
      firstName: 'Mark',
      lastName: 'Brown',
      companyName: 'EduTech Solutions',
      email: 'mark.brown@edutech.edu',
      phone: '+1 (555) 777-8888',
      status: LeadStatus.closed,
      source: LeadSource.partner,
      rating: LeadRating.warm,
      tags: ['Education', 'Non-profit'],
      description: 'Budget constraints. May revisit next quarter.',
      createdAt: DateTime.now().subtract(const Duration(days: 30)),
      updatedAt: DateTime.now().subtract(const Duration(days: 5)),
    ),
    Lead(
      id: 'lead-8',
      firstName: 'Amanda',
      lastName: 'Garcia',
      companyName: 'Creative Agency Co',
      email: 'amanda@creativeagency.co',
      phone: '+1 (555) 888-9999',
      status: LeadStatus.inProcess,
      source: LeadSource.publicRelations,
      rating: LeadRating.warm,
      tags: ['Agency', 'Creative'],
      description: 'Interested in team collaboration features.',
      createdAt: DateTime.now().subtract(const Duration(days: 4)),
      updatedAt: DateTime.now().subtract(const Duration(days: 1)),
    ),
  ];

  // ============================================
  // DEALS
  // ============================================

  static final List<Deal> deals = [
    Deal(
      id: 'deal-1',
      title: 'Enterprise Software Package',
      value: 75000,
      stage: DealStage.negotiation,
      probability: 75,
      closeDate: DateTime.now().add(const Duration(days: 5)),
      leadId: 'lead-1',
      companyName: 'TechCorp Industries',
      products: [
        const DealProduct(id: 'prod-1', name: 'Enterprise License', quantity: 1, unitPrice: 50000),
        const DealProduct(id: 'prod-2', name: 'Premium Support', quantity: 1, unitPrice: 25000),
      ],
      assignedTo: 'user-1',
      priority: Priority.high,
      labels: ['Enterprise', 'Q4 Target'],
      createdAt: DateTime.now().subtract(const Duration(days: 20)),
      updatedAt: DateTime.now().subtract(const Duration(hours: 6)),
    ),
    Deal(
      id: 'deal-2',
      title: 'Global Solutions Implementation',
      value: 45000,
      stage: DealStage.proposal,
      probability: 50,
      closeDate: DateTime.now().add(const Duration(days: 14)),
      leadId: 'lead-2',
      companyName: 'Global Solutions Ltd',
      products: [
        const DealProduct(id: 'prod-3', name: 'Business License', quantity: 5, unitPrice: 8000),
        const DealProduct(id: 'prod-4', name: 'Training Package', quantity: 1, unitPrice: 5000),
      ],
      assignedTo: 'user-2',
      priority: Priority.medium,
      labels: ['Implementation'],
      createdAt: DateTime.now().subtract(const Duration(days: 15)),
      updatedAt: DateTime.now().subtract(const Duration(days: 2)),
    ),
    Deal(
      id: 'deal-3',
      title: 'Metro Financial CRM Upgrade',
      value: 120000,
      stage: DealStage.qualified,
      probability: 25,
      closeDate: DateTime.now().add(const Duration(days: 30)),
      leadId: 'lead-4',
      companyName: 'Metro Financial',
      products: [
        const DealProduct(id: 'prod-5', name: 'Enterprise Suite', quantity: 1, unitPrice: 100000),
        const DealProduct(id: 'prod-6', name: 'Data Migration', quantity: 1, unitPrice: 20000),
      ],
      assignedTo: 'user-3',
      priority: Priority.high,
      labels: ['Enterprise', 'Finance'],
      createdAt: DateTime.now().subtract(const Duration(days: 10)),
      updatedAt: DateTime.now().subtract(const Duration(days: 1)),
    ),
    Deal(
      id: 'deal-4',
      title: 'Retail Plus Starter Package',
      value: 15000,
      stage: DealStage.prospecting,
      probability: 10,
      closeDate: DateTime.now().add(const Duration(days: 45)),
      leadId: 'lead-5',
      companyName: 'Retail Plus',
      products: [
        const DealProduct(id: 'prod-7', name: 'Starter License', quantity: 3, unitPrice: 5000),
      ],
      assignedTo: 'user-2',
      priority: Priority.low,
      labels: ['SMB', 'Retail'],
      createdAt: DateTime.now().subtract(const Duration(days: 5)),
      updatedAt: DateTime.now().subtract(const Duration(days: 3)),
    ),
    Deal(
      id: 'deal-5',
      title: 'HealthFirst Integration',
      value: 85000,
      stage: DealStage.proposal,
      probability: 50,
      closeDate: DateTime.now().add(const Duration(days: 21)),
      leadId: 'lead-6',
      companyName: 'HealthFirst',
      products: [
        const DealProduct(id: 'prod-8', name: 'Healthcare Module', quantity: 1, unitPrice: 60000),
        const DealProduct(id: 'prod-9', name: 'API Integration', quantity: 1, unitPrice: 25000),
      ],
      assignedTo: 'user-4',
      priority: Priority.high,
      labels: ['Healthcare', 'Priority'],
      createdAt: DateTime.now().subtract(const Duration(days: 8)),
      updatedAt: DateTime.now().subtract(const Duration(hours: 12)),
    ),
    Deal(
      id: 'deal-6',
      title: 'Creative Agency Subscription',
      value: 24000,
      stage: DealStage.qualified,
      probability: 25,
      closeDate: DateTime.now().add(const Duration(days: 28)),
      leadId: 'lead-8',
      companyName: 'Creative Agency Co',
      products: [
        const DealProduct(id: 'prod-10', name: 'Team License', quantity: 12, unitPrice: 2000),
      ],
      assignedTo: 'user-3',
      priority: Priority.medium,
      labels: ['Subscription', 'Agency'],
      createdAt: DateTime.now().subtract(const Duration(days: 6)),
      updatedAt: DateTime.now().subtract(const Duration(days: 2)),
    ),
    Deal(
      id: 'deal-7',
      title: 'Innovate Labs Pilot',
      value: 35000,
      stage: DealStage.negotiation,
      probability: 80,
      closeDate: DateTime.now().add(const Duration(days: 3)),
      leadId: 'lead-3',
      companyName: 'Innovate Labs',
      products: [
        const DealProduct(id: 'prod-11', name: 'Pilot Program', quantity: 1, unitPrice: 35000),
      ],
      assignedTo: 'user-1',
      priority: Priority.high,
      labels: ['Startup', 'Fast Track'],
      createdAt: DateTime.now().subtract(const Duration(days: 12)),
      updatedAt: DateTime.now().subtract(const Duration(hours: 3)),
    ),
    Deal(
      id: 'deal-8',
      title: 'EduTech Annual Contract',
      value: 28000,
      stage: DealStage.closedLost,
      probability: 0,
      closeDate: DateTime.now().subtract(const Duration(days: 5)),
      leadId: 'lead-7',
      companyName: 'EduTech Solutions',
      products: [
        const DealProduct(id: 'prod-12', name: 'Education License', quantity: 1, unitPrice: 28000),
      ],
      assignedTo: 'user-1',
      priority: Priority.medium,
      labels: ['Education'],
      notes: 'Lost due to budget constraints. Follow up next quarter.',
      createdAt: DateTime.now().subtract(const Duration(days: 25)),
      updatedAt: DateTime.now().subtract(const Duration(days: 5)),
    ),
  ];

  // ============================================
  // TASKS
  // ============================================

  static final List<Task> tasks = [
    Task(
      id: 'task-1',
      title: 'Follow up with TechCorp',
      description: 'Send updated proposal with revised pricing',
      dueDate: DateTime.now().add(const Duration(hours: 2)),
      status: TaskStatus.inProgress,
      priority: Priority.high,
      relatedTo: RelatedEntity(id: 'deal-1', type: RelatedEntityType.opportunity, title: 'Enterprise Software Package'),
      createdAt: DateTime.now().subtract(const Duration(days: 1)),
      updatedAt: DateTime.now(),
    ),
    Task(
      id: 'task-2',
      title: 'Schedule demo for HealthFirst',
      description: 'Coordinate with technical team for product demo',
      dueDate: DateTime.now(),
      status: TaskStatus.newTask,
      priority: Priority.high,
      relatedTo: RelatedEntity(id: 'lead-6', type: RelatedEntityType.lead, title: 'Jennifer Lee'),
      createdAt: DateTime.now().subtract(const Duration(days: 2)),
      updatedAt: DateTime.now(),
    ),
    Task(
      id: 'task-3',
      title: 'Prepare quarterly report',
      description: 'Compile sales data for Q4 review',
      dueDate: DateTime.now().subtract(const Duration(days: 1)),
      status: TaskStatus.newTask,
      priority: Priority.medium,
      relatedTo: null,
      createdAt: DateTime.now().subtract(const Duration(days: 5)),
      updatedAt: DateTime.now().subtract(const Duration(days: 1)),
    ),
    Task(
      id: 'task-4',
      title: 'Call Global Solutions',
      description: 'Discuss implementation timeline',
      dueDate: DateTime.now(),
      status: TaskStatus.completed,
      priority: Priority.medium,
      relatedTo: RelatedEntity(id: 'lead-2', type: RelatedEntityType.lead, title: 'Emma Wilson'),
      createdAt: DateTime.now().subtract(const Duration(days: 3)),
      updatedAt: DateTime.now().subtract(const Duration(hours: 4)),
    ),
    Task(
      id: 'task-5',
      title: 'Send contract to Innovate Labs',
      description: 'Final contract ready for signature',
      dueDate: DateTime.now().add(const Duration(days: 1)),
      status: TaskStatus.newTask,
      priority: Priority.high,
      relatedTo: RelatedEntity(id: 'deal-7', type: RelatedEntityType.opportunity, title: 'Innovate Labs Pilot'),
      createdAt: DateTime.now().subtract(const Duration(days: 1)),
      updatedAt: DateTime.now(),
    ),
    Task(
      id: 'task-6',
      title: 'Update CRM notes for Retail Plus',
      description: 'Document latest conversation details',
      dueDate: DateTime.now().add(const Duration(days: 3)),
      status: TaskStatus.newTask,
      priority: Priority.low,
      relatedTo: RelatedEntity(id: 'lead-5', type: RelatedEntityType.lead, title: 'David Thompson'),
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    ),
    Task(
      id: 'task-7',
      title: 'Review Metro Financial requirements',
      description: 'Analyze technical requirements document',
      dueDate: DateTime.now().add(const Duration(days: 2)),
      status: TaskStatus.inProgress,
      priority: Priority.medium,
      relatedTo: RelatedEntity(id: 'deal-3', type: RelatedEntityType.opportunity, title: 'Metro Financial CRM Upgrade'),
      createdAt: DateTime.now().subtract(const Duration(days: 2)),
      updatedAt: DateTime.now().subtract(const Duration(days: 1)),
    ),
    Task(
      id: 'task-8',
      title: 'Team sync meeting',
      description: 'Weekly sales team standup',
      dueDate: DateTime.now().add(const Duration(days: 4)),
      status: TaskStatus.newTask,
      priority: Priority.low,
      relatedTo: null,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    ),
  ];

  // ============================================
  // ACTIVITIES
  // ============================================

  static final List<Activity> activities = [
    Activity(
      id: 'activity-1',
      type: ActivityType.stageChange,
      title: 'Deal moved to Negotiation',
      description: 'Enterprise Software Package advanced to negotiation stage',
      timestamp: DateTime.now().subtract(const Duration(hours: 2)),
      userId: 'user-1',
      userName: 'Alex Johnson',
      relatedTo: RelatedEntity(id: 'deal-1', type: RelatedEntityType.opportunity, title: 'Enterprise Software Package'),
    ),
    Activity(
      id: 'activity-2',
      type: ActivityType.call,
      title: 'Call with TechCorp',
      description: 'Discussed pricing and implementation timeline',
      timestamp: DateTime.now().subtract(const Duration(hours: 5)),
      userId: 'user-1',
      userName: 'Alex Johnson',
      relatedTo: RelatedEntity(id: 'lead-1', type: RelatedEntityType.lead, title: 'John Smith'),
    ),
    Activity(
      id: 'activity-3',
      type: ActivityType.email,
      title: 'Proposal sent',
      description: 'Sent updated proposal document to Global Solutions',
      timestamp: DateTime.now().subtract(const Duration(hours: 8)),
      userId: 'user-2',
      userName: 'Sarah Williams',
      relatedTo: RelatedEntity(id: 'deal-2', type: RelatedEntityType.opportunity, title: 'Global Solutions Implementation'),
    ),
    Activity(
      id: 'activity-4',
      type: ActivityType.leadCreated,
      title: 'New lead created',
      description: 'Jennifer Lee from HealthFirst added',
      timestamp: DateTime.now().subtract(const Duration(hours: 12)),
      userId: 'user-4',
      userName: 'Emily Davis',
      relatedTo: RelatedEntity(id: 'lead-6', type: RelatedEntityType.lead, title: 'Jennifer Lee'),
    ),
    Activity(
      id: 'activity-5',
      type: ActivityType.meeting,
      title: 'Demo meeting',
      description: 'Product demonstration for Innovate Labs team',
      timestamp: DateTime.now().subtract(const Duration(days: 1)),
      userId: 'user-1',
      userName: 'Alex Johnson',
      relatedTo: RelatedEntity(id: 'lead-3', type: RelatedEntityType.lead, title: 'Robert Martinez'),
    ),
    Activity(
      id: 'activity-6',
      type: ActivityType.note,
      title: 'Note added',
      description: 'Added follow-up notes from discovery call',
      timestamp: DateTime.now().subtract(const Duration(days: 1, hours: 4)),
      userId: 'user-3',
      userName: 'Michael Chen',
      relatedTo: RelatedEntity(id: 'lead-4', type: RelatedEntityType.lead, title: 'Lisa Anderson'),
    ),
    Activity(
      id: 'activity-7',
      type: ActivityType.dealWon,
      title: 'Deal Won!',
      description: 'Successfully closed contract with prior customer',
      timestamp: DateTime.now().subtract(const Duration(days: 2)),
      userId: 'user-2',
      userName: 'Sarah Williams',
      relatedTo: null,
    ),
    Activity(
      id: 'activity-8',
      type: ActivityType.taskCompleted,
      title: 'Task completed',
      description: 'Finished proposal review',
      timestamp: DateTime.now().subtract(const Duration(days: 2, hours: 6)),
      userId: 'user-1',
      userName: 'Alex Johnson',
      relatedTo: RelatedEntity(id: 'deal-1', type: RelatedEntityType.opportunity, title: 'Enterprise Software Package'),
    ),
  ];

  // ============================================
  // NOTIFICATIONS
  // ============================================

  static final List<AppNotification> notifications = [
    AppNotification(
      id: 'notif-1',
      userId: 'user-1',
      type: NotificationType.taskDue,
      title: 'Task Due Soon',
      message: 'Follow up with TechCorp is due in 2 hours',
      read: false,
      relatedTo: RelatedEntity(id: 'task-1', type: RelatedEntityType.opportunity, title: 'Enterprise Software Package'),
      timestamp: DateTime.now().subtract(const Duration(minutes: 30)),
    ),
    AppNotification(
      id: 'notif-2',
      userId: 'user-1',
      type: NotificationType.dealStageChanged,
      title: 'Deal Updated',
      message: 'Innovate Labs Pilot moved to negotiation',
      read: false,
      relatedTo: RelatedEntity(id: 'deal-7', type: RelatedEntityType.opportunity, title: 'Innovate Labs Pilot'),
      timestamp: DateTime.now().subtract(const Duration(hours: 2)),
    ),
    AppNotification(
      id: 'notif-3',
      userId: 'user-1',
      type: NotificationType.leadAssigned,
      title: 'New Lead Assigned',
      message: 'Robert Martinez from Innovate Labs has been assigned to you',
      read: true,
      relatedTo: RelatedEntity(id: 'lead-3', type: RelatedEntityType.lead, title: 'Robert Martinez'),
      timestamp: DateTime.now().subtract(const Duration(days: 1)),
    ),
    AppNotification(
      id: 'notif-4',
      userId: 'user-1',
      type: NotificationType.dealWon,
      title: 'Congratulations!',
      message: 'Sarah closed a deal worth \$50,000',
      read: true,
      relatedTo: null,
      timestamp: DateTime.now().subtract(const Duration(days: 2)),
    ),
  ];

  // ============================================
  // DASHBOARD KPIs
  // ============================================

  static double get totalSales {
    return deals
        .where((d) => d.stage == DealStage.closedWon)
        .fold(0.0, (sum, deal) => sum + deal.value);
  }

  static int get openDeals {
    return deals.where((d) => !d.stage.isClosed).length;
  }

  static double get pipelineValue {
    return deals
        .where((d) => !d.stage.isClosed)
        .fold(0.0, (sum, deal) => sum + deal.value);
  }

  static double get conversionRate {
    final won = deals.where((d) => d.stage == DealStage.closedWon).length;
    final total = deals.where((d) => d.stage.isClosed).length;
    if (total == 0) return 0;
    return (won / total) * 100;
  }

  static int get completedTasksCount {
    return tasks.where((t) => t.completed).length;
  }

  static int get totalTasksCount => tasks.length;

  static double get taskCompletionRate {
    if (tasks.isEmpty) return 0;
    return (completedTasksCount / totalTasksCount) * 100;
  }

  static List<Deal> get dealsClosingSoon {
    return deals
        .where((d) => !d.stage.isClosed && d.isClosingSoon)
        .toList()
      ..sort((a, b) => (a.closeDate ?? DateTime.now())
          .compareTo(b.closeDate ?? DateTime.now()));
  }

  static List<Task> get todaysTasks {
    return tasks
        .where((t) => !t.completed && (t.isDueToday || t.isOverdue))
        .toList()
      ..sort((a, b) => (a.dueDate ?? DateTime.now()).compareTo(b.dueDate ?? DateTime.now()));
  }

  static List<Activity> get recentActivities {
    return List.from(activities)
      ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
  }

  // ============================================
  // SALES CHART DATA (Last 6 months)
  // ============================================

  static List<Map<String, dynamic>> get salesChartData => [
    {'month': 'Jul', 'value': 42000},
    {'month': 'Aug', 'value': 58000},
    {'month': 'Sep', 'value': 49000},
    {'month': 'Oct', 'value': 72000},
    {'month': 'Nov', 'value': 85000},
    {'month': 'Dec', 'value': 95000},
  ];

  // ============================================
  // PIPELINE FUNNEL DATA
  // ============================================

  static Map<DealStage, List<Deal>> get dealsByStage {
    final map = <DealStage, List<Deal>>{};
    for (final stage in DealStage.pipelineStages) {
      map[stage] = deals.where((d) => d.stage == stage).toList();
    }
    return map;
  }

  static Map<DealStage, double> get pipelineValueByStage {
    final map = <DealStage, double>{};
    for (final stage in DealStage.pipelineStages) {
      map[stage] = deals
          .where((d) => d.stage == stage)
          .fold(0.0, (sum, deal) => sum + deal.value);
    }
    return map;
  }

  // ============================================
  // HELPER METHODS
  // ============================================

  static User? getUserById(String id) {
    try {
      return users.firstWhere((u) => u.id == id);
    } catch (_) {
      return null;
    }
  }

  static Lead? getLeadById(String id) {
    try {
      return leads.firstWhere((l) => l.id == id);
    } catch (_) {
      return null;
    }
  }

  static Deal? getDealById(String id) {
    try {
      return deals.firstWhere((d) => d.id == id);
    } catch (_) {
      return null;
    }
  }

  static Task? getTaskById(String id) {
    try {
      return tasks.firstWhere((t) => t.id == id);
    } catch (_) {
      return null;
    }
  }

  static List<Activity> getActivitiesForLead(String leadId) {
    return activities
        .where((a) =>
            a.relatedTo?.type == RelatedEntityType.lead &&
            a.relatedTo?.id == leadId)
        .toList()
      ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
  }

  static List<Activity> getActivitiesForDeal(String dealId) {
    return activities
        .where((a) =>
            a.relatedTo?.type == RelatedEntityType.opportunity &&
            a.relatedTo?.id == dealId)
        .toList()
      ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
  }
}
