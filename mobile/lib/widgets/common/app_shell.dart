import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../providers/auth_provider.dart';
import '../../routes/app_router.dart';
import 'avatar.dart';

/// Bottom-nav configuration. The "More" entry opens a bottom sheet instead of
/// switching branches; it represents both the Tasks (branch 4) and full
/// More/Settings (branch 5) destinations so the tab highlights when the user
/// is on either of those screens.
class _NavBranch {
  final String label;
  final IconData icon;
  final List<int> branches;
  final bool opensSheet;
  const _NavBranch({
    required this.label,
    required this.icon,
    required this.branches,
    this.opensSheet = false,
  });
}

const _navBranches = <_NavBranch>[
  _NavBranch(label: 'Home', icon: LucideIcons.layoutDashboard, branches: [0]),
  _NavBranch(label: 'Leads', icon: LucideIcons.users, branches: [1]),
  _NavBranch(label: 'Deals', icon: LucideIcons.briefcase, branches: [2]),
  _NavBranch(label: 'Tickets', icon: LucideIcons.ticket, branches: [3]),
  _NavBranch(
    label: 'More',
    icon: LucideIcons.moreHorizontal,
    branches: [5, 4],
    opensSheet: true,
  ),
];

/// App Shell - Main wrapper with bottom navigation
class AppShell extends ConsumerWidget {
  final StatefulNavigationShell navigationShell;

  const AppShell({super.key, required this.navigationShell});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentBranch = navigationShell.currentIndex;
    final selectedNavIndex = _navBranches.indexWhere(
      (b) => b.branches.contains(currentBranch),
    );

    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: _BottomNav(
        currentIndex: selectedNavIndex,
        onTap: (navIndex) {
          final entry = _navBranches[navIndex];
          if (entry.opensSheet) {
            _showMoreSheet(context, ref, navigationShell);
            return;
          }
          final target = entry.branches.first;
          navigationShell.goBranch(
            target,
            initialLocation: target == currentBranch,
          );
        },
      ),
    );
  }
}

void _showMoreSheet(
  BuildContext context,
  WidgetRef ref,
  StatefulNavigationShell navigationShell,
) {
  showModalBottomSheet(
    context: context,
    backgroundColor: AppColors.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (sheetContext) => _MoreSheet(navigationShell: navigationShell),
  );
}

class _MoreSheet extends ConsumerWidget {
  final StatefulNavigationShell navigationShell;
  const _MoreSheet({required this.navigationShell});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final user = authState.user;

    return SafeArea(
      top: false,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 8),
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.gray200,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          if (user != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Row(
                children: [
                  UserAvatar(
                    name: user.displayName,
                    imageUrl: user.profilePic,
                    size: AvatarSize.lg,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user.displayName,
                          style: AppTypography.h3.copyWith(fontSize: 16),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          user.email,
                          style: AppTypography.bodySmall.copyWith(
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
            ),
          const Divider(height: 1),
          _SheetItem(
            icon: LucideIcons.checkSquare,
            label: 'Tasks',
            onTap: () {
              Navigator.pop(context);
              navigationShell.goBranch(4);
            },
          ),
          _SheetItem(
            icon: LucideIcons.settings,
            label: 'Settings',
            onTap: () {
              Navigator.pop(context);
              navigationShell.goBranch(5);
            },
          ),
          _SheetItem(
            icon: LucideIcons.logOut,
            label: 'Sign out',
            destructive: true,
            onTap: () => _confirmSignOut(context, ref),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  void _confirmSignOut(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Sign out'),
        content: const Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(dialogContext); // close confirm
              Navigator.pop(context); // close sheet
              await ref.read(authProvider.notifier).signOut();
              if (context.mounted) context.go(AppRoutes.login);
            },
            child: Text(
              'Sign out',
              style: TextStyle(color: AppColors.danger600),
            ),
          ),
        ],
      ),
    );
  }
}

class _SheetItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool destructive;

  const _SheetItem({
    required this.icon,
    required this.label,
    required this.onTap,
    this.destructive = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = destructive ? AppColors.danger600 : AppColors.textPrimary;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        child: Row(
          children: [
            Icon(icon, size: 20, color: color),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                label,
                style: AppTypography.body.copyWith(
                  color: color,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            if (!destructive)
              Icon(
                LucideIcons.chevronRight,
                size: 18,
                color: AppColors.textTertiary,
              ),
          ],
        ),
      ),
    );
  }
}

/// Bottom Navigation Bar
class _BottomNav extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;

  const _BottomNav({required this.currentIndex, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: AppLayout.bottomNavHeight,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              for (var i = 0; i < _navBranches.length; i++)
                _NavItem(
                  icon: _navBranches[i].icon,
                  label: _navBranches[i].label,
                  isSelected: currentIndex == i,
                  onTap: () => onTap(i),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Individual navigation item
class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AnimatedContainer(
                duration: AppDurations.fast,
                curve: AppCurves.defaultCurve,
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 2,
                ),
                decoration: BoxDecoration(
                  color: isSelected ? AppColors.primary100 : Colors.transparent,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(
                  icon,
                  size: 20,
                  color: isSelected ? AppColors.primary600 : AppColors.gray400,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                label,
                style: AppTypography.labelSmall.copyWith(
                  color: isSelected ? AppColors.primary600 : AppColors.gray500,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
