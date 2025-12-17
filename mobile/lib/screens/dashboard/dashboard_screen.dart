import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:intl/intl.dart';
import '../../core/theme/theme.dart';
import '../../data/mock/mock_data.dart';
import '../../data/models/models.dart';
import '../../routes/app_router.dart';
import '../../widgets/common/common.dart';

/// Dashboard Screen
/// Main screen with KPIs, charts, pipeline, tasks, and activity feed
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat.currency(symbol: '\$', decimalDigits: 0);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      body: CustomScrollView(
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
                    MockData.currentUser.firstName,
                    style: AppTypography.h3.copyWith(fontSize: 18),
                  ),
                ],
              ),
            ),
            actions: [
              IconButton(
                icon: Stack(
                  children: [
                    const Icon(LucideIcons.bell, size: 22),
                    Positioned(
                      right: 0,
                      top: 0,
                      child: Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(
                          color: AppColors.danger500,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                  ],
                ),
                onPressed: () {},
              ),
              const SizedBox(width: 8),
            ],
          ),

          // Content
          SliverToBoxAdapter(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 16),

                // KPI Cards
                _buildKpiSection(currencyFormat),

                const SizedBox(height: 24),

                // Sales Chart Section
                _buildSalesChartSection(),

                const SizedBox(height: 24),

                // Pipeline Overview
                _buildPipelineSection(currencyFormat),

                const SizedBox(height: 24),

                // Deals Closing Soon
                _buildDealsClosingSoon(context, currencyFormat),

                const SizedBox(height: 24),

                // Today's Tasks
                _buildTodaysTasks(context),

                const SizedBox(height: 24),

                // Recent Activity
                _buildRecentActivity(),

                const SizedBox(height: 100),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: _buildExpandableFAB(context),
    );
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'morning';
    if (hour < 17) return 'afternoon';
    return 'evening';
  }

  Widget _buildKpiSection(NumberFormat currencyFormat) {
    return SizedBox(
      height: 110,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        children: [
          _KpiCard(
            title: 'Total Sales',
            value: currencyFormat.format(MockData.totalSales),
            icon: LucideIcons.dollarSign,
            color: AppColors.success500,
            trend: '+12%',
            trendUp: true,
          ),
          _KpiCard(
            title: 'Open Deals',
            value: MockData.openDeals.toString(),
            icon: LucideIcons.briefcase,
            color: AppColors.primary500,
          ),
          _KpiCard(
            title: 'Pipeline',
            value: currencyFormat.format(MockData.pipelineValue),
            icon: LucideIcons.trendingUp,
            color: AppColors.warning500,
          ),
          _KpiCard(
            title: 'Conversion',
            value: '${MockData.conversionRate.toStringAsFixed(0)}%',
            icon: LucideIcons.target,
            color: AppColors.purple500,
            trend: '+5%',
            trendUp: true,
          ),
        ],
      ),
    );
  }

  Widget _buildSalesChartSection() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          // Sales Trend Chart
          Expanded(
            flex: 2,
            child: Container(
              height: 180,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: AppLayout.borderRadiusLg,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Sales Trend',
                    style: AppTypography.labelSmall.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Expanded(
                    child: _SimpleSalesChart(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 12),
          // Task Completion Ring
          Container(
            width: 120,
            height: 180,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: AppLayout.borderRadiusLg,
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  'Tasks',
                  style: AppTypography.labelSmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 12),
                _ProgressRing(
                  progress: MockData.taskCompletionRate / 100,
                  size: 70,
                ),
                const SizedBox(height: 8),
                Text(
                  '${MockData.completedTasksCount}/${MockData.totalTasksCount}',
                  style: AppTypography.caption,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPipelineSection(NumberFormat currencyFormat) {
    final pipelineData = MockData.pipelineValueByStage;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusLg,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Pipeline Overview',
              style: AppTypography.label,
            ),
            const SizedBox(height: 16),
            ...DealStage.pipelineStages.take(4).map((stage) {
              final value = pipelineData[stage] ?? 0;
              final maxValue = pipelineData.values.reduce((a, b) => a > b ? a : b);
              final percentage = maxValue > 0 ? value / maxValue : 0;

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: stage.color,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      width: 80,
                      child: Text(
                        stage.shortLabel,
                        style: AppTypography.caption,
                      ),
                    ),
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: percentage.toDouble(),
                          backgroundColor: AppColors.gray100,
                          valueColor: AlwaysStoppedAnimation(stage.color),
                          minHeight: 8,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    SizedBox(
                      width: 60,
                      child: Text(
                        currencyFormat.format(value),
                        style: AppTypography.numberSmall,
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

  Widget _buildDealsClosingSoon(BuildContext context, NumberFormat currencyFormat) {
    final deals = MockData.dealsClosingSoon.take(3).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Closing This Week', style: AppTypography.label),
              GestureDetector(
                onTap: () => context.go(AppRoutes.deals),
                child: Text(
                  'See All',
                  style: AppTypography.labelSmall.copyWith(
                    color: AppColors.primary600,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        if (deals.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: AppLayout.borderRadiusLg,
              ),
              child: Center(
                child: Text(
                  'No deals closing this week',
                  style: AppTypography.caption,
                ),
              ),
            ),
          )
        else
          SizedBox(
            height: 100,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: deals.length,
              itemBuilder: (context, index) {
                final deal = deals[index];
                return GestureDetector(
                  onTap: () => context.push('/deals/${deal.id}'),
                  child: Container(
                    width: 200,
                    margin: const EdgeInsets.only(right: 12),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: AppLayout.borderRadiusMd,
                      border: Border.all(color: AppColors.borderLight),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                deal.title,
                                style: AppTypography.label,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            PriorityBadge(priority: deal.priority, compact: true),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          deal.companyName,
                          style: AppTypography.caption,
                          maxLines: 1,
                        ),
                        const Spacer(),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              currencyFormat.format(deal.value),
                              style: AppTypography.numberSmall.copyWith(
                                color: AppColors.primary600,
                              ),
                            ),
                            Text(
                              '${deal.daysUntilClose}d',
                              style: AppTypography.caption.copyWith(
                                color: deal.daysUntilClose! <= 2
                                    ? AppColors.warning600
                                    : AppColors.textSecondary,
                              ),
                            ),
                          ],
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

  Widget _buildTodaysTasks(BuildContext context) {
    final tasks = MockData.todaysTasks.take(3).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("Today's Tasks", style: AppTypography.label),
              GestureDetector(
                onTap: () => context.go(AppRoutes.tasks),
                child: Text(
                  'See All',
                  style: AppTypography.labelSmall.copyWith(
                    color: AppColors.primary600,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: AppLayout.borderRadiusLg,
            ),
            child: tasks.isEmpty
                ? Padding(
                    padding: const EdgeInsets.all(24),
                    child: Center(
                      child: Text(
                        'No tasks for today',
                        style: AppTypography.caption,
                      ),
                    ),
                  )
                : Column(
                    children: tasks.asMap().entries.map((entry) {
                      final index = entry.key;
                      final task = entry.value;
                      return _TaskItem(
                        task: task,
                        showDivider: index < tasks.length - 1,
                      );
                    }).toList(),
                  ),
          ),
        ),
      ],
    );
  }

  Widget _buildRecentActivity() {
    final activities = MockData.recentActivities.take(4).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Text('Recent Activity', style: AppTypography.label),
        ),
        const SizedBox(height: 12),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: AppLayout.borderRadiusLg,
            ),
            child: Column(
              children: activities.asMap().entries.map((entry) {
                final index = entry.key;
                final activity = entry.value;
                return _ActivityItem(
                  activity: activity,
                  showDivider: index < activities.length - 1,
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
  final String? trend;
  final bool trendUp;

  const _KpiCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
    this.trend,
    this.trendUp = true,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 150,
      margin: const EdgeInsets.only(right: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppLayout.borderRadiusMd,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, size: 18, color: color),
              ),
              if (trend != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: trendUp
                        ? AppColors.success100
                        : AppColors.danger100,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    trend!,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: trendUp
                          ? AppColors.success600
                          : AppColors.danger600,
                    ),
                  ),
                ),
            ],
          ),
          const Spacer(),
          Text(
            value,
            style: AppTypography.h3.copyWith(fontSize: 20),
          ),
          const SizedBox(height: 2),
          Text(
            title,
            style: AppTypography.caption,
          ),
        ],
      ),
    );
  }
}

// Simple Sales Chart
class _SimpleSalesChart extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final data = MockData.salesChartData;
    final maxValue = data.map((d) => d['value'] as int).reduce((a, b) => a > b ? a : b);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: data.asMap().entries.map((entry) {
        final index = entry.key;
        final item = entry.value;
        final value = item['value'] as int;
        final height = (value / maxValue) * 100;

        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                AnimatedContainer(
                  duration: Duration(milliseconds: 300 + (index * 100)),
                  curve: Curves.easeOut,
                  height: height,
                  decoration: BoxDecoration(
                    color: index == data.length - 1
                        ? AppColors.primary500
                        : AppColors.primary200,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  item['month'] as String,
                  style: const TextStyle(
                    fontSize: 9,
                    color: AppColors.gray400,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

// Progress Ring
class _ProgressRing extends StatelessWidget {
  final double progress;
  final double size;

  const _ProgressRing({
    required this.progress,
    this.size = 80,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        fit: StackFit.expand,
        children: [
          CircularProgressIndicator(
            value: 1,
            strokeWidth: 6,
            backgroundColor: AppColors.gray100,
            valueColor: const AlwaysStoppedAnimation(AppColors.gray100),
          ),
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: progress),
            duration: const Duration(milliseconds: 800),
            curve: Curves.easeOut,
            builder: (context, value, child) {
              return CircularProgressIndicator(
                value: value,
                strokeWidth: 6,
                backgroundColor: Colors.transparent,
                valueColor: const AlwaysStoppedAnimation(AppColors.success500),
              );
            },
          ),
          Center(
            child: Text(
              '${(progress * 100).toInt()}%',
              style: AppTypography.label.copyWith(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }
}

// Task Item
class _TaskItem extends StatelessWidget {
  final Task task;
  final bool showDivider;

  const _TaskItem({
    required this.task,
    this.showDivider = true,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Container(
                width: 20,
                height: 20,
                decoration: BoxDecoration(
                  border: Border.all(
                    color: task.completed
                        ? AppColors.success500
                        : AppColors.gray300,
                    width: 2,
                  ),
                  borderRadius: BorderRadius.circular(4),
                  color: task.completed ? AppColors.success500 : null,
                ),
                child: task.completed
                    ? const Icon(Icons.check, size: 14, color: Colors.white)
                    : null,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      task.title,
                      style: AppTypography.body.copyWith(
                        decoration: task.completed
                            ? TextDecoration.lineThrough
                            : null,
                        color: task.completed
                            ? AppColors.gray400
                            : AppColors.textPrimary,
                      ),
                    ),
                    if (task.relatedTo != null)
                      Text(
                        task.relatedTo!.displayLabel,
                        style: AppTypography.caption,
                      ),
                  ],
                ),
              ),
              PriorityBadge(priority: task.priority, compact: true),
            ],
          ),
        ),
        if (showDivider)
          const Divider(height: 1, indent: 44),
      ],
    );
  }
}

// Activity Item
class _ActivityItem extends StatelessWidget {
  final Activity activity;
  final bool showDivider;

  const _ActivityItem({
    required this.activity,
    this.showDivider = true,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: activity.type.color.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  activity.type.icon,
                  size: 18,
                  color: activity.type.color,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      activity.title,
                      style: AppTypography.body,
                    ),
                    Row(
                      children: [
                        if (activity.userName != null) ...[
                          Text(
                            activity.userName!,
                            style: AppTypography.caption.copyWith(
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const Text(' • ', style: TextStyle(color: AppColors.gray300)),
                        ],
                        Text(
                          activity.relativeTime,
                          style: AppTypography.caption,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (showDivider)
          const Divider(height: 1, indent: 60),
      ],
    );
  }
}
