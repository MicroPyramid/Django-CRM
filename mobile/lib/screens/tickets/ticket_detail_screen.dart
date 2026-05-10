import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/ticket.dart';
import '../../data/models/comment.dart';
import '../../providers/tickets_provider.dart';
import '../../widgets/common/common.dart';

/// Ticket Detail Screen — Overview / Comments / Activity tabs.
class TicketDetailScreen extends ConsumerStatefulWidget {
  final String ticketId;

  const TicketDetailScreen({super.key, required this.ticketId});

  @override
  ConsumerState<TicketDetailScreen> createState() => _TicketDetailScreenState();
}

class _TicketDetailScreenState extends ConsumerState<TicketDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _commentController = TextEditingController();

  TicketDetailResult? _detail;
  bool _isLoading = true;
  bool _isAddingComment = false;
  bool _isInternalNote = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _fetchDetail();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _fetchDetail() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    final detail = await ref
        .read(ticketsProvider.notifier)
        .getTicketDetail(widget.ticketId);
    if (mounted) {
      setState(() {
        _isLoading = false;
        _detail = detail;
        if (detail == null) _error = 'Failed to load ticket';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
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
    if (_detail == null || _error != null) {
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
              Text('Ticket not found', style: AppTypography.h3),
              const SizedBox(height: 8),
              Text(
                _error ?? 'This ticket may have been deleted',
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 16),
              TextButton(onPressed: _fetchDetail, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }

    final c = _detail!.ticketObj;

    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        leading: IconButton(
          icon: const Icon(LucideIcons.chevronLeft),
          onPressed: () => context.pop(),
        ),
        title: Text(
          c.name,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: AppTypography.h3,
        ),
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.pencil),
            onPressed: () async {
              final result = await context.push(
                '/tickets/${widget.ticketId}/edit',
              );
              if (result == true && mounted) _fetchDetail();
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary600,
          unselectedLabelColor: AppColors.textSecondary,
          indicatorColor: AppColors.primary600,
          indicatorWeight: 2,
          labelStyle: AppTypography.label,
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'Comments'),
            Tab(text: 'Activity'),
          ],
        ),
      ),
      body: Column(
        children: [
          _buildHeaderStrip(c),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildOverview(c),
                _buildCommentsTab(c),
                _buildActivityTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeaderStrip(Ticket c) {
    return Container(
      width: double.infinity,
      color: AppColors.surfaceDim,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Wrap(
        spacing: 8,
        runSpacing: 6,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: c.status.color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              c.status.label,
              style: AppTypography.caption.copyWith(
                color: c.status.color,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: c.priority.color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(LucideIcons.flag, size: 12, color: c.priority.color),
                const SizedBox(width: 4),
                Text(
                  c.priority.label,
                  style: AppTypography.caption.copyWith(
                    color: c.priority.color,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.gray100,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  c.ticketType.icon,
                  size: 12,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(width: 4),
                Text(
                  c.ticketType.label,
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          if (c.isFirstResponseSlaBreached)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.danger100,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    LucideIcons.alertTriangle,
                    size: 12,
                    color: AppColors.danger600,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    'SLA breached',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.danger600,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildOverview(Ticket c) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _card(
            title: 'Ticket Information',
            child: Column(
              children: [
                _InfoRow(
                  icon: LucideIcons.fileText,
                  label: 'NAME',
                  value: c.name,
                ),
                const Divider(height: 24),
                _InfoRow(
                  icon: LucideIcons.building2,
                  label: 'ACCOUNT',
                  value: c.accountName ?? 'No account linked',
                ),
                const Divider(height: 24),
                _InfoRow(
                  icon: LucideIcons.calendar,
                  label: 'CREATED',
                  value: _formatDate(c.createdAt),
                ),
                if (c.closedOn != null) ...[
                  const Divider(height: 24),
                  _InfoRow(
                    icon: LucideIcons.checkCircle,
                    label: 'CLOSED',
                    value: _formatDate(c.closedOn!),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          _card(
            title: 'Assigned To',
            child: Row(
              children: [
                UserAvatar(name: c.assignedToName, size: AvatarSize.md),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(c.assignedToName, style: AppTypography.label),
                ),
              ],
            ),
          ),
          if (c.description != null && c.description!.isNotEmpty) ...[
            const SizedBox(height: 16),
            _card(
              title: 'Description',
              child: Text(
                c.description!,
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
              ),
            ),
          ],
          const SizedBox(height: 100),
        ],
      ),
    );
  }

  Widget _buildCommentsTab(Ticket c) {
    final comments = c.comments;
    final internalIds = _detail?.internalCommentIds ?? const {};

    return Column(
      children: [
        Expanded(
          child: comments.isEmpty
              ? const EmptyState(
                  icon: LucideIcons.messageSquare,
                  title: 'No comments yet',
                  description: 'Add the first comment to get started',
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: comments.length,
                  itemBuilder: (context, i) {
                    final comment = comments[i];
                    return _CommentTile(
                      comment: comment,
                      isInternal: internalIds.contains(comment.id),
                    );
                  },
                ),
        ),
        if (_detail?.commentPermission ?? false) _buildCommentComposer(),
      ],
    );
  }

  Widget _buildCommentComposer() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: SafeArea(
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _commentController,
                    enabled: !_isAddingComment,
                    decoration: InputDecoration(
                      hintText: _isInternalNote
                          ? 'Add an internal note...'
                          : 'Add a comment...',
                      hintStyle: AppTypography.body.copyWith(
                        color: AppColors.textTertiary,
                      ),
                      filled: true,
                      fillColor: AppColors.gray100,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    maxLines: null,
                  ),
                ),
                const SizedBox(width: 12),
                Container(
                  decoration: BoxDecoration(
                    color: _isAddingComment
                        ? AppColors.gray400
                        : (_isInternalNote
                              ? AppColors.warning600
                              : AppColors.primary600),
                    shape: BoxShape.circle,
                  ),
                  child: IconButton(
                    icon: _isAddingComment
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(
                            LucideIcons.send,
                            color: Colors.white,
                            size: 20,
                          ),
                    onPressed: _isAddingComment ? null : _addComment,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Switch(
                  value: _isInternalNote,
                  onChanged: _isAddingComment
                      ? null
                      : (v) => setState(() => _isInternalNote = v),
                ),
                const SizedBox(width: 4),
                Text(
                  'Internal note (not visible to customer)',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _addComment() async {
    final text = _commentController.text.trim();
    if (text.isEmpty) return;
    setState(() => _isAddingComment = true);
    final response = await ref
        .read(ticketsProvider.notifier)
        .addComment(widget.ticketId, text, isInternal: _isInternalNote);
    if (!mounted) return;
    setState(() => _isAddingComment = false);
    if (response.success) {
      _commentController.clear();
      await _fetchDetail();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Comment added'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(response.message ?? 'Failed to add comment'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: AppColors.danger600,
        ),
      );
    }
  }

  Widget _buildActivityTab() {
    final activities = _detail?.activities ?? [];
    if (activities.isEmpty) {
      return const Center(
        child: EmptyState(
          icon: LucideIcons.clock,
          title: 'No activity yet',
          description: 'Status changes and assignments will appear here',
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: activities.length,
      itemBuilder: (context, i) {
        final a = activities[i];
        return _ActivityTile(activity: a);
      },
    );
  }

  Widget _card({required String title, required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppLayout.borderRadiusLg,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: AppTypography.overline.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
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

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 20, color: AppColors.gray400),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: AppTypography.overline.copyWith(
                  color: AppColors.textTertiary,
                  fontSize: 10,
                ),
              ),
              const SizedBox(height: 2),
              Text(value, style: AppTypography.body),
            ],
          ),
        ),
      ],
    );
  }
}

class _CommentTile extends StatelessWidget {
  final Comment comment;
  final bool isInternal;

  const _CommentTile({required this.comment, required this.isInternal});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isInternal ? AppColors.warning50 : AppColors.gray50,
        borderRadius: AppLayout.borderRadiusLg,
        border: Border.all(
          color: isInternal ? AppColors.warning200 : AppColors.border,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (isInternal) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.warning100,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(LucideIcons.lock, size: 11, color: AppColors.warning700),
                  const SizedBox(width: 3),
                  Text(
                    'Internal',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.warning700,
                      fontWeight: FontWeight.w600,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 6),
          ],
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
              Text(
                comment.authorName,
                style: AppTypography.caption.copyWith(
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                _formatTimeAgo(comment.commentedOn),
                style: AppTypography.caption.copyWith(
                  color: AppColors.textTertiary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatTimeAgo(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);
    if (difference.inDays > 30) {
      return '${(difference.inDays / 30).floor()}mo ago';
    } else if (difference.inDays > 0) {
      return '${difference.inDays}d ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}m ago';
    } else {
      return 'Just now';
    }
  }
}

class _ActivityTile extends StatelessWidget {
  final Map<String, dynamic> activity;
  const _ActivityTile({required this.activity});

  @override
  Widget build(BuildContext context) {
    final code = (activity['action_code'] ?? activity['code'] ?? '') as String;
    final description =
        (activity['description'] as String?) ??
        (activity['action_label'] as String?) ??
        code;
    final userEmail =
        activity['user_email'] as String? ??
        ((activity['user'] as Map<String, dynamic>?)?['email'] as String?);
    final timestampRaw = activity['timestamp'] ?? activity['created_at'];
    DateTime? timestamp;
    if (timestampRaw is String) timestamp = DateTime.tryParse(timestampRaw);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppLayout.borderRadiusMd,
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: AppColors.primary50,
              shape: BoxShape.circle,
            ),
            child: Icon(
              LucideIcons.activity,
              size: 14,
              color: AppColors.primary600,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(description, style: AppTypography.body),
                const SizedBox(height: 4),
                Text(
                  [
                    if (userEmail != null && userEmail.isNotEmpty) userEmail,
                    if (timestamp != null) _format(timestamp),
                  ].join(' · '),
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textTertiary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _format(DateTime t) {
    final now = DateTime.now();
    final diff = now.difference(t);
    if (diff.inDays > 30) return '${(diff.inDays / 30).floor()}mo ago';
    if (diff.inDays > 0) return '${diff.inDays}d ago';
    if (diff.inHours > 0) return '${diff.inHours}h ago';
    if (diff.inMinutes > 0) return '${diff.inMinutes}m ago';
    return 'Just now';
  }
}
