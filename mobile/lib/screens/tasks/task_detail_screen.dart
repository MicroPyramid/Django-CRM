import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/tasks_provider.dart';
import '../../widgets/common/common.dart';

/// Task Detail Screen
/// Shows task info with actions: Edit, Complete, Delete
class TaskDetailScreen extends ConsumerStatefulWidget {
  final String taskId;

  const TaskDetailScreen({
    super.key,
    required this.taskId,
  });

  @override
  ConsumerState<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends ConsumerState<TaskDetailScreen> {
  Task? _task;
  bool _isLoading = true;
  bool _isUpdating = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchTask();
  }

  Future<void> _fetchTask() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final task = await ref.read(tasksProvider.notifier).getTaskById(widget.taskId);

    if (mounted) {
      setState(() {
        _isLoading = false;
        _task = task;
        if (task == null) {
          _error = 'Failed to load task';
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    // Loading state
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(
          leading: IconButton(
            icon: const Icon(LucideIcons.chevronLeft),
            onPressed: () => context.pop(),
          ),
        ),
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    // Error or not found state
    if (_task == null || _error != null) {
      return Scaffold(
        appBar: AppBar(
          leading: IconButton(
            icon: const Icon(LucideIcons.chevronLeft),
            onPressed: () => context.pop(),
          ),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                LucideIcons.fileX,
                size: 48,
                color: AppColors.gray400,
              ),
              const SizedBox(height: 16),
              Text(
                'Task not found',
                style: AppTypography.h3,
              ),
              const SizedBox(height: 8),
              Text(
                _error ?? 'This task may have been deleted',
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 16),
              TextButton(
                onPressed: _fetchTask,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.surface,
      body: CustomScrollView(
        slivers: [
          // App Bar
          SliverAppBar(
            expandedHeight: 200,
            pinned: true,
            backgroundColor: _getHeaderColor(),
            leading: IconButton(
              icon: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.9),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  LucideIcons.chevronLeft,
                  size: 20,
                  color: AppColors.textPrimary,
                ),
              ),
              onPressed: () => context.pop(),
            ),
            actions: [
              IconButton(
                icon: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.9),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    LucideIcons.pencil,
                    size: 18,
                    color: AppColors.textPrimary,
                  ),
                ),
                onPressed: () async {
                  final result = await context.push('/tasks/${widget.taskId}/edit');
                  if (result == true && mounted) {
                    _fetchTask();
                  }
                },
              ),
              IconButton(
                icon: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.9),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    LucideIcons.moreVertical,
                    size: 18,
                    color: AppColors.textPrimary,
                  ),
                ),
                onPressed: () => _showMoreOptions(),
              ),
            ],
            flexibleSpace: FlexibleSpaceBar(
              background: _buildHeader(),
            ),
          ),

