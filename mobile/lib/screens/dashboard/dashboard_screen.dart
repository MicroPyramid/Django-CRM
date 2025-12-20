import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:intl/intl.dart';
import '../../core/theme/theme.dart';
import '../../data/models/dashboard_data.dart';
import '../../providers/auth_provider.dart';
import '../../providers/dashboard_provider.dart';
import '../../routes/app_router.dart';

/// Dashboard Screen
/// Main screen with KPIs, charts, pipeline, tasks, and activity feed
class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    // Fetch dashboard data when screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(dashboardProvider.notifier).fetchDashboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    final dashboardState = ref.watch(dashboardProvider);
    final authState = ref.watch(authProvider);
    final userName = authState.user?.displayName ?? 'User';
    final currencySymbol = authState.selectedOrganization?.currencySymbol ?? '\$';
    final currencyFormat = NumberFormat.currency(symbol: currencySymbol, decimalDigits: 0);
    final compactCurrencyFormat = NumberFormat.compactCurrency(symbol: currencySymbol, decimalDigits: 1);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      body: RefreshIndicator(
        onRefresh: () => ref.read(dashboardProvider.notifier).refresh(),
        child: CustomScrollView(
          slivers: [
            // App Bar
            SliverAppBar(
              expandedHeight: 100,
              floating: false,
              pinned: true,
              backgroundColor: AppColors.surface,
              flexibleSpace: FlexibleSpaceBar(
                titlePadding: const EdgeInsets.only(left: 16, bottom: 16),
                title: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Good ${_getGreeting()},',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                        fontSize: 11,
                      ),
                    ),
                    Text(
                      userName.split(' ').first,
                      style: AppTypography.h3.copyWith(fontSize: 18),
                    ),
                  ],
                ),
              ),
            ),

            // Content
            SliverToBoxAdapter(
              child: _buildContent(dashboardState, currencyFormat, compactCurrencyFormat),
            ),
          ],
        ),
      ),
      floatingActionButton: _buildExpandableFAB(context),
    );
  }

  Widget _buildContent(DashboardState dashboardState, NumberFormat currencyFormat, NumberFormat compactCurrencyFormat) {
    if (dashboardState.isLoading && dashboardState.data == null) {
      return const SizedBox(
        height: 400,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (dashboardState.error != null && dashboardState.data == null) {
      return SizedBox(
        height: 400,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(LucideIcons.alertCircle, size: 48, color: Colors.grey[400]),
              const SizedBox(height: 16),
              Text(
                'Failed to load dashboard',
                style: AppTypography.label.copyWith(color: Colors.grey[600]),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => ref.read(dashboardProvider.notifier).refresh(),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    final data = dashboardState.data ?? const DashboardData();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),

        // KPI Cards
        _buildKpiSection(data, compactCurrencyFormat),

        const SizedBox(height: 16),

        // Urgent Metrics
        if (_hasUrgentItems(data.urgentCounts)) ...[
          _buildUrgentSection(data.urgentCounts),
          const SizedBox(height: 16),
        ],

        // Pipeline Overview
        if (data.pipelineByStage.isNotEmpty) ...[
          _buildPipelineSection(data.pipelineByStage, currencyFormat),
          const SizedBox(height: 16),
        ],

        // Hot Leads
        if (data.hotLeads.isNotEmpty) ...[
          _buildHotLeadsSection(data.hotLeads),
          const SizedBox(height: 16),
        ],

        // Today's Tasks
        _buildTasksSection(data.tasks),

        const SizedBox(height: 16),

        // Recent Activity
        if (data.activities.isNotEmpty) ...[
          _buildActivitySection(data.activities),
        ],

        const SizedBox(height: 80),
      ],
    );
  }

  bool _hasUrgentItems(UrgentCounts counts) {
    return counts.overdueTasks > 0 ||
        counts.tasksDueToday > 0 ||
        counts.followupsToday > 0 ||
        counts.hotLeads > 0;
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'morning';
    if (hour < 17) return 'afternoon';
    return 'evening';
  }

  Widget _buildKpiSection(DashboardData data, NumberFormat currencyFormat) {
    final textScale = MediaQuery.textScalerOf(context).scale(1.0);
    final kpiHeight = 70 + (30 * textScale); // Base 70 + scaled text area

    return SizedBox(
      height: kpiHeight,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        children: [
          _KpiCard(
            title: 'Pipeline',
            value: currencyFormat.format(data.revenueMetrics.pipelineValue),
            icon: LucideIcons.dollarSign,
            color: AppColors.success500,
          ),
          _KpiCard(
            title: 'Open Deals',
            value: data.opportunitiesCount.toString(),
            icon: LucideIcons.briefcase,
            color: AppColors.primary500,
          ),
          _KpiCard(
            title: 'Leads',
            value: data.leadsCount.toString(),
            icon: LucideIcons.users,
            color: AppColors.warning500,
          ),
          _KpiCard(
            title: 'Conversion',
            value: '${data.revenueMetrics.conversionRate.toStringAsFixed(0)}%',
            icon: LucideIcons.target,
            color: AppColors.purple500,
          ),
        ],
      ),
    );
  }

  Widget _buildUrgentSection(UrgentCounts counts) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.warning50,
          borderRadius: AppLayout.borderRadiusMd,
          border: Border.all(color: AppColors.warning200),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(LucideIcons.alertTriangle, size: 16, color: AppColors.warning600),
                const SizedBox(width: 6),
                Text(
                  'Needs Attention',
                  style: AppTypography.labelSmall.copyWith(color: AppColors.warning700),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 12,
              runSpacing: 6,
              children: [
                if (counts.overdueTasks > 0)
                  _UrgentBadge(
                    label: 'Overdue',
                    count: counts.overdueTasks,
                    color: AppColors.danger500,
                  ),
                if (counts.tasksDueToday > 0)
                  _UrgentBadge(
                    label: 'Due Today',
                    count: counts.tasksDueToday,
                    color: AppColors.warning500,
                  ),
                if (counts.followupsToday > 0)
                  _UrgentBadge(
                    label: 'Follow-ups',
                    count: counts.followupsToday,
                    color: AppColors.primary500,
                  ),
                if (counts.hotLeads > 0)
                  _UrgentBadge(
                    label: 'Hot Leads',
                    count: counts.hotLeads,
                    color: AppColors.success500,
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPipelineSection(List<PipelineStage> stages, NumberFormat currencyFormat) {
    // Only show active pipeline stages (not closed)
    final activeStages = stages.where((s) =>
        !s.code.contains('CLOSED') && s.value > 0).toList();

    if (activeStages.isEmpty) {
      return const SizedBox.shrink();
    }

    final maxValue = activeStages.map((s) => s.value).reduce((a, b) => a > b ? a : b);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusMd,
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Pipeline Overview', style: AppTypography.labelSmall),
            const SizedBox(height: 10),
            ...activeStages.map((stage) {
              final percentage = maxValue > 0 ? stage.value / maxValue : 0;
              final stageColor = _getStageColor(stage.code);

              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: stageColor,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    SizedBox(
                      width: 80,
                      child: Text(
                        stage.label,
                        style: AppTypography.bodySmall.copyWith(fontSize: 11),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(3),
                        child: LinearProgressIndicator(
                          value: percentage.toDouble(),
                          backgroundColor: AppColors.gray100,
                          valueColor: AlwaysStoppedAnimation(stageColor),
                          minHeight: 6,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      width: 70,
                      child: Text(
                        currencyFormat.format(stage.value),
                        style: AppTypography.bodySmall.copyWith(
                          fontWeight: FontWeight.w600,
                          fontSize: 11,
                        ),
                        textAlign: TextAlign.right,
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Color _getStageColor(String code) {
    switch (code) {
      case 'PROSPECTING':
        return AppColors.gray400;
      case 'QUALIFICATION':
        return AppColors.primary400;
      case 'PROPOSAL':
        return AppColors.warning400;
      case 'NEGOTIATION':
        return AppColors.purple400;
      case 'CLOSED_WON':
        return AppColors.success500;
      case 'CLOSED_LOST':
        return AppColors.danger500;
      default:
        return AppColors.gray400;
    }
  }

  Widget _buildHotLeadsSection(List<HotLead> leads) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Hot Leads', style: AppTypography.labelSmall),
              GestureDetector(
                onTap: () => context.go(AppRoutes.leads),
                child: Text(
                  'See All',
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.primary600,
                    fontSize: 11,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 76,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            itemCount: leads.take(5).length,
            itemBuilder: (context, index) {
              final lead = leads[index];
              return GestureDetector(
                onTap: () => context.push('/leads/${lead.id}'),
                child: Container(
                  width: 160,
                  margin: const EdgeInsets.only(right: 8),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: AppLayout.borderRadiusSm,
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              lead.fullName,
                              style: AppTypography.labelSmall,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                            decoration: BoxDecoration(
                              color: AppColors.danger100,
                              borderRadius: BorderRadius.circular(3),
                            ),
                            child: Text(
                              'HOT',
                              style: TextStyle(
                                fontSize: 8,
                                fontWeight: FontWeight.w600,
                                color: AppColors.danger600,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      if (lead.company != null)
                        Text(
                          lead.company!,
                          style: AppTypography.bodySmall.copyWith(
                            color: AppColors.textSecondary,
                            fontSize: 11,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      const Spacer(),
                      if (lead.nextFollowUp != null)
                        Text(
                          'Follow-up: ${DateFormat.MMMd().format(lead.nextFollowUp!)}',
                          style: AppTypography.bodySmall.copyWith(
                            color: AppColors.warning600,
                            fontSize: 10,
                          ),
                        ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildTasksSection(List<DashboardTask> tasks) {
    final upcomingTasks = tasks.where((t) => !t.isCompleted).take(5).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Upcoming Tasks', style: AppTypography.labelSmall),
              GestureDetector(
                onTap: () => context.go(AppRoutes.tasks),
                child: Text(
                  'See All',
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.primary600,
                    fontSize: 11,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: AppLayout.borderRadiusMd,
              border: Border.all(color: AppColors.border),
            ),
            child: upcomingTasks.isEmpty
                ? Padding(
                    padding: const EdgeInsets.all(16),
                    child: Center(
                      child: Column(
                        children: [
                          Icon(LucideIcons.checkCircle, size: 24, color: Colors.grey[300]),
                          const SizedBox(height: 6),
                          Text(
                            'No upcoming tasks',
                            style: AppTypography.bodySmall.copyWith(
                              color: AppColors.textTertiary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  )
                : Column(
                    children: upcomingTasks.asMap().entries.map((entry) {
                      final index = entry.key;
                      final task = entry.value;
                      return _TaskItem(
                        task: task,
                        showDivider: index < upcomingTasks.length - 1,
                      );
                    }).toList(),
                  ),
          ),
        ),
      ],
    );
  }

  Widget _buildActivitySection(List<DashboardActivity> activities) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Text('Recent Activity', style: AppTypography.labelSmall),
        ),
        const SizedBox(height: 8),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: AppLayout.borderRadiusMd,
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              children: activities.take(5).toList().asMap().entries.map((entry) {
                final index = entry.key;
                final activity = entry.value;
                return _ActivityItem(
                  activity: activity,
                  showDivider: index < activities.length - 1 && index < 4,
                );
              }).toList(),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildExpandableFAB(BuildContext context) {
    return FloatingActionButton(
      onPressed: () {
        showModalBottomSheet(
          context: context,
          builder: (context) => Container(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ListTile(
                  leading: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: AppColors.primary100,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      LucideIcons.userPlus,
                      color: AppColors.primary600,
                      size: 20,
                    ),
                  ),
                  title: const Text('Add Lead'),
                  subtitle: const Text('Create a new lead'),
                  onTap: () {
                    context.pop();
                    context.push(AppRoutes.leadCreate);
                  },
                ),
                ListTile(
                  leading: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: AppColors.success100,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      LucideIcons.plusCircle,
                      color: AppColors.success600,
                      size: 20,
                    ),
                  ),
                  title: const Text('Add Deal'),
                  subtitle: const Text('Create a new deal'),
                  onTap: () {
                    context.pop();
                    // Navigate to deal create
                  },
                ),
                ListTile(
                  leading: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: AppColors.warning100,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      LucideIcons.checkSquare,
                      color: AppColors.warning600,
                      size: 20,
                    ),
                  ),
                  title: const Text('Add Task'),
                  subtitle: const Text('Create a new task'),
                  onTap: () {
                    context.pop();
                    // Navigate to task create
                  },
                ),
              ],
            ),
          ),
        );
      },
      child: const Icon(LucideIcons.plus),
    );
  }
}

// KPI Card Widget
class _KpiCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _KpiCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final textScale = MediaQuery.textScalerOf(context).scale(1.0);
    final cardWidth = 100 + (25 * textScale); // Base 100 + scaled text area

    return Container(
      width: cardWidth,
      margin: const EdgeInsets.only(right: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppLayout.borderRadiusSm,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Icon(icon, size: 14, color: color),
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: AppTypography.label.copyWith(
              fontWeight: FontWeight.w700,
              fontSize: 15,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          Text(
            title,
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}

// Urgent Badge Widget
class _UrgentBadge extends StatelessWidget {
  final String label;
  final int count;
  final Color color;

  const _UrgentBadge({
    required this.label,
    required this.count,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                count.toString(),
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
              ),
              const SizedBox(width: 3),
              Text(
                label,
                style: TextStyle(
                  fontSize: 10,
                  color: color,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// Task Item
class _TaskItem extends StatelessWidget {
  final DashboardTask task;
  final bool showDivider;

  const _TaskItem({
    required this.task,
    this.showDivider = true,
  });

  Color _getPriorityColor() {
    switch (task.priority.toLowerCase()) {
      case 'urgent':
        return AppColors.purple500;
      case 'high':
        return AppColors.danger500;
      case 'medium':
        return AppColors.warning500;
      case 'low':
      default:
        return AppColors.success500;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          child: Row(
            children: [
              Container(
                width: 3,
                height: 32,
                decoration: BoxDecoration(
                  color: _getPriorityColor(),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      task.title,
                      style: AppTypography.body.copyWith(
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (task.relatedTo != null || task.dueDate != null)
                      Row(
                        children: [
                          if (task.relatedTo != null)
                            Flexible(
                              child: Text(
                                task.relatedTo!,
                                style: AppTypography.caption.copyWith(
                                  color: AppColors.textTertiary,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          if (task.relatedTo != null && task.dueDate != null)
                            Text(' • ', style: TextStyle(color: AppColors.gray300, fontSize: 12)),
                          if (task.dueDate != null)
                            Text(
                              DateFormat.MMMd().format(task.dueDate!),
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textTertiary,
                              ),
                            ),
                        ],
                      ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: _getPriorityColor().withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  task.priority,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: _getPriorityColor(),
                  ),
                ),
              ),
            ],
          ),
        ),
        if (showDivider) const Divider(height: 1, indent: 24),
      ],
    );
  }
}

// Activity Item
class _ActivityItem extends StatelessWidget {
  final DashboardActivity activity;
  final bool showDivider;

  const _ActivityItem({
    required this.activity,
    this.showDivider = true,
  });

  IconData _getActivityIcon() {
    switch (activity.activityType.toLowerCase()) {
      case 'create':
        return LucideIcons.plus;
      case 'update':
        return LucideIcons.edit;
      case 'delete':
        return LucideIcons.trash;
      case 'comment':
        return LucideIcons.messageSquare;
      case 'email':
        return LucideIcons.mail;
      case 'call':
        return LucideIcons.phone;
      default:
        return LucideIcons.activity;
    }
  }

  Color _getActivityColor() {
    switch (activity.activityType.toLowerCase()) {
      case 'create':
        return AppColors.success500;
      case 'update':
        return AppColors.primary500;
      case 'delete':
        return AppColors.danger500;
      case 'comment':
        return AppColors.warning500;
      default:
        return AppColors.gray500;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          child: Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: _getActivityColor().withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  _getActivityIcon(),
                  size: 14,
                  color: _getActivityColor(),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      activity.description,
                      style: AppTypography.body,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Row(
                      children: [
                        if (activity.userName != null) ...[
                          Flexible(
                            child: Text(
                              activity.userName!.split('@').first,
                              style: AppTypography.caption.copyWith(
                                fontWeight: FontWeight.w500,
                                color: AppColors.textSecondary,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          Text(' • ', style: TextStyle(color: AppColors.gray300, fontSize: 12)),
                        ],
                        Text(
                          activity.relativeTime,
                          style: AppTypography.caption.copyWith(
                            color: AppColors.textTertiary,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (showDivider) const Divider(height: 1, indent: 48),
      ],
    );
  }
}
