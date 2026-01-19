import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/tasks_provider.dart';
import '../../widgets/common/common.dart';

/// Task Form Screen - Reusable for both Create and Edit
class TaskFormScreen extends ConsumerStatefulWidget {
  final String? taskId;
  final Task? initialTask;

  const TaskFormScreen({
    super.key,
    this.taskId,
    this.initialTask,
  });

  bool get isEditMode => taskId != null;

  @override
  ConsumerState<TaskFormScreen> createState() => _TaskFormScreenState();
}

class _TaskFormScreenState extends ConsumerState<TaskFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();

  TaskStatus _status = TaskStatus.newTask;
  Priority _priority = Priority.medium;
  DateTime? _dueDate;
  bool _isLoading = false;
  bool _isFetchingTask = false;
  String? _fetchError;
  Task? _existingTask;

  @override
  void initState() {
    super.initState();
    if (widget.initialTask != null) {
      _populateFromTask(widget.initialTask!);
    } else if (widget.isEditMode) {
      _fetchTask();
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _fetchTask() async {
    setState(() {
      _isFetchingTask = true;
      _fetchError = null;
    });

    final task = await ref.read(tasksProvider.notifier).getTaskById(widget.taskId!);

    if (mounted) {
      setState(() {
        _isFetchingTask = false;
        if (task != null) {
          _existingTask = task;
          _populateFromTask(task);
        } else {
          _fetchError = 'Failed to load task';
        }
      });
    }
  }

  void _populateFromTask(Task task) {
    _existingTask = task;
    _titleController.text = task.title;
    _descriptionController.text = task.description ?? '';
    _status = task.status;
    _priority = task.priority;
    _dueDate = task.dueDate;
  }

  bool get _hasUnsavedChanges {
    if (_existingTask != null) {
      return _titleController.text != _existingTask!.title ||
          _descriptionController.text != (_existingTask!.description ?? '') ||
          _status != _existingTask!.status ||
          _priority != _existingTask!.priority ||
          _dueDate != _existingTask!.dueDate;
    }
    return _titleController.text.isNotEmpty ||
        _descriptionController.text.isNotEmpty ||
        _dueDate != null;
  }

  Future<bool> _onWillPop() async {
    if (!_hasUnsavedChanges) return true;

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Discard changes?'),
        content: const Text(
          'You have unsaved changes. Are you sure you want to leave?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(
              'Discard',
              style: TextStyle(color: AppColors.danger600),
            ),
          ),
        ],
      ),
    );

    return result ?? false;
  }

  Map<String, dynamic> _buildPayload() {
    return {
      'title': _titleController.text.trim(),
      'description': _descriptionController.text.trim().isEmpty
          ? null
          : _descriptionController.text.trim(),
      'status': _status.value,
      'priority': _priority.label,
      'due_date': _dueDate?.toIso8601String().split('T').first,
    };
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final payload = _buildPayload();
    final notifier = ref.read(tasksProvider.notifier);

    final response = widget.isEditMode
        ? await notifier.updateTask(widget.taskId!, payload)
        : await notifier.createTask(payload);

    if (mounted) {
      setState(() => _isLoading = false);

      if (response.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.isEditMode
                ? 'Task updated successfully'
                : 'Task created successfully'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        context.pop(true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.message ?? 'Failed to save task'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppColors.danger600,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: !_hasUnsavedChanges,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        final shouldPop = await _onWillPop();
        if (shouldPop && context.mounted) {
          context.pop();
        }
      },
      child: Scaffold(
        backgroundColor: AppColors.surface,
        appBar: AppBar(
          title: Text(widget.isEditMode ? 'Edit Task' : 'New Task'),
          backgroundColor: AppColors.surface,
          elevation: 0,
          scrolledUnderElevation: 1,
          leading: IconButton(
            icon: const Icon(LucideIcons.chevronLeft),
            onPressed: () async {
              if (_hasUnsavedChanges) {
                final shouldPop = await _onWillPop();
                if (shouldPop && context.mounted) {
                  context.pop();
                }
              } else {
                context.pop();
              }
            },
          ),
        ),
        body: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isFetchingTask) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_fetchError != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              LucideIcons.alertCircle,
              size: 48,
              color: AppColors.danger500,
            ),
            const SizedBox(height: 16),
            Text(
              _fetchError!,
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
      );
    }

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Task Title Section
            _buildSectionTitle('Task Details'),
            const SizedBox(height: 16),
            _buildTitleField(),

            const SizedBox(height: 24),

            // Status & Priority Section
            _buildSectionTitle('Status & Priority'),
            const SizedBox(height: 16),
            _buildStatusSelector(),
            const SizedBox(height: 20),
            _buildPrioritySelector(),

            const SizedBox(height: 24),

            // Due Date Section
            _buildSectionTitle('Due Date'),
            const SizedBox(height: 16),
            _buildDueDatePicker(),

            const SizedBox(height: 24),

            // Description Section
            _buildSectionTitle('Description'),
            const SizedBox(height: 16),
            TextAreaField(
              label: 'Notes',
              hint: 'Add any additional details about this task...',
              controller: _descriptionController,
              maxLines: 5,
            ),

            const SizedBox(height: 40),

            // Submit Button
            PrimaryButton(
              label: widget.isEditMode ? 'Update Task' : 'Create Task',
              onPressed: _isLoading ? null : _handleSubmit,
              isLoading: _isLoading,
              icon: widget.isEditMode ? LucideIcons.save : LucideIcons.plus,
            ),

            const SizedBox(height: 16),

            // Cancel Button
            Center(
              child: GestureDetector(
                onTap: () async {
                  if (_hasUnsavedChanges) {
                    final shouldPop = await _onWillPop();
                    if (shouldPop && mounted) {
                      context.pop();
                    }
                  } else {
                    context.pop();
                  }
                },
                child: Text(
                  'Cancel',
                  style: AppTypography.label.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 48),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title.toUpperCase(),
      style: AppTypography.overline.copyWith(
        color: AppColors.textSecondary,
        letterSpacing: 1.2,
      ),
    );
  }

  Widget _buildTitleField() {
    return FloatingLabelInput(
      label: 'Task Title',
      hint: 'What needs to be done?',
      controller: _titleController,
      prefixIcon: LucideIcons.checkSquare,
      textInputAction: TextInputAction.next,
      textCapitalization: TextCapitalization.sentences,
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Task title is required';
        }
        return null;
      },
    );
  }

  Widget _buildStatusSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Status',
          style: AppTypography.caption.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 10),
        Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.border),
          ),
          child: Row(
            children: TaskStatus.values.map((status) {
              final isSelected = _status == status;
              final isFirst = status == TaskStatus.values.first;
              final isLast = status == TaskStatus.values.last;

              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _status = status),
                  child: AnimatedContainer(
                    duration: AppDurations.fast,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    decoration: BoxDecoration(
                      color: isSelected ? status.color : AppColors.surface,
                      borderRadius: BorderRadius.horizontal(
                        left: isFirst ? const Radius.circular(11) : Radius.zero,
                        right: isLast ? const Radius.circular(11) : Radius.zero,
                      ),
                    ),
                    child: Column(
                      children: [
                        Icon(
                          _getStatusIcon(status),
                          size: 18,
                          color: isSelected ? Colors.white : status.color,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          status.label,
                          textAlign: TextAlign.center,
                          style: AppTypography.labelSmall.copyWith(
                            color: isSelected
                                ? Colors.white
                                : AppColors.textSecondary,
                            fontWeight: isSelected
                                ? FontWeight.w600
                                : FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
      ],
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

  Widget _buildPrioritySelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Priority',
          style: AppTypography.caption.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            _buildPriorityChip(Priority.low, LucideIcons.arrowDown),
            const SizedBox(width: 10),
            _buildPriorityChip(Priority.medium, LucideIcons.minus),
            const SizedBox(width: 10),
            _buildPriorityChip(Priority.high, LucideIcons.arrowUp),
          ],
        ),
      ],
    );
  }

  Widget _buildPriorityChip(Priority priority, IconData icon) {
    final isSelected = _priority == priority;

    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _priority = priority),
        child: AnimatedContainer(
          duration: AppDurations.fast,
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
          decoration: BoxDecoration(
            color: isSelected
                ? priority.color.withValues(alpha: 0.15)
                : AppColors.gray50,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected ? priority.color : AppColors.border,
              width: isSelected ? 2 : 1,
            ),
          ),
          child: FittedBox(
            fit: BoxFit.scaleDown,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  icon,
                  size: 16,
                  color: isSelected ? priority.color : AppColors.gray500,
                ),
                const SizedBox(width: 6),
                Text(
                  priority.label,
                  style: AppTypography.label.copyWith(
                    color: isSelected ? priority.color : AppColors.textSecondary,
                    fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDueDatePicker() {
    return GestureDetector(
      onTap: _selectDueDate,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: _dueDate != null
              ? AppColors.primary50
              : AppColors.gray50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: _dueDate != null
                ? AppColors.primary300
                : AppColors.border,
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: _dueDate != null
                    ? AppColors.primary100
                    : AppColors.gray100,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                LucideIcons.calendar,
                size: 20,
                color: _dueDate != null
                    ? AppColors.primary600
                    : AppColors.gray500,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _dueDate != null ? 'Due Date' : 'Add Due Date',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                  if (_dueDate != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      _formatDisplayDate(_dueDate!),
                      style: AppTypography.label.copyWith(
                        color: AppColors.primary700,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (_dueDate != null)
              GestureDetector(
                onTap: () => setState(() => _dueDate = null),
                child: Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: AppColors.gray100,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    LucideIcons.x,
                    size: 14,
                    color: AppColors.gray600,
                  ),
                ),
              )
            else
              Icon(
                LucideIcons.chevronRight,
                size: 20,
                color: AppColors.textTertiary,
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _selectDueDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _dueDate ?? now,
      firstDate: DateTime(now.year - 1),
      lastDate: DateTime(now.year + 5),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: ColorScheme.light(
              primary: AppColors.primary600,
              onPrimary: Colors.white,
              surface: AppColors.surface,
              onSurface: AppColors.textPrimary,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      setState(() => _dueDate = picked);
    }
  }

  String _formatDisplayDate(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final taskDate = DateTime(date.year, date.month, date.day);
    final tomorrow = today.add(const Duration(days: 1));

    if (taskDate == today) {
      return 'Today';
    } else if (taskDate == tomorrow) {
      return 'Tomorrow';
    } else {
      final months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      return '${months[date.month - 1]} ${date.day}, ${date.year}';
    }
  }
}