          // Content
          SliverToBoxAdapter(
            child: _buildContent(),
          ),
        ],
      ),
      bottomNavigationBar: _buildBottomActions(),
    );
  }

  Color _getHeaderColor() {
    if (_task!.completed) return AppColors.success50;
    if (_task!.isOverdue) return AppColors.danger50;
    return AppColors.primary50;
  }

  Widget _buildHeader() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            _getHeaderColor(),
            _getHeaderColor().withValues(alpha: 0.7),
          ],
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.end,
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Status Badge
              Row(
                children: [
                  _buildStatusChip(),
                  const SizedBox(width: 8),
                  PriorityBadge(priority: _task!.priority),
                ],
              ),

              const SizedBox(height: 12),

              // Title - always show
              Text(
                _task!.title,
                style: AppTypography.h2.copyWith(
                  color: AppColors.textPrimary,
                  decoration: _task!.completed
                      ? TextDecoration.lineThrough
                      : null,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),

              const SizedBox(height: 8),

              // Due Date
              if (_task!.dueDate != null)
                Row(
                  children: [
                    Icon(
                      LucideIcons.calendar,
                      size: 16,
                      color: _getDueDateColor(),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      _formatDueDate(_task!.dueDate!),
                      style: AppTypography.label.copyWith(
                        color: _getDueDateColor(),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                )
              else
                Text(
                  'No due date',
                  style: AppTypography.body.copyWith(
                    color: AppColors.textTertiary,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusChip() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: _task!.status.color,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            _getStatusIcon(_task!.status),
            size: 14,
            color: Colors.white,
          ),
          const SizedBox(width: 6),
          Text(
            _task!.status.label,
            style: AppTypography.labelSmall.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  IconData _getStatusIcon(TaskStatus status) {
    switch (status) {
      case TaskStatus.newTask:
        return LucideIcons.circle;
      case TaskStatus.inProgress:
        return LucideIcons.clock;
      case TaskStatus.completed:
        return LucideIcons.checkCircle2;
    }
  }

  Color _getDueDateColor() {
    if (_task!.completed) return AppColors.textTertiary;
    if (_task!.isOverdue) return AppColors.danger600;
    if (_task!.isDueToday) return AppColors.warning600;
    return AppColors.textSecondary;
  }

  Widget _buildContent() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Description Card
          if (_task!.description != null && _task!.description!.isNotEmpty)
            _buildCard(
              title: 'Description',
              icon: LucideIcons.fileText,
              child: Text(
                _task!.description!,
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                  height: 1.6,
                ),
              ),
            ),

          if (_task!.description != null && _task!.description!.isNotEmpty)
            const SizedBox(height: 16),

          // Related Entity Card
          if (_task!.relatedTo != null)
            _buildCard(
              title: 'Related To',
              icon: LucideIcons.link2,
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: AppColors.primary100,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      _task!.relatedTo!.type.icon,
                      size: 20,
                      color: AppColors.primary600,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _task!.relatedTo!.type.label,
                          style: AppTypography.caption.copyWith(
                            color: AppColors.textSecondary,
                          ),
                        ),
                        Text(
                          _task!.relatedTo!.title,
                          style: AppTypography.label,
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    LucideIcons.chevronRight,
                    size: 20,
                    color: AppColors.textTertiary,
                  ),
                ],
              ),
            ),

          if (_task!.relatedTo != null)
            const SizedBox(height: 16),

          // Assigned To Card
          if (_task!.assignedTo != null && _task!.assignedTo!.isNotEmpty)
            _buildCard(
              title: 'Assigned To',
              icon: LucideIcons.user,
              child: Row(
                children: [
                  UserAvatar(
                    name: _task!.assignedToName,
                    size: AvatarSize.md,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    _task!.assignedToName,
                    style: AppTypography.label,
                  ),
                ],
              ),
            ),

          if (_task!.assignedTo != null && _task!.assignedTo!.isNotEmpty)
            const SizedBox(height: 16),

          // Tags Card
          if (_task!.tags.isNotEmpty)
            _buildCard(
              title: 'Tags',
              icon: LucideIcons.tag,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _task!.tags
                    .map((tag) => LabelPill(label: tag))
                    .toList(),
              ),
            ),

          if (_task!.tags.isNotEmpty)
            const SizedBox(height: 16),

          // Metadata Card
          _buildCard(
            title: 'Details',
            icon: LucideIcons.info,
            child: Column(
              children: [
                _buildInfoRow(
                  'Created',
                  _formatDateTime(_task!.createdAt),
                  LucideIcons.plus,
                ),
                if (_task!.updatedAt != null) ...[
                  const Divider(height: 20),
                  _buildInfoRow(
                    'Last Updated',
                    _formatDateTime(_task!.updatedAt!),
                    LucideIcons.pencil,
                  ),
                ],
              ],
            ),
          ),

          const SizedBox(height: 100),
        ],
      ),
    );
  }

  Widget _buildCard({
    required String title,
    required IconData icon,
    required Widget child,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                size: 16,
                color: AppColors.textTertiary,
              ),
              const SizedBox(width: 8),
              Text(
                title.toUpperCase(),
                style: AppTypography.overline.copyWith(
                  color: AppColors.textTertiary,
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, IconData icon) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: AppColors.gray400,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            label,
            style: AppTypography.body.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ),
        Text(
          value,
          style: AppTypography.label.copyWith(
            color: AppColors.textPrimary,
          ),
        ),
      ],
    );
  }

  Widget _buildBottomActions() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(
          top: BorderSide(color: AppColors.border),
        ),
      ),
      child: SafeArea(
        child: Row(
          children: [
            // Toggle Status Button
            Expanded(
              child: _isUpdating
                  ? const Center(
                      child: SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    )
                  : _task!.completed
                      ? SecondaryButton(
                          label: 'Reopen',
                          icon: LucideIcons.rotateCcw,
                          onPressed: _toggleTaskStatus,
                          isFullWidth: true,
                        )
                      : PrimaryButton(
                          label: 'Complete',
                          icon: LucideIcons.checkCircle2,
                          onPressed: _toggleTaskStatus,
                          isFullWidth: true,
                        ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _toggleTaskStatus() async {
    if (_task == null || _isUpdating) return;

    setState(() => _isUpdating = true);

    final response = await ref.read(tasksProvider.notifier).toggleTaskStatus(_task!);

    if (mounted) {
      setState(() => _isUpdating = false);

      if (response.success) {
        await _fetchTask();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(_task!.completed
                  ? 'Task marked as incomplete'
                  : 'Task completed'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.message ?? 'Failed to update task'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppColors.danger600,
          ),
        );
      }
    }
  }

  void _showMoreOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              margin: const EdgeInsets.only(top: 12),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.gray300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            ListTile(
              leading: const Icon(LucideIcons.pencil),
              title: const Text('Edit Task'),
              onTap: () async {
                Navigator.pop(context);
                final result = await context.push('/tasks/${widget.taskId}/edit');
                if (result == true && mounted) {
                  _fetchTask();
                }
              },
            ),
            ListTile(
              leading: Icon(
                _task!.completed ? LucideIcons.rotateCcw : LucideIcons.checkCircle2,
              ),
              title: Text(_task!.completed ? 'Reopen Task' : 'Complete Task'),
              onTap: () {
                Navigator.pop(context);
                _toggleTaskStatus();
              },
            ),
            ListTile(
              leading: Icon(LucideIcons.trash2, color: AppColors.danger600),
              title: Text(
                'Delete Task',
                style: TextStyle(color: AppColors.danger600),
              ),
              onTap: () {
                Navigator.pop(context);
                _confirmDelete();
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  void _confirmDelete() {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Delete Task?'),
        content: const Text(
          'This action cannot be undone. Are you sure you want to delete this task?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(dialogContext);
              await _deleteTask();
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

  Future<void> _deleteTask() async {
    setState(() => _isUpdating = true);

    final response = await ref.read(tasksProvider.notifier).deleteTask(widget.taskId);

    if (mounted) {
      setState(() => _isUpdating = false);

      if (response.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Task deleted'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        context.pop(true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.message ?? 'Failed to delete task'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppColors.danger600,
          ),
        );
      }
    }
  }

  String _formatDueDate(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final taskDate = DateTime(date.year, date.month, date.day);
    final tomorrow = today.add(const Duration(days: 1));
    final yesterday = today.subtract(const Duration(days: 1));

    if (taskDate == today) {
      return 'Due Today';
    } else if (taskDate == tomorrow) {
      return 'Due Tomorrow';
    } else if (taskDate == yesterday) {
      return 'Due Yesterday';
    } else if (taskDate.isBefore(today)) {
      final days = today.difference(taskDate).inDays;
      return '$days day${days > 1 ? 's' : ''} overdue';
    } else {
      final months = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
      ];
      return 'Due ${months[date.month - 1]} ${date.day}, ${date.year}';
    }
  }

  String _formatDateTime(DateTime date) {
    final months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }
}
