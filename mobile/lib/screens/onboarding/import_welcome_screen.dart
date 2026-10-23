import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../providers/contacts_provider.dart';
import '../../providers/csv_import_provider.dart';
import '../../providers/dashboard_provider.dart';
import '../../providers/leads_provider.dart';
import '../../providers/org_modules_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/forms/csv_import_sheet.dart';

/// The first screen after creating a workspace, and where the dashboard's
/// card sends a workspace that is still empty: whose names are in the sheet,
/// then the import, or a skip to the dashboard. The web's `/welcome`
/// (`frontend/src/routes/(app)/welcome/+page.svelte`), in the same words.
///
/// Who may import is the server's call: a member without import rights who
/// reaches this screen gets the import views' 403, worded as on the web.
class ImportWelcomeScreen extends ConsumerStatefulWidget {
  const ImportWelcomeScreen({super.key, this.pickFile, this.saveFile});

  /// Stand-ins for the platform pickers, for tests only.
  final Future<PlatformFile?> Function()? pickFile;
  final Future<String?> Function(String fileName, List<int> bytes)? saveFile;

  @override
  ConsumerState<ImportWelcomeScreen> createState() =>
      _ImportWelcomeScreenState();
}

class _ImportWelcomeScreenState extends ConsumerState<ImportWelcomeScreen> {
  /// Where the records will land. The sheet's "Import as leads instead"
  /// moves a contacts import here, as the web page's `onUseLeads` does.
  CsvImportTarget _chosen = CsvImportTarget.contacts;

  Future<void> _open(CsvImportTarget target, {required bool leadsOn}) {
    _chosen = target;
    return showCsvImportSheet(
      context,
      target,
      onImported: _imported,
      onUseLeads: leadsOn ? () => _chosen = CsvImportTarget.leads : null,
      pickFile: widget.pickFile,
      saveFile: widget.saveFile,
    );
  }

  /// On to the list the records went into. Both it and the dashboard, whose
  /// card is what offered this, may hold what they fetched before the import.
  void _imported() {
    final router = GoRouter.of(context);
    ref.invalidate(dashboardProvider);
    if (_chosen == CsvImportTarget.leads) {
      ref.invalidate(leadsProvider);
      router.go(AppRoutes.leads);
      return;
    }
    ref.invalidate(contactsProvider);
    // Contacts sits outside the tab bar, so the dashboard goes under it and
    // back lands there rather than closing the app.
    router.go(AppRoutes.dashboard);
    router.push(AppRoutes.contacts);
  }

  @override
  Widget build(BuildContext context) {
    final leadsOn = ref.watch(moduleOnProvider('leads'));
    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(backgroundColor: AppColors.surface, elevation: 0),
      body: SafeArea(
        top: false,
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          child: Center(
            child: ConstrainedBox(
              // A phone uses its whole width; a tablet keeps a readable
              // column, as the web page does at 720px.
              constraints: const BoxConstraints(maxWidth: 560),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('Bring in your contacts', style: AppTypography.h2),
                  const SizedBox(height: 4),
                  Text(
                    'Upload a spreadsheet and we will match its columns for '
                    'you.',
                    style: AppTypography.body.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 20),
                  _Choice(
                    icon: LucideIcons.users,
                    title: 'Customers and people you work with',
                    line: 'Import them as contacts.',
                    onTap: () =>
                        _open(CsvImportTarget.contacts, leadsOn: leadsOn),
                  ),
                  if (leadsOn) ...[
                    const SizedBox(height: 10),
                    _Choice(
                      icon: LucideIcons.target,
                      title: "People you're trying to sell to",
                      line: 'Import them as leads to follow up.',
                      onTap: () => _open(CsvImportTarget.leads, leadsOn: true),
                    ),
                  ],
                  const SizedBox(height: 16),
                  TextButton(
                    style: TextButton.styleFrom(
                      minimumSize: const Size.fromHeight(
                        AppLayout.buttonHeightLarge,
                      ),
                    ),
                    onPressed: () => context.go(AppRoutes.dashboard),
                    child: const Text('Skip for now'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// One answer to "whose names are in the sheet?", a flat card that opens the
/// import for it.
class _Choice extends StatelessWidget {
  const _Choice({
    required this.icon,
    required this.title,
    required this.line,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String line;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      borderRadius: AppLayout.borderRadiusMd,
      child: InkWell(
        borderRadius: AppLayout.borderRadiusMd,
        onTap: onTap,
        child: Container(
          constraints: const BoxConstraints(minHeight: 64),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.border),
            borderRadius: AppLayout.borderRadiusMd,
          ),
          child: Row(
            children: [
              Icon(icon, size: 20, color: AppColors.textSecondary),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: AppTypography.body.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      line,
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(
                LucideIcons.chevronRight,
                size: 18,
                color: AppColors.textTertiary,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
