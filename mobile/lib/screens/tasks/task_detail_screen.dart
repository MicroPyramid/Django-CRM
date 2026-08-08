import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/deals_provider.dart';
import '../../providers/leads_provider.dart';
import '../../providers/lookup_provider.dart';
import '../../providers/tasks_provider.dart';
import '../../providers/tickets_provider.dart';
import '../../config/api_config.dart';
import '../../services/attachment_upload.dart';
import '../../widgets/common/common.dart';

/// Task Detail Screen
/// Shows task info with actions: Edit, Complete, Delete
class TaskDetailScreen extends ConsumerStatefulWidget {
  final String taskId;

  const TaskDetailScreen({super.key, required this.taskId});

  @override
  ConsumerState<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends ConsumerState<TaskDetailScreen> {
  TaskDetailResult? _detail;
  bool _isLoading = true;
  bool _isUpdating = false;
  bool _isPostingComment = false;
  bool _isUploadingAttachment = false;
  String? _error;

  final TextEditingController _commentController = TextEditingController();
  final FocusNode _commentFocus = FocusNode();

  Task? get _task => _detail?.task;

  @override
  void initState() {
    super.initState();
    _fetchTask();
  }

  @override
  void dispose() {
    _commentController.dispose();
    _commentFocus.dispose();
    super.dispose();
  }

  Future<void> _fetchTask() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final detail = await ref
        .read(tasksProvider.notifier)
        .getTaskDetail(widget.taskId);

    if (mounted) {
      setState(() {
        _isLoading = false;
        _detail = detail;
        if (detail == null) {
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
        body: const Center(child: CircularProgressIndicator()),
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
              Icon(LucideIcons.fileX, size: 48, color: AppColors.gray400),
              const SizedBox(height: 16),
              Text('Task not found', style: AppTypography.h3),
              const SizedBox(height: 8),
              Text(
                _error ?? 'This task may have been deleted',
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 16),
              TextButton(onPressed: _fetchTask, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.surface,
      // Body is a Column so the composer + action button can live at the
      // bottom of the body proper, *outside* the sliver scroll view. Putting
      // a TextField inside a Scaffold.bottomNavigationBar slot didn't reliably
      // raise the soft keyboard on Android. This layout does.
      body: Column(
        children: [
          Expanded(
            child: CustomScrollView(
              slivers: [
                _buildSliverAppBar(),
                SliverToBoxAdapter(child: _buildContent()),
              ],
            ),
          ),
          _buildBottomActions(),
        ],
      ),
    );
  }

  Widget _buildSliverAppBar() {
    return SliverAppBar(
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
      flexibleSpace: FlexibleSpaceBar(background: _buildHeader()),
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
          colors: [_getHeaderColor(), _getHeaderColor().withValues(alpha: 0.7)],
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
                  PriorityBadge.fromPriority(_task!.priority),
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
          Icon(_getStatusIcon(_task!.status), size: 14, color: Colors.white),
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
    final task = _task!;
    final related = _resolveRelatedEntity();
    final defs =
        _detail?.customFieldDefinitions ?? const <CustomFieldDefinition>[];
    final comments = _detail?.comments ?? const <Comment>[];
    final attachments = _detail?.attachments ?? const <Attachment>[];
    final createdByLabel = task.createdByName?.isNotEmpty == true
        ? task.createdByName!
        : (task.createdByEmail ?? '');

    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (task.description != null && task.description!.isNotEmpty) ...[
            _buildCard(
              title: 'Description',
              icon: LucideIcons.fileText,
              child: Text(
                task.description!,
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                  height: 1.6,
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],

          if (related != null) ...[
            _buildRelatedCard(related),
            const SizedBox(height: 16),
          ],

          if (task.assignedTo != null && task.assignedTo!.isNotEmpty) ...[
            _buildCard(
              title: 'Assigned To',
              icon: LucideIcons.user,
              child: _buildAssigneesList(task.assignedTo!),
            ),
            const SizedBox(height: 16),
          ],

          if (task.teamNames.isNotEmpty) ...[
            _buildCard(
              title: 'Teams',
              icon: LucideIcons.users,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: task.teamNames
                    .map((name) => LabelPill(label: name))
                    .toList(),
              ),
            ),
            const SizedBox(height: 16),
          ],

          if (task.tags.isNotEmpty) ...[
            _buildCard(
              title: 'Tags',
              icon: LucideIcons.tag,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: task.tags
                    .map((tag) => LabelPill(label: tag))
                    .toList(),
              ),
            ),
            const SizedBox(height: 16),
          ],

          if (defs.any((d) => _cfValueOf(d).isNotEmpty)) ...[
            _buildCard(
              title: 'Custom Fields',
              icon: LucideIcons.listChecks,
              child: Column(children: _buildCustomFieldRows(defs)),
            ),
            const SizedBox(height: 16),
          ],

          _buildCommentsCard(comments),
          const SizedBox(height: 16),

          // Shown even when empty, now that there is something to do here.
          // While the section only listed files, an empty one was noise; the
          // Attach button is the reason to render it.
          _buildCard(
            title: 'Attachments',
            icon: LucideIcons.paperclip,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (var i = 0; i < attachments.length; i++) ...[
                  if (i > 0) const Divider(height: 16),
                  _buildAttachmentRow(attachments[i]),
                ],
                if (attachments.isEmpty)
                  Text(
                    'No files yet.',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                const SizedBox(height: 12),
                AttachFileButton(
                  isUploading: _isUploadingAttachment,
                  onPressed: _pickAndUploadAttachment,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          _buildCard(
            title: 'Details',
            icon: LucideIcons.info,
            child: Column(
              children: [
                _buildInfoRow(
                  'Created',
                  _formatDateTime(task.createdAt),
                  LucideIcons.plus,
                ),
                if (createdByLabel.isNotEmpty) ...[
                  const Divider(height: 20),
                  _buildInfoRow('Created by', createdByLabel, LucideIcons.user),
                ],
                if (task.updatedAt != null) ...[
                  const Divider(height: 20),
                  _buildInfoRow(
                    'Last Updated',
                    _formatDateTime(task.updatedAt!),
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

  /// Resolve the linked parent entity (account / lead / opportunity / case)
  /// from the cached lookup providers. The backend serializes these FKs as
  /// plain UUID strings, not nested objects, so without this lookup the
  /// "Related To" card silently disappears even when a parent IS attached.
  _RelatedRef? _resolveRelatedEntity() {
    final t = _task;
    if (t == null) return null;

    if (t.accountId != null) {
      String label = 'Selected account';
      for (final a in ref.watch(accountOptionsProvider)) {
        if (a.id == t.accountId) {
          label = a.name;
          break;
        }
      }
      // No /accounts/:id route on mobile yet. Show the card, but don't fake
      // a chevron the user can't follow.
      return _RelatedRef(
        typeLabel: 'Account',
        icon: LucideIcons.building,
        label: label,
        path: null,
      );
    }
    if (t.leadId != null) {
      String label = 'Selected lead';
      for (final l in ref.watch(leadsListProvider)) {
        if (l.id == t.leadId) {
          final n = '${l.firstName} ${l.lastName}'.trim();
          label = n.isEmpty ? (l.email) : n;
          break;
        }
      }
      return _RelatedRef(
        typeLabel: 'Lead',
        icon: LucideIcons.userPlus,
        label: label,
        path: '/leads/${t.leadId}',
      );
    }
    if (t.opportunityId != null) {
      String label = 'Selected deal';
      for (final d in ref.watch(dealsListProvider)) {
        if (d.id == t.opportunityId) {
          label = d.title;
          break;
        }
      }
      return _RelatedRef(
        typeLabel: 'Opportunity',
        icon: LucideIcons.trendingUp,
        label: label,
        path: '/deals/${t.opportunityId}',
      );
    }
    if (t.caseId != null) {
      String label = 'Selected ticket';
      for (final c in ref.watch(ticketsListProvider)) {
        if (c.id == t.caseId) {
          label = c.name;
          break;
        }
      }
      return _RelatedRef(
        typeLabel: 'Ticket',
        icon: LucideIcons.lifeBuoy,
        label: label,
        path: '/tickets/${t.caseId}',
      );
    }
    return null;
  }

  Widget _buildRelatedCard(_RelatedRef r) {
    return _buildCard(
      title: 'Related To',
      icon: LucideIcons.link2,
      child: InkWell(
        onTap: r.path == null ? null : () => context.push(r.path!),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppColors.primary100,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(r.icon, size: 20, color: AppColors.primary600),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      r.typeLabel,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    Text(r.label, style: AppTypography.label),
                  ],
                ),
              ),
              if (r.path != null)
                Icon(
                  LucideIcons.chevronRight,
                  size: 20,
                  color: AppColors.textTertiary,
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAssigneesList(List<Map<String, dynamic>> assignees) {
    return Column(
      children: [
        for (var i = 0; i < assignees.length; i++) ...[
          if (i > 0) const SizedBox(height: 12),
          Row(
            children: [
              UserAvatar(
                name: _assigneeDisplayName(assignees[i]),
                size: AvatarSize.sm,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  _assigneeDisplayName(assignees[i]),
                  style: AppTypography.label,
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }

  String _assigneeDisplayName(Map<String, dynamic> profile) {
    // ProfileSerializer wraps the user under `user_details` ({email, name, …}).
    // Some older endpoints still return user__email at the top level. Keep
    // that fallback so a payload shape change doesn't blank out the avatar.
    final details = profile['user_details'];
    String? email;
    String? name;
    if (details is Map<String, dynamic>) {
      email = details['email'] as String?;
      name = (details['name'] as String?)?.trim();
    }
    email ??= profile['user__email'] as String?;
    if (name != null && name.isNotEmpty) return name;
    if (email != null && email.isNotEmpty) return email.split('@').first;
    return 'Unassigned';
  }

  /// Render the raw value stored under `custom_fields[def.key]` as a
  /// display string. Empty / missing values return '' so the caller can
  /// skip them.
  String _cfValueOf(CustomFieldDefinition def) {
    final raw = _task?.customFields[def.key];
    if (raw == null) return '';
    if (raw is bool) return raw ? 'Yes' : 'No';
    if (raw is List) return raw.join(', ');
    final s = raw.toString();
    return s;
  }

  List<Widget> _buildCustomFieldRows(List<CustomFieldDefinition> defs) {
    final rows = <Widget>[];
    for (final def in defs) {
      final value = _cfValueOf(def);
      if (value.isEmpty) continue;
      if (rows.isNotEmpty) rows.add(const Divider(height: 20));
      rows.add(_buildInfoRow(def.label, value, LucideIcons.tag));
    }
    return rows;
  }

  Widget _buildCommentsCard(List<Comment> comments) {
    // The composer lives in the bottomNavigationBar (see _buildBottomActions);
    // putting it here too caused focus/keyboard issues when the sliver
    // viewport pushed it offscreen on tap.
    return _buildCard(
      title: 'Comments',
      icon: LucideIcons.messageCircle,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (comments.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Text(
                'No comments yet. Use the box below to add one.',
                style: AppTypography.body.copyWith(
                  color: AppColors.textTertiary,
                ),
              ),
            )
          else
            Column(
              children: [
                for (var i = 0; i < comments.length; i++) ...[
                  if (i > 0) const SizedBox(height: 10),
                  _buildCommentTile(comments[i]),
                ],
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildCommentTile(Comment comment) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.gray50,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            comment.comment,
            style: AppTypography.body.copyWith(
              color: AppColors.textPrimary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              UserAvatar(name: comment.authorName, size: AvatarSize.xs),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  comment.authorName,
                  style: AppTypography.caption.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              Text(
                _formatTimeAgo(comment.commentedOn),
                style: AppTypography.caption.copyWith(
                  color: AppColors.textTertiary,
                ),
              ),
              IconButton(
                visualDensity: VisualDensity.compact,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                icon: Icon(
                  LucideIcons.trash2,
                  size: 14,
                  color: AppColors.textTertiary,
                ),
                onPressed: () => _confirmDeleteComment(comment),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCommentComposer() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: TextField(
            controller: _commentController,
            focusNode: _commentFocus,
            enabled: !_isPostingComment,
            minLines: 1,
            maxLines: 4,
            keyboardType: TextInputType.multiline,
            textInputAction: TextInputAction.newline,
            decoration: InputDecoration(
              hintText: 'Add a comment…',
              hintStyle: AppTypography.body.copyWith(
                color: AppColors.textTertiary,
              ),
              filled: true,
              fillColor: AppColors.gray100,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 14,
                vertical: 10,
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(20),
                borderSide: BorderSide.none,
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Material(
          color: _isPostingComment ? AppColors.gray400 : AppColors.primary600,
          shape: const CircleBorder(),
          child: InkWell(
            customBorder: const CircleBorder(),
            onTap: _isPostingComment ? null : _addComment,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: _isPostingComment
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(LucideIcons.send, color: Colors.white, size: 18),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildAttachmentRow(Attachment att) {
    return InkWell(
      onTap: att.hasFile ? () => _openAttachment(att) : null,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppColors.primary50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                LucideIcons.file,
                size: 18,
                color: AppColors.primary600,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    att.fileName,
                    style: AppTypography.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (att.createdBy != null && att.createdBy!.isNotEmpty)
                    Text(
                      att.createdBy!,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textTertiary,
                      ),
                    ),
                ],
              ),
            ),
            IconButton(
              visualDensity: VisualDensity.compact,
              icon: Icon(
                LucideIcons.trash2,
                size: 16,
                color: AppColors.textTertiary,
              ),
              onPressed: () => _confirmDeleteAttachment(att),
            ),
          ],
        ),
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
              Icon(icon, size: 16, color: AppColors.textTertiary),
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
        Icon(icon, size: 16, color: AppColors.gray400),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            label,
            style: AppTypography.body.copyWith(color: AppColors.textSecondary),
          ),
        ),
        Text(
          value,
          style: AppTypography.label.copyWith(color: AppColors.textPrimary),
        ),
      ],
    );
  }

  Widget _buildBottomActions() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
              child: _buildCommentComposer(),
            ),
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              child: Row(
                children: [
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
          ],
        ),
      ),
    );
  }

  Future<void> _toggleTaskStatus() async {
    if (_task == null || _isUpdating) return;

    setState(() => _isUpdating = true);

    final response = await ref
        .read(tasksProvider.notifier)
        .toggleTaskStatus(_task!);

    if (mounted) {
      setState(() => _isUpdating = false);

      if (response.success) {
        await _fetchTask();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                _task!.completed
                    ? 'Task marked as incomplete'
                    : 'Task completed',
              ),
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
                final result = await context.push(
                  '/tasks/${widget.taskId}/edit',
                );
                if (result == true && mounted) {
                  _fetchTask();
                }
              },
            ),
            ListTile(
              leading: Icon(
                _task!.completed
                    ? LucideIcons.rotateCcw
                    : LucideIcons.checkCircle2,
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
            child: Text('Delete', style: TextStyle(color: AppColors.danger600)),
          ),
        ],
      ),
    );
  }

  Future<void> _deleteTask() async {
    setState(() => _isUpdating = true);

    final response = await ref
        .read(tasksProvider.notifier)
        .deleteTask(widget.taskId);

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

  Future<void> _addComment() async {
    final text = _commentController.text.trim();
    if (text.isEmpty) return;
    setState(() => _isPostingComment = true);
    final response = await ref
        .read(tasksProvider.notifier)
        .addTaskComment(widget.taskId, text);
    if (!mounted) return;
    if (!response.success) {
      setState(() => _isPostingComment = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(response.message ?? 'Failed to add comment'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: AppColors.danger600,
        ),
      );
      return;
    }
    _commentController.clear();

    // Use the POST response directly. It returns the refreshed comments and
    // attachments. The previous _fetchTask() refetch flashed the full-page
    // spinner (since _fetchTask always sets _isLoading=true) and would
    // silently fail if getTaskDetail returned null, leaving the new comment
    // invisible even though the server saved it.
    final data = response.data;
    final commentsData = data?['comments'];
    final attachmentsData = data?['attachments'];
    if (_detail != null && commentsData is List) {
      final newComments = commentsData
          .whereType<Map<String, dynamic>>()
          .map(Comment.fromJson)
          .toList();
      final newAttachments = attachmentsData is List
          ? attachmentsData
                .whereType<Map<String, dynamic>>()
                .map(Attachment.fromJson)
                .toList()
          : _detail!.attachments;
      setState(() {
        _detail = _detail!.copyWith(
          comments: newComments,
          attachments: newAttachments,
        );
        _isPostingComment = false;
      });
    } else {
      // Response shape unexpected, fall back to refetch.
      await _fetchTask();
      if (mounted) setState(() => _isPostingComment = false);
    }
  }

  void _confirmDeleteComment(Comment comment) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Delete comment?'),
        content: const Text('This cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(dialogContext);
              final response = await ref
                  .read(tasksProvider.notifier)
                  .deleteTaskComment(comment.id);
              if (!mounted) return;
              if (response.success || response.statusCode == 204) {
                if (_detail != null) {
                  setState(() {
                    _detail = _detail!.copyWith(
                      comments: _detail!.comments
                          .where((c) => c.id != comment.id)
                          .toList(),
                    );
                  });
                }
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(response.message ?? 'Delete failed'),
                    behavior: SnackBarBehavior.floating,
                    backgroundColor: AppColors.danger600,
                  ),
                );
              }
            },
            child: Text('Delete', style: TextStyle(color: AppColors.danger600)),
          ),
        ],
      ),
    );
  }

  void _confirmDeleteAttachment(Attachment att) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Delete attachment?'),
        content: Text('Remove "${att.fileName}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(dialogContext);
              final response = await ref
                  .read(tasksProvider.notifier)
                  .deleteTaskAttachment(att.id);
              if (!mounted) return;
              if (response.success || response.statusCode == 204) {
                if (_detail != null) {
                  setState(() {
                    _detail = _detail!.copyWith(
                      attachments: _detail!.attachments
                          .where((a) => a.id != att.id)
                          .toList(),
                    );
                  });
                }
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(response.message ?? 'Delete failed'),
                    behavior: SnackBarBehavior.floating,
                    backgroundColor: AppColors.danger600,
                  ),
                );
              }
            },
            child: Text('Delete', style: TextStyle(color: AppColors.danger600)),
          ),
        ],
      ),
    );
  }

  /// Attach a file to this task.
  ///
  /// The detail POST answers with the refreshed `attachments` array, the same
  /// way it does for a comment, so the list updates in place. Refetching would
  /// throw the page back to its spinner and lose the scroll position.
  Future<void> _pickAndUploadAttachment() async {
    if (_isUploadingAttachment || _detail == null) return;
    setState(() => _isUploadingAttachment = true);

    final result = await pickAndUploadAttachment(
      target: AttachmentTarget.task,
      recordId: widget.taskId,
    );

    if (!mounted) return;
    setState(() => _isUploadingAttachment = false);

    if (result.cancelled) return;
    if (!result.succeeded) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.error!),
          behavior: SnackBarBehavior.floating,
          backgroundColor: AppColors.danger600,
        ),
      );
      return;
    }

    final attachmentsData = result.data?['attachments'];
    if (_detail != null && attachmentsData is List) {
      setState(() {
        _detail = _detail!.copyWith(
          attachments: attachmentsData
              .whereType<Map<String, dynamic>>()
              .map(Attachment.fromJson)
              .toList(),
        );
      });
    } else {
      // The upload landed but the shape was not what this expects. Refetching
      // is slower than the in-place update and is never wrong.
      await _fetchTask();
    }
  }

  /// Download an attachment through the API, with the token attached. See the
  /// note on `Attachment.filePath` for why the stored path is not a URL.
  Future<void> _openAttachment(Attachment att) async {
    if (!att.hasFile) return;
    final result = await downloadAttachment(
      url: ApiConfig.attachmentDownload(att.id),
      fileName: att.fileName,
    );
    if (!mounted || result.success) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(result.error ?? 'Could not download that file.'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  String _formatTimeAgo(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inDays > 30) return '${(diff.inDays / 30).floor()}mo ago';
    if (diff.inDays > 0) return '${diff.inDays}d ago';
    if (diff.inHours > 0) return '${diff.inHours}h ago';
    if (diff.inMinutes > 0) return '${diff.inMinutes}m ago';
    return 'Just now';
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
        'Jan',
        'Feb',
        'Mar',
        'Apr',
        'May',
        'Jun',
        'Jul',
        'Aug',
        'Sep',
        'Oct',
        'Nov',
        'Dec',
      ];
      return 'Due ${months[date.month - 1]} ${date.day}, ${date.year}';
    }
  }

  String _formatDateTime(DateTime date) {
    final months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }
}

/// Resolved parent-entity reference for the Related-To card. `path` is null
/// when the mobile app has no detail screen for that entity type (e.g.
/// accounts), the card renders without a chevron in that case.
class _RelatedRef {
  final String typeLabel;
  final IconData icon;
  final String label;
  final String? path;

  const _RelatedRef({
    required this.typeLabel,
    required this.icon,
    required this.label,
    required this.path,
  });
}
