import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/lookup_models.dart';
import '../../data/models/models.dart';
import '../../providers/deals_provider.dart';
import '../../providers/leads_provider.dart';
import '../../providers/lookup_provider.dart';
import '../../providers/tasks_provider.dart';
import '../../providers/tickets_provider.dart';
import '../../widgets/common/common.dart';
import '../../widgets/forms/custom_fields_form.dart';
import '../../widgets/forms/multi_select_sheet.dart';

/// One of the four parent entities a task can be linked to. The backend's
/// `Task.clean()` invariant enforces at most one is set.
enum _RelatedKind {
  account('account', 'Account', LucideIcons.building2),
  lead('lead', 'Lead', LucideIcons.user),
  opportunity('opportunity', 'Opportunity', LucideIcons.trendingUp),
  ticket('case', 'Ticket', LucideIcons.lifeBuoy);

  final String apiValue;
  final String label;
  final IconData icon;
  const _RelatedKind(this.apiValue, this.label, this.icon);
}

/// Task Form Screen - Reusable for both Create and Edit
class TaskFormScreen extends ConsumerStatefulWidget {
  final String? taskId;
  final Task? initialTask;

  /// Day to pre-fill on a new task, from the calendar cell the user tapped.
  /// Ignored in edit mode, where the task's own due date wins.
  final DateTime? initialDueDate;

