import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../common/common.dart';

/// Task Row Widget
/// Displays task in list with checkbox, info, and swipe actions
class TaskRow extends StatelessWidget {
  final Task task;
  final VoidCallback? onToggle;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;

  const TaskRow({
    super.key,
    required this.task,
    this.onToggle,
    this.onTap,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Dismissible(
      key: Key(task.id),
      direction: DismissDirection.endToStart,
      background: Container(
        color: AppColors.danger500,
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        child: const Icon(
          LucideIcons.trash2,
          color: Colors.white,
          size: 22,
        ),
      ),
      confirmDismiss: (direction) async {
        onDelete?.call();
        return false; // Handle deletion in callback
      },
      child: InkWell(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            color: AppColors.surface,
            border: Border(
              bottom: BorderSide(color: AppColors.gray100),
            ),
          ),
          child: Row(
            children: [
              // Checkbox
              GestureDetector(
                onTap: onToggle,
                child: AnimatedContainer(
                  duration: AppDurations.fast,
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: task.completed ? AppColors.primary600 : null,
                    border: Border.all(
                      color: task.completed
                          ? AppColors.primary600
                          : AppColors.gray300,
                      width: 2,
                    ),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: task.completed
                      ? const Icon(
                          LucideIcons.check,
                          size: 14,
                          color: Colors.white,
                        )
                      : null,
                ),
              ),

              const SizedBox(width: 14),

              // Task Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Title
                    Text(
                      task.title,
                      style: AppTypography.label.copyWith(
                        decoration:
                            task.completed ? TextDecoration.lineThrough : null,
                        color: task.completed
                            ? AppColors.textTertiary
                            : AppColors.textPrimary,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),

                    const SizedBox(height: 4),

                    // Subtitle: Due time + Related entity
                    Row(
                      children: [
                        Icon(
                          LucideIcons.clock,
                          size: 12,
                          color: _getDueTimeColor(),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          _formatDueTime(),
                          style: AppTypography.caption.copyWith(
                            color: _getDueTimeColor(),
                            fontWeight: _isUrgent() ? FontWeight.w600 : null,
                          ),
                        ),
                        if (task.relatedTo != null) ...[
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 6),
                            child: Text(
                              '•',
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textTertiary,
                              ),
                            ),
                          ),
                          Expanded(
                            child: Text(
                              _getRelatedLabel(),
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textSecondary,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 10),

              // Priority Badge
              PriorityBadge(priority: task.priority, compact: true),

              const SizedBox(width: 10),

              // Assignee Avatar
              UserAvatar(
                name: task.assignedToName,
                size: AvatarSize.xs,
              ),
            ],
          ),
        ),
      ),
    );
  }

  bool _isUrgent() {
    if (task.dueDate == null) return false;
    final now = DateTime.now();
    return task.dueDate!.isBefore(now) ||
        task.dueDate!.difference(now).inHours < 2;
  }

  Color _getDueTimeColor() {
    if (task.completed) return AppColors.textTertiary;
    if (task.dueDate == null) return AppColors.textTertiary;

    final now = DateTime.now();
    final dueDate = task.dueDate!;

    if (dueDate.isBefore(now)) {
      return AppColors.danger600;
    } else if (dueDate.difference(now).inHours < 2) {
      return AppColors.warning600;
    } else if (_isSameDay(dueDate, now)) {
      return AppColors.textSecondary;
    } else {
      return AppColors.textTertiary;
    }
  }

  String _formatDueTime() {
    if (task.dueDate == null) return 'No due date';

    final now = DateTime.now();
    final dueDate = task.dueDate!;

    if (dueDate.isBefore(now) && !_isSameDay(dueDate, now)) {
      final daysOverdue = now.difference(dueDate).inDays;
      return '${daysOverdue}d overdue';
    } else if (_isSameDay(dueDate, now)) {
      return 'Today ${_formatTime(dueDate)}';
    } else if (_isSameDay(dueDate, now.add(const Duration(days: 1)))) {
      return 'Tomorrow ${_formatTime(dueDate)}';
    } else {
      return _formatDateShort(dueDate);
    }
  }

  String _formatTime(DateTime date) {
    final hour = date.hour > 12 ? date.hour - 12 : date.hour;
    final period = date.hour >= 12 ? 'PM' : 'AM';
    final minute = date.minute.toString().padLeft(2, '0');
    return '$hour:$minute $period';
  }

  String _formatDateShort(DateTime date) {
    final months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${months[date.month - 1]} ${date.day}';
  }

  bool _isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  String _getRelatedLabel() {
    if (task.relatedTo == null) return '';

    final type = task.relatedTo!.type;
    final title = task.relatedTo!.title;

    switch (type) {
      case RelatedEntityType.lead:
        return 'Lead: $title';
      case RelatedEntityType.account:
        return 'Account: $title';
      case RelatedEntityType.opportunity:
        return 'Opportunity: $title';
      case RelatedEntityType.case_:
        return 'Case: $title';
      case RelatedEntityType.contact:
        return 'Contact: $title';
    }
  }
}

/// Task Group Widget
/// Collapsible section for grouping tasks (Overdue, Today, Upcoming)
class TaskGroup extends StatefulWidget {
  final String title;
  final String variant; // 'danger', 'warning', 'default'
  final List<Task> tasks;
  final Function(Task)? onToggle;
  final Function(Task)? onTap;
  final Function(Task)? onDelete;
  final bool initiallyExpanded;

  const TaskGroup({
    super.key,
    required this.title,
    this.variant = 'default',
    required this.tasks,
    this.onToggle,
    this.onTap,
    this.onDelete,
    this.initiallyExpanded = true,
  });

  @override
  State<TaskGroup> createState() => _TaskGroupState();
}

class _TaskGroupState extends State<TaskGroup> {
  late bool _expanded;

  @override
  void initState() {
    super.initState();
    _expanded = widget.initiallyExpanded;
  }

  Color get _accentColor {
    switch (widget.variant) {
      case 'danger':
        return AppColors.danger500;
      case 'warning':
        return AppColors.warning500;
      default:
        return AppColors.gray400;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.tasks.isEmpty) return const SizedBox.shrink();

    return Column(
      children: [
        // Group Header
        InkWell(
          onTap: () => setState(() => _expanded = !_expanded),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: AppColors.gray50,
              border: Border(
                left: BorderSide(color: _accentColor, width: 3),
                bottom: BorderSide(color: AppColors.border),
              ),
            ),
            child: Row(
              children: [
                Text(
                  widget.title,
                  style: AppTypography.label.copyWith(
                    color: _accentColor,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: _accentColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${widget.tasks.length}',
                    style: AppTypography.caption.copyWith(
                      color: _accentColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const Spacer(),
                AnimatedRotation(
                  turns: _expanded ? 0 : -0.25,
                  duration: AppDurations.fast,
                  child: Icon(
                    LucideIcons.chevronDown,
                    size: 20,
                    color: AppColors.textTertiary,
                  ),
                ),
              ],
            ),
          ),
        ),

        // Group Content
        AnimatedCrossFade(
          firstChild: Column(
            children: widget.tasks.map((task) {
              return TaskRow(
                task: task,
                onToggle: () => widget.onToggle?.call(task),
                onTap: () => widget.onTap?.call(task),
                onDelete: () => widget.onDelete?.call(task),
              );
            }).toList(),
          ),
          secondChild: const SizedBox.shrink(),
          crossFadeState:
              _expanded ? CrossFadeState.showFirst : CrossFadeState.showSecond,
          duration: AppDurations.normal,
        ),
      ],
    );
  }
}
