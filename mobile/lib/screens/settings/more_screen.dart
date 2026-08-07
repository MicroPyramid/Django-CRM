import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../config/api_config.dart';
import '../../core/theme/theme.dart';
import '../../providers/auth_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/common/common.dart';

/// More/Settings Screen
/// User profile, app settings, and support options
class MoreScreen extends ConsumerStatefulWidget {
  const MoreScreen({super.key});

  @override
  ConsumerState<MoreScreen> createState() => _MoreScreenState();
}

class _MoreScreenState extends ConsumerState<MoreScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('More'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Profile Section
            _buildProfileSection(),

            // Workspace Section. Destinations that aren't on the bottom nav.
            _buildSectionHeader('Workspace'),
            _MenuItem(
              icon: LucideIcons.checkSquare,
              label: 'Tasks',
              description: 'Your to-dos across leads, deals and tickets',
              onTap: () => context.go(AppRoutes.tasks),
            ),
            _MenuItem(
              icon: LucideIcons.building2,
              label: 'Accounts',
              description: 'The companies you sell to',
              onTap: () => context.push(AppRoutes.accounts),
            ),
            _MenuItem(
              icon: LucideIcons.users,
              label: 'Contacts',
              description: 'The people at those companies',
              onTap: () => context.push(AppRoutes.contacts),
            ),
            _MenuItem(
              icon: LucideIcons.clock,
              label: 'Timesheet',
              description: 'The hours you logged this week',
              onTap: () => context.push(AppRoutes.timesheet),
            ),
            _MenuItem(
              icon: LucideIcons.bell,
              label: 'Notifications',
              description: 'Mentions and comments on your tickets',
              onTap: () => context.push(AppRoutes.notifications),
            ),
            _MenuItem(
              icon: LucideIcons.receipt,
              label: 'Invoices',
              description: 'What is owed, and what has been paid',
              onTap: () => context.push(AppRoutes.invoices),
            ),

            // Account Section
            _buildSectionHeader('Account'),
            _MenuItem(
              icon: LucideIcons.user,
              label: 'Profile Settings',
              onTap: () => context.push(AppRoutes.profile),
            ),
            // Only worth showing to someone who has somewhere to switch to.
            // The picker and `switchOrganization` both already existed and
            // worked; nothing in the app reached them once an org was chosen,
            // so the only way to change org was to sign out.
            if ((ref.watch(authProvider).organizations?.length ?? 0) > 1)
              _MenuItem(
                icon: LucideIcons.building2,
                label: 'Switch Organization',
                description: ref.watch(selectedOrgProvider)?.name,
                onTap: () => context.push(AppRoutes.orgSelection),
              ),

            // Team Section
            _buildSectionHeader('Team'),
            _MenuItem(
              icon: LucideIcons.users,
              label: 'Team',
              description: 'Who is in this org, and what they can do',
              onTap: () => context.push(AppRoutes.team),
            ),

            // Preferences used to be a section here, holding a Dark Mode
            // switch that repainted nothing and then announced "Dark mode
            // enabled", and a Language picker offering three languages the app
            // has never had a single string in. Both are gone rather than
            // relabelled: honouring the theme is a repaint of 1,472 hardcoded
            // colour references, and there is no localisation to select.

            // Support Section
            _buildSectionHeader('Support'),
            _MenuItem(
              icon: LucideIcons.helpCircle,
              label: 'Help Center',
              onTap: () => _openOnTheWeb('/docs', 'Help Center'),
            ),
            _MenuItem(
              icon: LucideIcons.fileText,
              label: 'Terms of Service',
              onTap: () =>
                  _openOnTheWeb('/terms-of-service', 'Terms of Service'),
            ),
            _MenuItem(
              icon: LucideIcons.shield,
              label: 'Privacy Policy',
              onTap: () => _openOnTheWeb('/privacy-policy', 'Privacy Policy'),
            ),

            // Sign Out Button
            const SizedBox(height: 24),
            _buildSignOutButton(),

            // Version Info
            const SizedBox(height: 24),
            Center(
              child: Text(
                'Version 1.0.0',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textTertiary,
                ),
              ),
            ),

            const SizedBox(height: 100),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileSection() {
    final authState = ref.watch(authProvider);
    final user = authState.user;
    final org = authState.selectedOrganization;
    final displayName = user?.displayName ?? 'Signed-in user';
    final email = user?.email ?? '';
    final role = org?.role ?? org?.name;

    return GestureDetector(
      onTap: () => context.push(AppRoutes.profile),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
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
        child: Row(
          children: [
            UserAvatar(
              name: displayName,
              imageUrl: user?.profilePic,
              size: AvatarSize.xl,
            ),

            const SizedBox(width: 16),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    displayName,
                    style: AppTypography.h2.copyWith(
                      color: AppColors.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (role != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      role,
                      style: AppTypography.body.copyWith(
                        color: AppColors.textSecondary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                  if (email.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      email,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ],
              ),
            ),

            Icon(
              LucideIcons.chevronRight,
              size: 22,
              color: AppColors.textSecondary,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
      child: Text(
        title.toUpperCase(),
        style: AppTypography.overline.copyWith(
          color: AppColors.textSecondary,
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  Widget _buildSignOutButton() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: OutlinedButton(
        onPressed: () => _handleSignOut(),
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: AppColors.danger200),
          minimumSize: const Size(double.infinity, 52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(LucideIcons.logOut, size: 20, color: AppColors.danger600),
            const SizedBox(width: 10),
            Text(
              'Sign Out',
              style: AppTypography.button.copyWith(color: AppColors.danger600),
            ),
          ],
        ),
      ),
    );
  }

  /// Open a page on the marketing site, which is where these documents live.
  /// They were "coming soon" dialogs while the real pages were already
  /// published.
  Future<void> _openOnTheWeb(String path, String label) async {
    final uri = Uri.parse('${ApiConfig.marketingSite}$path');
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not open $label'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  void _handleSignOut() {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Sign Out'),
        content: const Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(dialogContext);

              // Sign out using auth provider
              await ref.read(authProvider.notifier).signOut();

              if (mounted) {
                context.go(AppRoutes.login);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Signed out successfully'),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              }
            },
            child: Text(
              'Sign Out',
              style: TextStyle(color: AppColors.danger600),
            ),
          ),
        ],
      ),
    );
  }
}

/// Menu Item Widget
class _MenuItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? description;
  final VoidCallback onTap;

  const _MenuItem({
    required this.icon,
    required this.label,
    this.description,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: AppColors.surface,
          border: Border(bottom: BorderSide(color: AppColors.gray100)),
        ),
        child: Row(
          children: [
            // Icon
            Icon(icon, size: 22, color: AppColors.textSecondary),

            const SizedBox(width: 14),

            // Label + Description
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: AppTypography.body.copyWith(
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  if (description != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      description!,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ],
              ),
            ),

            // Chevron
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
}