  const TaskFormScreen({
    super.key,
    this.taskId,
    this.initialTask,
    this.initialDueDate,
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
  List<String> _assigneeIds = [];
  _RelatedKind? _relatedKind;
  String? _relatedId;
  Map<String, dynamic> _customFields = {};
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
    } else {
      _dueDate = widget.initialDueDate;
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

    final task = await ref
        .read(tasksProvider.notifier)
        .getTaskById(widget.taskId!);

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
    _assigneeIds = List<String>.from(task.assignedToIds);
    _customFields = Map<String, dynamic>.from(task.customFields);
    if (task.accountId != null) {
      _relatedKind = _RelatedKind.account;
      _relatedId = task.accountId;
    } else if (task.leadId != null) {
      _relatedKind = _RelatedKind.lead;
      _relatedId = task.leadId;
    } else if (task.opportunityId != null) {
      _relatedKind = _RelatedKind.opportunity;
      _relatedId = task.opportunityId;
    } else if (task.caseId != null) {
      _relatedKind = _RelatedKind.ticket;
      _relatedId = task.caseId;
    }
  }

  // Resolve the label for the currently-linked entity from cached lookup
  // providers. The TaskSerializer returns FKs as plain UUIDs (not nested
  // objects), so we have no embedded name on the edit fetch. We look it up
  // in the same provider used by the picker. Returns null if the cache
  // doesn't have it yet (provider not loaded); the UI falls back to a
  // generic "Selected" hint until the provider warms up.
  String? _resolveRelatedLabel() {
    final id = _relatedId;
    final kind = _relatedKind;
    if (id == null || kind == null) return null;
    switch (kind) {
      case _RelatedKind.account:
        for (final a in ref.watch(accountsProvider)) {
          if (a.id == id) return a.name;
        }
        return null;
      case _RelatedKind.lead:
        for (final l in ref.watch(leadsListProvider)) {
          if (l.id == id) {
            final n = '${l.firstName} ${l.lastName}'.trim();
            return n.isEmpty ? l.email : n;
          }
        }
        return null;
      case _RelatedKind.opportunity:
        for (final d in ref.watch(dealsListProvider)) {
          if (d.id == id) return d.title;
        }
        return null;
      case _RelatedKind.ticket:
        for (final t in ref.watch(ticketsListProvider)) {
          if (t.id == id) return t.name;
        }
        return null;
    }
  }

  bool get _hasUnsavedChanges {
    if (_existingTask != null) {
      final t = _existingTask!;
      return _titleController.text != t.title ||
          _descriptionController.text != (t.description ?? '') ||
          _status != t.status ||
          _priority != t.priority ||
          _dueDate != t.dueDate ||
          !_listEq(_assigneeIds, t.assignedToIds) ||
          _relatedId != _existingRelatedId(t) ||
          !_mapEq(_customFields, t.customFields);
    }
    return _titleController.text.isNotEmpty ||
        _descriptionController.text.isNotEmpty ||
        _dueDate != null ||
        _assigneeIds.isNotEmpty ||
        _relatedId != null ||
        _customFields.isNotEmpty;
  }

  String? _existingRelatedId(Task t) =>
      t.accountId ?? t.leadId ?? t.opportunityId ?? t.caseId;

  bool _listEq(List<String> a, List<String> b) {
    if (a.length != b.length) return false;
    final sa = [...a]..sort();
    final sb = [...b]..sort();
    for (var i = 0; i < sa.length; i++) {
      if (sa[i] != sb[i]) return false;
    }
    return true;
  }

  bool _mapEq(Map<String, dynamic> a, Map<String, dynamic> b) {
    if (a.length != b.length) return false;
    for (final k in a.keys) {
      if (!b.containsKey(k) || a[k] != b[k]) return false;
    }
    return true;
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
    final payload = <String, dynamic>{
      'title': _titleController.text.trim(),
      'description': _descriptionController.text.trim().isEmpty
          ? null
          : _descriptionController.text.trim(),
      'status': _status.value,
      'priority': _priority.label,
      'due_date': _dueDate?.toIso8601String().split('T').first,
      'assigned_to': _assigneeIds,
      'custom_fields': _customFields,
    };
    // Send exactly one parent FK and clear the others. Backend's
    // `Task.clean()` rejects multi-parent. On PUT, sending `null` for an
    // unset slot is how the view detects "clear this FK" (task_views.py).
    for (final k in _RelatedKind.values) {
      payload[k.apiValue] = (_relatedKind == k) ? _relatedId : null;
    }
    return payload;
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
            content: Text(
              widget.isEditMode
                  ? 'Task updated successfully'
                  : 'Task created successfully',
            ),
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
      return const Center(child: CircularProgressIndicator());
    }

    if (_fetchError != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(LucideIcons.alertCircle, size: 48, color: AppColors.danger500),
            const SizedBox(height: 16),
            Text(
              _fetchError!,
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 16),
            TextButton(onPressed: _fetchTask, child: const Text('Retry')),
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

            // People Section
            _buildSectionTitle('People'),
            const SizedBox(height: 16),
            _buildAssigneesField(),

            const SizedBox(height: 24),

            // Linked Record Section
            _buildSectionTitle('Linked Record'),
            const SizedBox(height: 16),
            _buildRelatedField(),

            const SizedBox(height: 24),

            // Custom Fields Section (renders nothing if the org has none)
            _buildCustomFieldsSection(),

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
      maxLength: 200,
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
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
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
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
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
                    color: isSelected
                        ? priority.color
                        : AppColors.textSecondary,
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
          color: _dueDate != null ? AppColors.primary50 : AppColors.gray50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: _dueDate != null ? AppColors.primary300 : AppColors.border,
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
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December',
      ];
      return '${months[date.month - 1]} ${date.day}, ${date.year}';
    }
  }

  Widget _buildAssigneesField() {
    final users = ref.watch(usersProvider);
    final selected = users.where((u) => _assigneeIds.contains(u.id)).toList();
    return _PickerRow(
      label: 'Assigned to',
      icon: LucideIcons.users,
      placeholder: 'No one assigned',
      onTap: () => _pickAssignees(users),
      child: selected.isEmpty
          ? null
          : Wrap(
              spacing: 6,
              runSpacing: 4,
              children: [
                for (final u in selected) LabelPill(label: u.displayName),
              ],
            ),
    );
  }

  Future<void> _pickAssignees(List<UserLookup> users) async {
    final initial = users.where((u) => _assigneeIds.contains(u.id)).toList();
    final result = await MultiSelectSheet.show<UserLookup>(
      context: context,
      title: 'Assigned to',
      items: users,
      initialSelection: initial,
      labelOf: (u) => u.displayName,
      searchText: (u) => '${u.email} ${u.displayName}',
      leadingOf: (u) => UserAvatar(name: u.displayName, size: AvatarSize.xs),
      emptyMessage: 'No users found',
    );
    if (result != null) {
      setState(() => _assigneeIds = result.map((u) => u.id).toList());
    }
  }

  Widget _buildRelatedField() {
    final label = _resolveRelatedLabel();
    final displayValue = _relatedKind == null
        ? null
        : '${_relatedKind!.label}: ${label ?? "Selected"}';
    return _PickerRow(
      label: 'Linked record',
      icon: _relatedKind?.icon ?? LucideIcons.link2,
      placeholder: 'Not linked',
      onTap: _pickRelated,
      onClear: _relatedKind == null
          ? null
          : () => setState(() {
              _relatedKind = null;
              _relatedId = null;
            }),
      child: displayValue == null
          ? null
          : Text(
              displayValue,
              style: AppTypography.body.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w500,
              ),
            ),
    );
  }

  Future<void> _pickRelated() async {
    final picked = await showModalBottomSheet<_RelatedKind>(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
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
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text('Link to…', style: AppTypography.h3),
            ),
            for (final k in _RelatedKind.values)
              InkWell(
                onTap: () => Navigator.pop(ctx, k),
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 14,
                  ),
                  child: Row(
                    children: [
                      Icon(k.icon, size: 20, color: AppColors.textSecondary),
                      const SizedBox(width: 14),
                      Text(k.label, style: AppTypography.body),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
    if (picked == null || !mounted) return;
    await _pickEntityForKind(picked);
  }

  Future<void> _pickEntityForKind(_RelatedKind kind) async {
    switch (kind) {
      case _RelatedKind.account:
        final accounts = ref.read(accountsProvider);
        final pick = await _pickFromList<AccountLookup>(
          title: 'Select Account',
          items: accounts,
          labelOf: (a) => a.name,
          icon: LucideIcons.building2,
        );
        if (pick != null) {
          setState(() {
            _relatedKind = kind;
            _relatedId = pick.id;
          });
        }
        break;
      case _RelatedKind.lead:
        final leads = ref.read(leadsListProvider);
        final pick = await _pickFromList<Lead>(
          title: 'Select Lead',
          items: leads,
          labelOf: (l) {
            final n = '${l.firstName} ${l.lastName}'.trim();
            return n.isEmpty ? l.email : n;
          },
          icon: LucideIcons.user,
        );
        if (pick != null) {
          setState(() {
            _relatedKind = kind;
            _relatedId = pick.id;
          });
        }
        break;
      case _RelatedKind.opportunity:
        final deals = ref.read(dealsListProvider);
        final pick = await _pickFromList<Deal>(
          title: 'Select Opportunity',
          items: deals,
          labelOf: (d) => d.title,
          icon: LucideIcons.trendingUp,
        );
        if (pick != null) {
          setState(() {
            _relatedKind = kind;
            _relatedId = pick.id;
          });
        }
        break;
      case _RelatedKind.ticket:
        final tickets = ref.read(ticketsListProvider);
        final pick = await _pickFromList<Ticket>(
          title: 'Select Ticket',
          items: tickets,
          labelOf: (t) => t.name,
          icon: LucideIcons.lifeBuoy,
        );
        if (pick != null) {
          setState(() {
            _relatedKind = kind;
            _relatedId = pick.id;
          });
        }
        break;
    }
  }

  Future<T?> _pickFromList<T>({
    required String title,
    required List<T> items,
    required String Function(T) labelOf,
    required IconData icon,
  }) {
    return showModalBottomSheet<T>(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.4,
        maxChildSize: 0.95,
        expand: false,
        builder: (_, controller) => Column(
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
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(title, style: AppTypography.h3),
            ),
            Expanded(
              child: items.isEmpty
                  ? const Center(
                      child: EmptyState(
                        icon: LucideIcons.inbox,
                        title: 'Nothing to pick',
                        description:
                            'Open this section on the web or create one first.',
                      ),
                    )
                  : ListView.builder(
                      controller: controller,
                      itemCount: items.length,
                      itemBuilder: (_, i) {
                        final item = items[i];
                        return InkWell(
                          onTap: () => Navigator.pop(ctx, item),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 14,
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  icon,
                                  size: 18,
                                  color: AppColors.textSecondary,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    labelOf(item),
                                    style: AppTypography.body,
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
        ),
      ),
    );
  }

  Widget _buildCustomFieldsSection() {
    return Consumer(
      builder: (context, ref, _) {
        final asyncDefs = ref.watch(customFieldDefinitionsProvider('Task'));
        final defs = asyncDefs.value ?? const [];
        if (defs.isEmpty) return const SizedBox.shrink();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionTitle('Custom Fields'),
            const SizedBox(height: 16),
            CustomFieldsForm(
              targetModel: 'Task',
              values: _customFields,
              onChanged: (v) => setState(() => _customFields = v),
            ),
            const SizedBox(height: 24),
          ],
        );
      },
    );
  }
}

/// Shared "tap to open picker" tile used by Assigned-to and Linked-record.
class _PickerRow extends StatelessWidget {
  final String label;
  final IconData icon;
  final String placeholder;
  final VoidCallback onTap;
  final VoidCallback? onClear;
  final Widget? child;

  const _PickerRow({
    required this.label,
    required this.icon,
    required this.placeholder,
    required this.onTap,
    this.onClear,
    this.child,
  });

  @override
  Widget build(BuildContext context) {
    final hasValue = child != null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: onTap,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: hasValue ? AppColors.primary50 : AppColors.gray50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: hasValue ? AppColors.primary300 : AppColors.border,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  icon,
                  size: 20,
                  color: hasValue
                      ? AppColors.primary600
                      : AppColors.textSecondary,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child:
                      child ??
                      Text(
                        placeholder,
                        style: AppTypography.body.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                ),
                if (hasValue && onClear != null)
                  GestureDetector(
                    onTap: onClear,
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
        ),
      ],
    );
  }
}
