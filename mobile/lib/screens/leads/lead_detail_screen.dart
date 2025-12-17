import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../data/mock/mock_data.dart';
import '../../widgets/common/common.dart';
import '../../widgets/misc/timeline_item.dart';

/// Lead Detail Screen
/// Shows lead info with tabs: Overview, Timeline, Notes
class LeadDetailScreen extends StatefulWidget {
  final String leadId;

  const LeadDetailScreen({
    super.key,
    required this.leadId,
  });

  @override
  State<LeadDetailScreen> createState() => _LeadDetailScreenState();
}

class _LeadDetailScreenState extends State<LeadDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _noteController = TextEditingController();

  Lead? get lead => MockData.getLeadById(widget.leadId);
  User? get assignedUser => null; // Will be loaded from API in future

  List<Activity> get leadActivities => MockData.activities
      .where((a) =>
          a.relatedTo?.type == RelatedEntityType.lead && a.relatedTo?.id == widget.leadId)
      .toList()
    ..sort((a, b) => b.timestamp.compareTo(a.timestamp));

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (lead == null) {
      return Scaffold(
        appBar: AppBar(
          leading: IconButton(
            icon: const Icon(LucideIcons.chevronLeft),
            onPressed: () => context.pop(),
          ),
        ),
        body: const EmptyState(
          icon: LucideIcons.userX,
          title: 'Lead not found',
          description: 'This lead may have been deleted',
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.surface,
      body: NestedScrollView(
        headerSliverBuilder: (context, innerBoxIsScrolled) => [
          // App Bar + Header
          SliverAppBar(
            expandedHeight: 280,
            pinned: true,
            backgroundColor: AppColors.primary50,
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
                onPressed: () {
                  // Navigate to edit screen
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Edit coming soon'),
                      behavior: SnackBarBehavior.floating,
                    ),
                  );
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
            bottom: PreferredSize(
              preferredSize: const Size.fromHeight(48),
              child: Container(
                color: AppColors.surface,
                child: TabBar(
                  controller: _tabController,
                  labelColor: AppColors.primary600,
                  unselectedLabelColor: AppColors.textSecondary,
                  indicatorColor: AppColors.primary600,
                  indicatorWeight: 2,
                  labelStyle: AppTypography.label,
                  tabs: const [
                    Tab(text: 'Overview'),
                    Tab(text: 'Timeline'),
                    Tab(text: 'Notes'),
                  ],
                ),
              ),
            ),
          ),
        ],
        body: TabBarView(
          controller: _tabController,
          children: [
            _buildOverviewTab(),
            _buildTimelineTab(),
            _buildNotesTab(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.primary50,
            AppColors.primary100.withValues(alpha: 0.5),
          ],
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 60, 24, 16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Avatar
              UserAvatar(
                name: lead!.name,
                size: AvatarSize.xl,
              ),

              const SizedBox(height: 16),

              // Name
              Text(
                lead!.name,
                style: AppTypography.h1.copyWith(
                  color: AppColors.textPrimary,
                ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 4),

              // Company
              Text(
                lead!.company,
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),

              const SizedBox(height: 12),

              // Status & Priority Badges
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  StatusBadge.fromLeadStatus(lead!.status),
                  if (lead!.priority == Priority.high) ...[
                    const SizedBox(width: 8),
                    PriorityBadge(priority: lead!.priority),
                  ],
                ],
              ),

              const SizedBox(height: 16),

              // Quick Actions
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _QuickActionButton(
                    icon: LucideIcons.phone,
                    label: 'Call',
                    onTap: () => _launchPhone(lead!.phone),
                  ),
                  const SizedBox(width: 24),
                  _QuickActionButton(
                    icon: LucideIcons.mail,
                    label: 'Email',
                    onTap: () => _launchEmail(lead!.email),
                  ),
                  const SizedBox(width: 24),
                  _QuickActionButton(
                    icon: LucideIcons.messageSquare,
                    label: 'Message',
                    onTap: () => _launchSms(lead!.phone),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOverviewTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Contact Information Card
          _buildCard(
            title: 'Contact Information',
            child: Column(
              children: [
                _InfoRow(
                  icon: LucideIcons.mail,
                  label: 'EMAIL',
                  value: lead!.email,
                  onTap: () => _launchEmail(lead!.email),
                ),
                const Divider(height: 24),
                _InfoRow(
                  icon: LucideIcons.phone,
                  label: 'PHONE',
                  value: lead!.phone ?? 'Not provided',
                  onTap: lead!.phone != null
                      ? () => _launchPhone(lead!.phone!)
                      : null,
                ),
                const Divider(height: 24),
                _InfoRow(
                  icon: LucideIcons.globe,
                  label: 'SOURCE',
                  value: lead!.source.displayName,
                ),
                const Divider(height: 24),
                _InfoRow(
                  icon: LucideIcons.calendar,
                  label: 'CREATED',
                  value: _formatDate(lead!.createdAt),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Assigned To Card
          _buildCard(
            title: 'Assigned To',
            child: Row(
              children: [
                UserAvatar(
                  name: assignedUser?.name ?? 'Unknown',
                  imageUrl: assignedUser?.avatar,
                  size: AvatarSize.md,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        assignedUser?.name ?? 'Unknown',
                        style: AppTypography.label,
                      ),
                      Text(
                        assignedUser?.role ?? '',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Tags Card
          if (lead!.tags.isNotEmpty)
            _buildCard(
              title: 'Tags',
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: lead!.tags
                    .map((tag) => LabelPill(label: tag))
                    .toList(),
              ),
            ),

          const SizedBox(height: 16),

          // Description Preview Card
          if (lead!.description != null && lead!.description!.isNotEmpty)
            _buildCard(
              title: 'Description',
              action: GestureDetector(
                onTap: () => _tabController.animateTo(2),
                child: Text(
                  'See all',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.primary600,
                  ),
                ),
              ),
              child: Text(
                lead!.description!.length > 200
                    ? '${lead!.description!.substring(0, 200)}...'
                    : lead!.description!,
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
              ),
            ),

          const SizedBox(height: 100),
        ],
      ),
    );
  }

  Widget _buildTimelineTab() {
    if (leadActivities.isEmpty) {
      return const TimelineEmpty();
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: leadActivities.length,
      itemBuilder: (context, index) {
        return TimelineItem(
          activity: leadActivities[index],
          isFirst: index == 0,
          isLast: index == leadActivities.length - 1,
        );
      },
    );
  }

  Widget _buildNotesTab() {
    // Mock notes for this lead
    final notes = [
      {
        'text': lead!.description ?? 'Initial contact made via website form.',
        'author': lead!.assignedToName,
        'timestamp': lead!.createdAt,
      },
    ];

    return Column(
      children: [
        Expanded(
          child: notes.isEmpty
              ? const EmptyState(
                  icon: LucideIcons.fileText,
                  title: 'No notes yet',
                  description: 'Add a note to keep track of important details',
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: notes.length,
                  itemBuilder: (context, index) {
                    final note = notes[index];
                    return _NoteCard(
                      text: note['text'] as String,
                      author: note['author'] as String,
                      timestamp: note['timestamp'] as DateTime,
                    );
                  },
                ),
        ),

        // Add Note Input
        Container(
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
                Expanded(
                  child: TextField(
                    controller: _noteController,
                    decoration: InputDecoration(
                      hintText: 'Add a note...',
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
                    color: AppColors.primary600,
                    shape: BoxShape.circle,
                  ),
                  child: IconButton(
                    icon: const Icon(
                      LucideIcons.send,
                      color: Colors.white,
                      size: 20,
                    ),
                    onPressed: () {
                      if (_noteController.text.isNotEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Note added'),
                            behavior: SnackBarBehavior.floating,
                          ),
                        );
                        _noteController.clear();
                      }
                    },
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCard({
    required String title,
    required Widget child,
    Widget? action,
  }) {
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
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: AppTypography.overline.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              if (action != null) action,
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
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
              leading: const Icon(LucideIcons.userPlus),
              title: const Text('Change Status'),
              onTap: () {
                Navigator.pop(context);
                _showStatusChange();
              },
            ),
            ListTile(
              leading: const Icon(LucideIcons.copy),
              title: const Text('Duplicate Lead'),
              onTap: () {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Lead duplicated'),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
            ),
            ListTile(
              leading: Icon(LucideIcons.trash2, color: AppColors.danger600),
              title: Text(
                'Delete Lead',
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

  void _showStatusChange() {
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
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text('Change Status', style: AppTypography.h3),
            ),
            ...LeadStatus.values.map((status) => ListTile(
                  leading: Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: _getStatusColor(status),
                      shape: BoxShape.circle,
                    ),
                  ),
                  title: Text(status.displayName),
                  trailing: lead!.status == status
                      ? Icon(LucideIcons.check, color: AppColors.primary600)
                      : null,
                  onTap: () {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Status changed to ${status.displayName}'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                )),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  void _confirmDelete() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Lead?'),
        content: const Text(
          'This action cannot be undone. Are you sure you want to delete this lead?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              context.pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Lead deleted'),
                  behavior: SnackBarBehavior.floating,
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

  Color _getStatusColor(LeadStatus status) {
    // Use the color defined in the enum
    return status.color;
  }

  String _formatDate(DateTime date) {
    final months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }

  Future<void> _launchPhone(String? phone) async {
    if (phone == null) return;
    final uri = Uri.parse('tel:$phone');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  Future<void> _launchEmail(String email) async {
    final uri = Uri.parse('mailto:$email');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  Future<void> _launchSms(String? phone) async {
    if (phone == null) return;
    final uri = Uri.parse('sms:$phone');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }
}

/// Quick action button for header
class _QuickActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _QuickActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppColors.primary100,
              shape: BoxShape.circle,
            ),
            child: Icon(
              icon,
              color: AppColors.primary600,
              size: 22,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            label,
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

/// Info row widget
class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final VoidCallback? onTap;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Row(
        children: [
          Icon(
            icon,
            size: 20,
            color: AppColors.gray400,
          ),
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
                Text(
                  value,
                  style: AppTypography.body.copyWith(
                    color: onTap != null
                        ? AppColors.primary600
                        : AppColors.textPrimary,
                  ),
                ),
              ],
            ),
          ),
          if (onTap != null)
            Icon(
              LucideIcons.externalLink,
              size: 16,
              color: AppColors.primary600,
            ),
        ],
      ),
    );
  }
}

/// Note card widget
class _NoteCard extends StatelessWidget {
  final String text;
  final String author;
  final DateTime timestamp;

  const _NoteCard({
    required this.text,
    required this.author,
    required this.timestamp,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.gray50,
        borderRadius: AppLayout.borderRadiusLg,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            text,
            style: AppTypography.body.copyWith(
              color: AppColors.textPrimary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              UserAvatar(
                name: author,
                size: AvatarSize.xs,
              ),
              const SizedBox(width: 8),
              Text(
                author,
                style: AppTypography.caption.copyWith(
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                _formatTimeAgo(timestamp),
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
