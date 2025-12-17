import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:table_calendar/table_calendar.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/tasks_provider.dart';
import '../../widgets/cards/task_row.dart';
import '../../widgets/common/common.dart';

enum TaskViewMode { calendar, list }

/// Tasks List Screen
/// Calendar and List views for task management
class TasksListScreen extends ConsumerStatefulWidget {
  const TasksListScreen({super.key});

  @override
  ConsumerState<TasksListScreen> createState() => _TasksListScreenState();
}

class _TasksListScreenState extends ConsumerState<TasksListScreen> {
  TaskViewMode _viewMode = TaskViewMode.list;
  DateTime _focusedDay = DateTime.now();
  DateTime _selectedDay = DateTime.now();
  CalendarFormat _calendarFormat = CalendarFormat.month;

  @override
  void initState() {
    super.initState();
    // Fetch tasks on init
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(tasksProvider.notifier).fetchTasks(refresh: true);
    });
  }

  // Get task dates for calendar markers
  Set<String> _getTaskDates(List<Task> tasks) {
    return tasks
        .where((t) => t.dueDate != null)
        .map((t) => _formatDateKey(t.dueDate!))
        .toSet();
  }

  // Tasks for selected date (Calendar view)
  List<Task> _getTasksForSelectedDate(List<Task> tasks) {
    return tasks
        .where((t) => t.dueDate != null && _isSameDay(t.dueDate!, _selectedDay))
        .toList()
      ..sort((a, b) {
        if (a.dueDate == null) return 1;
        if (b.dueDate == null) return -1;
        return a.dueDate!.compareTo(b.dueDate!);
      });
  }

  @override
  Widget build(BuildContext context) {
    final tasksState = ref.watch(tasksProvider);
    final allTasks = tasksState.tasks;
    final isLoading = tasksState.isLoading;
    final error = tasksState.error;

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Tasks'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          // View toggle
          IconButton(
            icon: Icon(
              _viewMode == TaskViewMode.calendar
                  ? LucideIcons.list
                  : LucideIcons.calendar,
              size: 22,
            ),
            onPressed: () {
              setState(() {
                _viewMode = _viewMode == TaskViewMode.calendar
                    ? TaskViewMode.list
                    : TaskViewMode.calendar;
              });
            },
          ),

          // Add task
          IconButton(
            icon: const Icon(LucideIcons.plus, size: 22),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Create task coming soon'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
          ),
        ],
      ),
      body: _buildBody(allTasks, isLoading, error),
    );
  }

  Widget _buildBody(List<Task> allTasks, bool isLoading, String? error) {
    // Show loading spinner for initial load
    if (isLoading && allTasks.isEmpty) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    // Show error state
    if (error != null && allTasks.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                LucideIcons.alertCircle,
                size: 48,
                color: AppColors.danger500,
              ),
              const SizedBox(height: 16),
              Text(
                'Failed to load tasks',
                style: AppTypography.h3,
              ),
              const SizedBox(height: 8),
              Text(
                error,
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              PrimaryButton(
                label: 'Retry',
                icon: LucideIcons.refreshCw,
                onPressed: () {
                  ref.read(tasksProvider.notifier).fetchTasks(refresh: true);
                },
              ),
            ],
          ),
        ),
      );
    }

    return AnimatedSwitcher(
      duration: AppDurations.normal,
      child: _viewMode == TaskViewMode.calendar
          ? _buildCalendarView(allTasks)
          : _buildListView(allTasks, isLoading),
    );
  }

  Widget _buildCalendarView(List<Task> allTasks) {
    final taskDates = _getTaskDates(allTasks);
    final tasksForSelectedDate = _getTasksForSelectedDate(allTasks);

    return Column(
      children: [
        // Calendar
        Container(
          color: AppColors.surface,
          child: TableCalendar(
            firstDay: DateTime.utc(2020, 1, 1),
            lastDay: DateTime.utc(2030, 12, 31),
            focusedDay: _focusedDay,
            selectedDayPredicate: (day) => _isSameDay(_selectedDay, day),
            calendarFormat: _calendarFormat,
            startingDayOfWeek: StartingDayOfWeek.sunday,
            onDaySelected: (selectedDay, focusedDay) {
              setState(() {
                _selectedDay = selectedDay;
                _focusedDay = focusedDay;
              });
            },
            onFormatChanged: (format) {
              setState(() {
                _calendarFormat = format;
              });
            },
            onPageChanged: (focusedDay) {
              _focusedDay = focusedDay;
            },
            calendarStyle: CalendarStyle(
              // Today
              todayDecoration: BoxDecoration(
                color: AppColors.primary100,
                shape: BoxShape.circle,
              ),
              todayTextStyle: AppTypography.body.copyWith(
                color: AppColors.primary700,
                fontWeight: FontWeight.w600,
              ),
              // Selected
              selectedDecoration: BoxDecoration(
                color: AppColors.primary600,
                shape: BoxShape.circle,
              ),
              selectedTextStyle: AppTypography.body.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
              // Default
              defaultTextStyle: AppTypography.body,
              weekendTextStyle: AppTypography.body,
              outsideTextStyle: AppTypography.body.copyWith(
                color: AppColors.gray300,
              ),
              // Markers
              markerDecoration: BoxDecoration(
                color: AppColors.primary500,
                shape: BoxShape.circle,
              ),
              markersMaxCount: 3,
              markerSize: 5,
              markerMargin: const EdgeInsets.symmetric(horizontal: 1),
            ),
            headerStyle: HeaderStyle(
              titleCentered: true,
              formatButtonVisible: false,
              titleTextStyle: AppTypography.h3,
              leftChevronIcon: Icon(
                LucideIcons.chevronLeft,
                size: 22,
                color: AppColors.textSecondary,
              ),
              rightChevronIcon: Icon(
                LucideIcons.chevronRight,
                size: 22,
                color: AppColors.textSecondary,
              ),
            ),
            daysOfWeekStyle: DaysOfWeekStyle(
              weekdayStyle: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
              weekendStyle: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            calendarBuilders: CalendarBuilders(
              markerBuilder: (context, date, events) {
                if (taskDates.contains(_formatDateKey(date))) {
                  final tasksOnDate = allTasks
                      .where((t) => t.dueDate != null && _isSameDay(t.dueDate!, date))
                      .toList();
                  final hasOverdue = tasksOnDate.any((t) =>
                      !t.completed && t.dueDate != null && t.dueDate!.isBefore(DateTime.now()));

                  return Positioned(
                    bottom: 4,
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: BoxDecoration(
                            color: hasOverdue
                                ? AppColors.danger500
                                : AppColors.primary500,
                            shape: BoxShape.circle,
                          ),
                        ),
                        if (tasksOnDate.length > 1) ...[
                          const SizedBox(width: 2),
                          Container(
                            width: 4,
                            height: 4,
                            decoration: BoxDecoration(
                              color: AppColors.gray400,
                              shape: BoxShape.circle,
                            ),
                          ),
                        ],
                      ],
                    ),
                  );
                }
                return null;
              },
            ),
          ),
        ),

        // Section Header
        Container(
          width: double.infinity,
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          color: AppColors.surfaceDim,
          child: Text(
            _getSelectedDateLabel(),
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ),

        // Tasks for selected date
        Expanded(
          child: tasksForSelectedDate.isEmpty
              ? _buildEmptyDateState()
              : ListView.builder(
                  padding: const EdgeInsets.only(bottom: 100),
                  itemCount: tasksForSelectedDate.length,
                  itemBuilder: (context, index) {
                    final task = tasksForSelectedDate[index];
                    return TaskRow(
                      task: task,
                      onToggle: () => _toggleTask(task),
                      onTap: () => _showTaskDetail(task),
                      onDelete: () => _deleteTask(task),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildListView(List<Task> allTasks, bool isLoading) {
    final overdueTasks = ref.watch(overdueTasksProvider);
    final todayTasks = ref.watch(todayTasksProvider);
    final upcomingTasks = ref.watch(upcomingTasksProvider);
    final completedTasks = ref.watch(completedTasksProvider);
    final noDueDateTasks = ref.watch(noDueDateTasksProvider);

    final hasAnyTasks = overdueTasks.isNotEmpty ||
        todayTasks.isNotEmpty ||
        upcomingTasks.isNotEmpty ||
        noDueDateTasks.isNotEmpty;

    if (!hasAnyTasks && !isLoading) {
      return _buildAllCaughtUpState();
    }

    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(tasksProvider.notifier).refresh();
      },
      child: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 100),
        child: Column(
          children: [
            // Overdue
            if (overdueTasks.isNotEmpty)
              TaskGroup(
                title: 'Overdue',
                variant: 'danger',
                tasks: overdueTasks,
                onToggle: _toggleTask,
                onTap: _showTaskDetail,
                onDelete: _deleteTask,
              ),

            // Today
            if (todayTasks.isNotEmpty)
              TaskGroup(
                title: 'Today',
                variant: 'warning',
                tasks: todayTasks,
                onToggle: _toggleTask,
                onTap: _showTaskDetail,
                onDelete: _deleteTask,
              ),

            // Upcoming
            if (upcomingTasks.isNotEmpty)
              TaskGroup(
                title: 'Upcoming',
                variant: 'default',
                tasks: upcomingTasks,
                onToggle: _toggleTask,
                onTap: _showTaskDetail,
                onDelete: _deleteTask,
              ),

            // No Due Date
            if (noDueDateTasks.isNotEmpty)
              TaskGroup(
                title: 'No Due Date',
                variant: 'default',
                tasks: noDueDateTasks,
                onToggle: _toggleTask,
                onTap: _showTaskDetail,
                onDelete: _deleteTask,
              ),

            // Completed (collapsed by default)
            if (completedTasks.isNotEmpty)
              TaskGroup(
                title: 'Completed',
                variant: 'default',
                tasks: completedTasks,
                initiallyExpanded: false,
                onToggle: _toggleTask,
                onTap: _showTaskDetail,
                onDelete: _deleteTask,
              ),

            // Loading indicator at bottom
            if (isLoading && allTasks.isNotEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: Center(
                  child: CircularProgressIndicator(),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyDateState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: AppColors.gray100,
                shape: BoxShape.circle,
              ),
              child: Icon(
                LucideIcons.calendarCheck,
                size: 28,
                color: AppColors.gray400,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'No tasks for this date',
              style: AppTypography.label.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            GestureDetector(
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Create task coming soon'),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
              child: Text(
                'Add a task',
                style: AppTypography.label.copyWith(
                  color: AppColors.primary600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAllCaughtUpState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: AppColors.success100,
                shape: BoxShape.circle,
              ),
              child: Icon(
                LucideIcons.checkCircle2,
                size: 40,
                color: AppColors.success600,
              ),
            ),
            const SizedBox(height: 20),
            Text(
              'All caught up!',
              style: AppTypography.h2.copyWith(
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'No pending tasks. Create a new task to get started.',
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            PrimaryButton(
              label: 'Add Task',
              icon: LucideIcons.plus,
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Create task coming soon'),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  String _getSelectedDateLabel() {
    final now = DateTime.now();

    if (_isSameDay(_selectedDay, now)) {
      return 'Today';
    } else if (_isSameDay(_selectedDay, now.add(const Duration(days: 1)))) {
      return 'Tomorrow';
    } else if (_isSameDay(_selectedDay, now.subtract(const Duration(days: 1)))) {
      return 'Yesterday';
    } else {
      final months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      return '${months[_selectedDay.month - 1]} ${_selectedDay.day}';
    }
  }

  void _toggleTask(Task task) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          task.completed
              ? 'Task marked as incomplete'
              : 'Task completed',
        ),
        behavior: SnackBarBehavior.floating,
        action: SnackBarAction(
          label: 'Undo',
          onPressed: () {},
        ),
      ),
    );
  }

  void _showTaskDetail(Task task) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Handle
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.gray300,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Title
              Text(task.title, style: AppTypography.h2),
              const SizedBox(height: 8),

              // Priority & Due
              Row(
                children: [
                  PriorityBadge(priority: task.priority),
                  const SizedBox(width: 8),
                  if (task.dueDate != null)
                    Text(
                      _formatDueDate(task.dueDate!),
                      style: AppTypography.body.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    )
                  else
                    Text(
                      'No due date',
                      style: AppTypography.body.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                ],
              ),

              // Status
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: task.status.color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  task.status.label,
                  style: AppTypography.caption.copyWith(
                    color: task.status.color,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),

              if (task.description != null && task.description!.isNotEmpty) ...[
                const SizedBox(height: 16),
                Text(
                  task.description!,
                  style: AppTypography.body.copyWith(
                    color: AppColors.textSecondary,
                    height: 1.5,
                  ),
                ),
              ],

              if (task.relatedTo != null) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.gray50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        task.relatedTo!.type.icon,
                        size: 18,
                        color: AppColors.textSecondary,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '${task.relatedTo!.type.label.toUpperCase()}: ${task.relatedTo!.title}',
                        style: AppTypography.body.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 24),

              // Actions
              Row(
                children: [
                  Expanded(
                    child: SecondaryButton(
                      label: task.completed ? 'Mark Incomplete' : 'Complete',
                      icon: task.completed
                          ? LucideIcons.circle
                          : LucideIcons.checkCircle2,
                      onPressed: () {
                        Navigator.pop(context);
                        _toggleTask(task);
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: PrimaryButton(
                      label: 'Edit',
                      icon: LucideIcons.pencil,
                      onPressed: () {
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Edit task coming soon'),
                            behavior: SnackBarBehavior.floating,
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _deleteTask(Task task) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Task?'),
        content: Text('Are you sure you want to delete "${task.title}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: const Text('Task deleted'),
                  behavior: SnackBarBehavior.floating,
                  action: SnackBarAction(
                    label: 'Undo',
                    onPressed: () {},
                  ),
                ),
              );
            },
            child: Text(
              'Delete',
              style: TextStyle(color: AppColors.danger600),
            ),
          ),
        ],
      ),
    );
  }

  String _formatDueDate(DateTime date) {
    final now = DateTime.now();
    if (_isSameDay(date, now)) {
      return 'Due today';
    } else if (_isSameDay(date, now.add(const Duration(days: 1)))) {
      return 'Due tomorrow';
    } else {
      final months = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
      ];
      return 'Due ${months[date.month - 1]} ${date.day}';
    }
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  String _formatDateKey(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }
}
