import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/org_settings.dart';
import '../../providers/auth_provider.dart';
import '../../providers/org_modules_provider.dart';
import '../../providers/settings_provider.dart';
import '../../routes/app_router.dart';
import '../../services/org_date.dart';

/// The organization itself, read view.
///
/// Most of this is the company profile, and the thing worth saying about it is
/// where it ends up: these fields are printed on every invoice and estimate a
/// customer receives, so a wrong tax ID is a wrong document rather than a wrong
/// preference.
///
/// **The org API key is not here, in any form.** It authenticates as the org's
/// first admin, so the API never serializes it onto this payload. Rotating it
/// belongs behind its own audited action.
///
/// The read is open to any member: the company profile is not a secret, and
/// members legitimately see their org's address and currency. Editing is
/// admin-only, enforced server-side; hiding the button is UX. Industry apps
/// and sample data live on the Apps screen.
class OrganizationScreen extends ConsumerWidget {
  const OrganizationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isAdmin = ref.watch(isOrgAdminProvider);
    final async = ref.watch(orgSettingsProvider);
    final invoicesOn = ref.watch(moduleOnProvider('invoices'));
    final ticketsOn = ref.watch(moduleOnProvider('tickets'));

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Organization'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          if (isAdmin && async.value != null)
            IconButton(
              icon: const Icon(LucideIcons.pencil),
              tooltip: 'Edit details',
              onPressed: () => context.push(AppRoutes.settingsOrganizationEdit),
            ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => _ErrorState(
          onRetry: () => ref.read(orgSettingsProvider.notifier).refresh(),
        ),
        data: (org) => RefreshIndicator(
          onRefresh: () => ref.read(orgSettingsProvider.notifier).refresh(),
          child: ListView(
            padding: const EdgeInsets.only(bottom: 40),
            children: [
              _Header(org: org),
              const _SectionHeader('What customers see'),
              _Field(label: 'Legal name', value: org.companyName),
              _Field(label: 'Trading as', value: org.name),
              _Field(label: 'Address', value: org.addressSummary),
              _Field(label: 'Tax ID', value: org.taxId),
              _Field(label: 'Email', value: org.email),
              _Field(label: 'Phone', value: org.phone),
              _Field(label: 'Website', value: org.website),
              if (invoicesOn) const _PrintedNote(),
              const _SectionHeader('Defaults'),
              _Field(
                label: 'Currency',
                value: '${org.defaultCurrency} ${org.currencySymbol}',
                detail: invoicesOn
                    ? 'Applied to new invoices and estimates. Existing ones '
                          'keep theirs.'
                    : 'The default for new records that carry an amount. '
                          'Existing ones keep theirs.',
              ),
              _Field(
                label: 'Country',
                value: org.defaultCountry,
                detail: 'Default for new addresses.',
              ),
              _Field(
                label: 'Time zone',
                value: org.timezoneLabel,
                detail:
                    'When a day starts here, so "due today" and "overdue" '
                    'mean what your team expects.',
              ),
              if (invoicesOn) ...[
                const _SectionHeader('Invoice numbers'),
                _Field(
                  label: 'New invoices',
                  value: exampleNumber(
                    prefix: org.invoiceNumberPrefix,
                    datePart: org.numberDatePart,
                    padding: org.numberPadding,
                    start: org.invoiceNumberStart,
                    today: orgToday(),
                  ),
                  detail:
                      '${_datePartLabel(org.numberDatePart)}. Numbers already '
                      'issued keep theirs.',
                ),
                _Field(
                  label: 'New estimates',
                  value: exampleNumber(
                    prefix: org.estimateNumberPrefix,
                    datePart: org.numberDatePart,
                    padding: org.numberPadding,
                    today: orgToday(),
                  ),
                  detail: 'Same format, own prefix.',
                ),
              ],
              if (ticketsOn) ...[
                const _SectionHeader('Behaviour'),
                _Field(
                  label: 'Satisfaction surveys',
                  value: org.csatEnabled ? 'Sending' : 'Off',
                  detail: csatExplanation(org.csatEnabled),
                ),
                _Field(
                  label: 'Close child tickets with the parent',
                  value: org.autoCloseChildren
                      ? 'Starts ticked'
                      : 'Starts unticked',
                  detail:
                      '${cascadeDefaultExplanation(org.autoCloseChildren)} '
                      '$cascadeWebGapNote',
                ),
              ],
              const _ApiKeyNote(),
            ],
          ),
        ),
      ),
    );
  }
}

/// "Year, count restarts each year" for a stored date part.
String _datePartLabel(String datePart) => numberDatePartOptions
    .firstWhere(
      (option) => option.value == datePart,
      orElse: () => (value: datePart, label: datePart),
    )
    .label;

class _Header extends StatelessWidget {
  const _Header({required this.org});

  final OrgSettings org;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            org.name.isEmpty ? 'Unnamed organization' : org.name,
            style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 3),
          Text(
            '${org.memberCount} member${org.memberCount == 1 ? '' : 's'}',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({required this.label, required this.value, this.detail});

  final String label;
  final String value;
  final String? detail;

  @override
  Widget build(BuildContext context) {
    final shown = value.trim();
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            shown.isEmpty ? 'Not recorded' : shown,
            style: AppTypography.body.copyWith(
              fontWeight: FontWeight.w500,
              color: shown.isEmpty
                  ? AppColors.textTertiary
                  : AppColors.textPrimary,
            ),
          ),
          if (detail != null) ...[
            const SizedBox(height: 4),
            Text(
              detail!,
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _PrintedNote extends StatelessWidget {
  const _PrintedNote();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 0),
      child: Text(
        'These fields are printed on every invoice and estimate. Changing one '
        'changes documents from that moment on; PDFs already sent keep what '
        'they were sent with.',
        style: AppTypography.caption.copyWith(color: AppColors.textTertiary),
      ),
    );
  }
}

class _ApiKeyNote extends StatelessWidget {
  const _ApiKeyNote();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            LucideIcons.shieldAlert,
            size: 16,
            color: AppColors.textTertiary,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'The organization API key is not here. It authenticates as the '
              'whole organization, so it is never shown on a page you can '
              'reach by browsing. For per-person programmatic access, use API '
              'tokens, which can be revoked one at a time.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 22, 16, 8),
      child: Text(
        title.toUpperCase(),
        style: AppTypography.overline.copyWith(
          color: AppColors.textSecondary,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              LucideIcons.triangleAlert,
              size: 40,
              color: AppColors.textTertiary,
            ),
            const SizedBox(height: 16),
            Text(
              'Could not load the organization',
              style: AppTypography.body,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            OutlinedButton(onPressed: onRetry, child: const Text('Try again')),
          ],
        ),
      ),
    );
  }
}
