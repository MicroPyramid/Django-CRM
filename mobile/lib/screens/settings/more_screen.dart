import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../data/mock/mock_data.dart';
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
  bool _darkMode = false;

  User get _currentUser => MockData.currentUser;

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

            // Account Section
            _buildSectionHeader('Account'),
            _MenuItem(
              icon: LucideIcons.user,
              label: 'Profile Settings',
              onTap: () => _showComingSoon('Profile Settings'),
            ),

            // Team Section
            _buildSectionHeader('Team'),
            _MenuItem(
              icon: LucideIcons.users,
              label: 'Team Management',
              description: 'Manage team members and roles',
              onTap: () => _showComingSoon('Team Management'),
            ),

            // Preferences Section
            _buildSectionHeader('Preferences'),
            _ToggleMenuItem(
              icon: LucideIcons.moon,
              label: 'Dark Mode',
              value: _darkMode,
              onChanged: (value) {
                setState(() => _darkMode = value);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      value ? 'Dark mode enabled' : 'Dark mode disabled',
                    ),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
            ),
            _MenuItem(
              icon: LucideIcons.globe,
              label: 'Language',
              value: 'English',
              onTap: () => _showLanguagePicker(),
            ),

            // Support Section
            _buildSectionHeader('Support'),
            _MenuItem(
              icon: LucideIcons.helpCircle,
              label: 'Help Center',
              onTap: () => _showComingSoon('Help Center'),
            ),
            _MenuItem(
              icon: LucideIcons.fileText,
              label: 'Terms of Service',
              onTap: () => _showComingSoon('Terms of Service'),
            ),
            _MenuItem(
              icon: LucideIcons.shield,
              label: 'Privacy Policy',
              onTap: () => _showComingSoon('Privacy Policy'),
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
    return GestureDetector(
      onTap: () => _showComingSoon('Profile'),
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
            // Avatar
            UserAvatar(
              name: _currentUser.name,
              imageUrl: _currentUser.avatar,
              size: AvatarSize.xl,
            ),

            const SizedBox(width: 16),

            // User Info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _currentUser.name,
                    style: AppTypography.h2.copyWith(
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _currentUser.role,
                    style: AppTypography.body.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _currentUser.email,
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),

            // Chevron
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
            Icon(
              LucideIcons.logOut,
              size: 20,
              color: AppColors.danger600,
            ),
            const SizedBox(width: 10),
            Text(
              'Sign Out',
              style: AppTypography.button.copyWith(
                color: AppColors.danger600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showComingSoon(String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$feature coming soon'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showLanguagePicker() {
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
              child: Text('Select Language', style: AppTypography.h3),
            ),
            _LanguageOption(
              label: 'English',
              isSelected: true,
              onTap: () => Navigator.pop(context),
            ),
            _LanguageOption(
              label: 'Spanish',
              isSelected: false,
              onTap: () {
                Navigator.pop(context);
                _showComingSoon('Spanish language');
              },
            ),
            _LanguageOption(
              label: 'French',
              isSelected: false,
              onTap: () {
                Navigator.pop(context);
                _showComingSoon('French language');
              },
            ),
            _LanguageOption(
              label: 'German',
              isSelected: false,
              onTap: () {
                Navigator.pop(context);
                _showComingSoon('German language');
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
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
  final String? value;
  final VoidCallback onTap;

  const _MenuItem({
    required this.icon,
    required this.label,
    this.description,
    this.value,
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
          border: Border(
            bottom: BorderSide(color: AppColors.gray100),
          ),
        ),
        child: Row(
          children: [
            // Icon
            Icon(
              icon,
              size: 22,
              color: AppColors.textSecondary,
            ),

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

            // Value
            if (value != null) ...[
              Text(
                value!,
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(width: 8),
            ],

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

/// Toggle Menu Item Widget
class _ToggleMenuItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _ToggleMenuItem({
    required this.icon,
    required this.label,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(
          bottom: BorderSide(color: AppColors.gray100),
        ),
      ),
      child: Row(
        children: [
          // Icon
          Icon(
            icon,
            size: 22,
            color: AppColors.textSecondary,
          ),

          const SizedBox(width: 14),

          // Label
          Expanded(
            child: Text(
              label,
              style: AppTypography.body.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
          ),

          // Toggle
          Switch(
            value: value,
            onChanged: onChanged,
            activeTrackColor: AppColors.primary200,
            activeThumbColor: AppColors.primary600,
          ),
        ],
      ),
    );
  }
}

/// Language Option Widget
class _LanguageOption extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _LanguageOption({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Expanded(
              child: Text(
                label,
                style: AppTypography.body.copyWith(
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  color:
                      isSelected ? AppColors.primary600 : AppColors.textPrimary,
                ),
              ),
            ),
            if (isSelected)
              Icon(
                LucideIcons.check,
                size: 20,
                color: AppColors.primary600,
              ),
          ],
        ),
      ),
    );
  }
}

