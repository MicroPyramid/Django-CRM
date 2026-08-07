import 'package:flutter/material.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../common/common.dart';

/// Callback fired when a tag pill is tapped, used to set a tag filter.
typedef LeadTagTap = void Function(String tagId, String tagLabel);

/// Lead Card Widget
/// Displays lead summary in list view with avatar, status, priority, tags,
/// assignee, opportunity value, and tap-to-call/email actions.
class LeadCard extends StatelessWidget {
  final Lead lead;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;
  final LeadTagTap? onTagTap;

  const LeadCard({
    super.key,
    required this.lead,
    this.onTap,
    this.onLongPress,
    this.onTagTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppLayout.borderRadiusMd,
        border: Border.all(color: AppColors.border),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: AppLayout.borderRadiusMd,
        child: InkWell(
          onTap: onTap,
          onLongPress: onLongPress,
          borderRadius: AppLayout.borderRadiusMd,
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHeader(),
                if (lead.tags.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  _buildTags(),
                ],
                const SizedBox(height: 8),
                _buildFooter(context),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        UserAvatar(name: lead.name, size: AvatarSize.sm),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                lead.name,
                style: AppTypography.label.copyWith(
                  fontWeight: FontWeight.w600,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              Text(
                lead.company,
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (lead.priority == Priority.high)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.danger100,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      LucideIcons.flame,
                      size: 11,
                      color: AppColors.danger600,
                    ),
                    const SizedBox(width: 2),
                    Text(
                      'Hot',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.danger600,
                        fontWeight: FontWeight.w600,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 2),
            Text(
              _formatTimeAgo(lead.createdAt),
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildTags() {
    final displayCount = lead.tags.length > 2 ? 2 : lead.tags.length;
    final remainingCount = lead.tags.length - displayCount;

    return Wrap(
      spacing: 4,
      runSpacing: 4,
      children: [
        for (var i = 0; i < displayCount; i++)
          _TappableTag(
            label: lead.tags[i],
            // Tags and tagIds may not match length if backend returned mixed
            // shapes; fall back to the name if id is missing.
            onTap: onTagTap == null
                ? null
                : () {
                    final id = (i < lead.tagIds.length)
                        ? lead.tagIds[i]
                        : lead.tags[i];
                    onTagTap!(id, lead.tags[i]);
                  },
          ),
        if (remainingCount > 0)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Text(
              '+$remainingCount',
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildFooter(BuildContext context) {
    final hasValue =
        lead.opportunityAmount != null && lead.opportunityAmount! > 0;
    final hasAssignee = lead.assignedTo != null && lead.assignedTo!.isNotEmpty;
    final hasPhone = lead.phone != null && lead.phone!.trim().isNotEmpty;
    final hasEmail = lead.email.trim().isNotEmpty;

    return Row(
      children: [
        StatusBadge.fromLeadStatus(lead.status),
        const SizedBox(width: 6),
        if (hasValue)
          _ValuePill(amount: lead.opportunityAmount!, currency: lead.currency),
        const Spacer(),
        if (hasAssignee) ...[
          Tooltip(
            message: 'Assigned to ${lead.assignedToName}',
            child: UserAvatar(
              name: lead.assignedToName,
              imageUrl: lead.assignedToProfilePic,
              size: AvatarSize.xs,
            ),
          ),
          const SizedBox(width: 6),
        ],
        if (hasPhone)
          _CardActionIcon(
            icon: LucideIcons.phone,
            tooltip: 'Call ${lead.phone}',
            onTap: () =>
                _launch(context, Uri(scheme: 'tel', path: lead.phone!)),
          ),
        if (hasPhone && hasEmail) const SizedBox(width: 2),
        if (hasEmail)
          _CardActionIcon(
            icon: LucideIcons.mail,
            tooltip: 'Email ${lead.email}',
            onTap: () =>
                _launch(context, Uri(scheme: 'mailto', path: lead.email)),
          ),
        if (!hasPhone && !hasEmail) ...[
          // Fall back to the source pill when no actions are available.
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: AppColors.gray100,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  lead.source.icon,
                  size: 11,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(width: 3),
                Text(
                  lead.source.displayName,
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Future<void> _launch(BuildContext context, Uri uri) async {
    final ok = await launchUrl(uri);
    if (!ok && context.mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Could not open ${uri.scheme}')));
    }
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

class _TappableTag extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;

  const _TappableTag({required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    final pill = LabelPill(label: label);
    if (onTap == null) return pill;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(4),
      child: pill,
    );
  }
}

class _ValuePill extends StatelessWidget {
  final double amount;
  final String? currency;

  const _ValuePill({required this.amount, this.currency});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.success50,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(LucideIcons.dollarSign, size: 11, color: AppColors.success700),
          const SizedBox(width: 2),
          Text(
            _format(amount),
            style: AppTypography.caption.copyWith(
              color: AppColors.success700,
              fontWeight: FontWeight.w600,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }

  String _format(double v) {
    if (v >= 1000000) return '${(v / 1000000).toStringAsFixed(1)}M';
    if (v >= 1000) return '${(v / 1000).toStringAsFixed(v >= 10000 ? 0 : 1)}K';
    return v.toStringAsFixed(0);
  }
}

class _CardActionIcon extends StatelessWidget {
  final IconData icon;
  final String tooltip;
  final VoidCallback onTap;

  const _CardActionIcon({
    required this.icon,
    required this.tooltip,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: InkResponse(
        onTap: onTap,
        radius: 18,
        child: Padding(
          padding: const EdgeInsets.all(6),
          child: Icon(icon, size: 16, color: AppColors.primary600),
        ),
      ),
    );
  }
}

/// Compact lead card variant for horizontal scrolling lists
class LeadCardCompact extends StatelessWidget {
  final Lead lead;
  final VoidCallback? onTap;

  const LeadCardCompact({super.key, required this.lead, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 200,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: AppLayout.borderRadiusMd,
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                UserAvatar(name: lead.name, size: AvatarSize.sm),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        lead.name,
                        style: AppTypography.label,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      Text(
                        lead.company,
                        style: AppTypography.caption.copyWith(
                          color: AppColors.textSecondary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            StatusBadge.fromLeadStatus(lead.status),
          ],
        ),
      ),
    );
  }
}
