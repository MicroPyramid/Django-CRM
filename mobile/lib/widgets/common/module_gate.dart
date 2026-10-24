import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/org_modules_provider.dart';
import '../../routes/app_routes.dart';
import '../../routes/module_routes.dart';
import 'buttons.dart';

/// Shows [child] while the module its route needs is on, else a view saying
/// the module is switched off. Follows the module list while open. A hidden
/// screen is UX only; the API refuses the module's requests on its own.
class ModuleGate extends ConsumerWidget {
  final String path;
  final Widget child;

  const ModuleGate({super.key, required this.path, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final need = needFor(path);
    if (need == null) return child;
    final modules = ref.watch(shownModulesProvider);
    final refused = refusedModule(need, modules);
    if (refused == null || modules == null) return child;
    return ModuleOffView(label: modules.labelOf(refused));
  }
}

class ModuleOffView extends ConsumerWidget {
  final String label;

  const ModuleOffView({super.key, required this.label});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isAdmin = ref.watch(isOrgAdminProvider);
    return Scaffold(
      appBar: AppBar(title: Text(label)),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.xl),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  LucideIcons.toggleLeft,
                  size: 48,
                  color: AppColors.gray400,
                ),
                const SizedBox(height: AppSpacing.lg),
                Text(
                  '$label is switched off',
                  textAlign: TextAlign.center,
                  style: AppTypography.h3,
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  '$label is switched off for this organization.',
                  textAlign: TextAlign.center,
                  style: AppTypography.body,
                ),
                const SizedBox(height: AppSpacing.xl),
                PrimaryButton(
                  label: 'Back to Home',
                  onPressed: () => context.go(AppRoutes.dashboard),
                ),
                if (isAdmin) ...[
                  const SizedBox(height: AppSpacing.md),
                  // Not SecondaryButton: its fixed-height Row overflows when the
                  // label wraps at a large text scale.
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        minimumSize: const Size(
                          44,
                          AppLayout.buttonHeightLarge,
                        ),
                        foregroundColor: AppColors.primary600,
                        shape: RoundedRectangleBorder(
                          borderRadius: AppLayout.borderRadiusMd,
                        ),
                      ),
                      onPressed: () => context.push(AppRoutes.settingsApps),
                      child: const Text(
                        'Open Apps settings',
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
