import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:table_calendar/table_calendar.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../data/mock/mock_data.dart';
import '../../widgets/cards/task_row.dart';
import '../../widgets/common/common.dart';

enum TaskViewMode { calendar, list }

/// Tasks List Screen
/// Calendar and List views for task management
class TasksListScreen extends StatefulWidget {
  const TasksListScreen({super.key});

  @override
  State<TasksListScreen> createState() => _TasksListScreenState();
}

class _TasksListScreenState extends State<TasksListScreen> {
  TaskViewMode _viewMode = TaskViewMode.calendar;
  DateTime _focusedDay = DateTime.now();
  DateTime _selectedDay = DateTime.now();
  CalendarFormat _calendarFormat = CalendarFormat.month;

  // Get all tasks (using a copy for modification simulation)
  List<Task> get _allTasks => List<Task>.from(MockData.tasks);

  // Get task dates for calendar markers
  Set<String> get _taskDates {
    return _allTasks.map((t) => _formatDateKey(t.dueDate)).toSet();
  }

  // Tasks for selected date (Calendar view)
  List<Task> get _tasksForSelectedDate {
    return _allTasks
        .where((t) => _isSameDay(t.dueDate, _selectedDay))
        .toList()
      ..sort((a, b) => a.dueDate.compareTo(b.dueDate));
  }

  // Grouped tasks for List view
  List<Task> get _overdueTasks {
    final now = DateTime.now();
    return _allTasks
        .where((t) =>
            !t.completed &&
            t.dueDate.isBefore(now) &&
            !_isSameDay(t.dueDate, now))
        .toList()
      ..sort((a, b) => a.dueDate.compareTo(b.dueDate));
  }

  List<Task> get _todayTasks {
    final now = DateTime.now();
    return _allTasks
        .where((t) => !t.completed && _isSameDay(t.dueDate, now))
        .toList()
      ..sort((a, b) => a.dueDate.compareTo(b.dueDate));
  }

  List<Task> get _upcomingTasks {
    final now = DateTime.now();
    return _allTasks
        .where((t) =>
            !t.completed &&
            (t.dueDate.isAfter(now) && !_isSameDay(t.dueDate, now)))
        .toList()
      ..sort((a, b) => a.dueDate.compareTo(b.dueDate));
  }

  List<Task> get _completedTasks {
    return _allTasks.where((t) => t.completed).toList();
  }

  @override
  Widget build(BuildContext context) {
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
      body: AnimatedSwitcher(
        duration: AppDurations.normal,
        child: _viewMode == TaskViewMode.calendar
            ? _buildCalendarView()
            : _buildListView(),
      ),
    );
  }

  Widget _buildCalendarView() {
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
                if (_taskDates.contains(_formatDateKey(date))) {
                  final tasksOnDate = _allTasks
                      .where((t) => _isSameDay(t.dueDate, date))
                      .toList();
                  final hasOverdue = tasksOnDate.any((t) =>
                      !t.completed && t.dueDate.isBefore(DateTime.now()));

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
          child: _tasksForSelectedDate.isEmpty
              ? _buildEmptyDateState()
              : ListView.builder(
                  padding: const EdgeInsets.only(bottom: 100),
                  itemCount: _tasksForSelectedDate.length,
                  itemBuilder: (context, index) {
                    final task = _tasksForSelectedDate[index];
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

  Widget _buildListView() {
    final hasAnyTasks = _overdueTasks.isNotEmpty ||
        _todayTasks.isNotEmpty ||
        _upcomingTasks.isNotEmpty;

    if (!hasAnyTasks) {
      return _buildAllCaughtUpState();
    }

    return RefreshIndicator(
      onRefresh: () async {
        await Future.delayed(const Duration(seconds: 1));
      },
      child: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 100),
        child: Column(
          children: [
            // Overdue
            if (_overdueTasks.isNotEmpty)
              TaskGroup(
                title: 'Overdue',
                variant: 'danger',
                tasks: _overdueTasks,
                onToggle: _toggleTask,
                onTap: _showTaskDetail,
                onDelete: _deleteTask,
              ),

            // Today
            if (_todayTasks.isNotEmpty)
              TaskGroup(
                title: 'Today',
                variant: 'warning',
                tasks: _todayTasks,
                onToggle: _toggleTask,
                onTap: _showTaskDetail,
                onDelete: _deleteTask,
              ),

            // Upcoming
            if (_upcomingTasks.isNotEmpty)
              TaskGroup(
                title: 'Upcoming',
                variant: 'default',
                tasks: _upcomingTasks,
                onToggle: _toggleTask,
                onTap: _showTaskDetail,
                onDelete: _deleteTask,
              ),

            // Completed (collapsed by default)
            if (_completedTasks.isNotEmpty)
              TaskGroup(
                title: 'Completed',
                variant: 'default',
                tasks: _completedTasks,
                initiallyExpanded: false,
                onToggle: _toggleTask,
                onTap: _showTaskDetail,
                onDelete: _deleteTask,
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
                  Text(
                    _formatDueDate(task.dueDate),
                    style: AppTypography.body.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),

              if (task.description != null) ...[
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
                        task.relatedTo!.type == RelatedEntityType.lead
                            ? LucideIcons.user
                            : LucideIcons.briefcase,
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
      return 'Due today at ${_formatTime(date)}';
    } else if (_isSameDay(date, now.add(const Duration(days: 1)))) {
      return 'Due tomorrow at ${_formatTime(date)}';
    } else {
      final months = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
      ];
      return 'Due ${months[date.month - 1]} ${date.day} at ${_formatTime(date)}';
    }
  }

  String _formatTime(DateTime date) {
    final hour = date.hour > 12 ? date.hour - 12 : (date.hour == 0 ? 12 : date.hour);
    final period = date.hour >= 12 ? 'PM' : 'AM';
    final minute = date.minute.toString().padLeft(2, '0');
    return '$hour:$minute $period';
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  String _formatDateKey(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }
}
