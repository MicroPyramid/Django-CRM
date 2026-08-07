import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/org_settings.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import '../../routes/app_router.dart';

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
/// members legitimately see their org's address and currency. Editing, applying
/// a pack and clearing sample data are admin-only, enforced server-side; hiding
/// the buttons is UX.
class OrganizationScreen extends ConsumerWidget {
  const OrganizationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isAdmin = ref.watch(isOrgAdminProvider);
    final async = ref.watch(orgSettingsProvider);

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
          onRefresh: () async {
            ref.invalidate(orgPacksProvider);
            await ref.read(orgSettingsProvider.notifier).refresh();
          },
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
              const _PrintedNote(),
              const _SectionHeader('Defaults'),
              _Field(
                label: 'Currency',
                value: '${org.defaultCurrency} ${org.currencySymbol}',
                detail:
                    'Applied to new invoices and estimates. Existing ones '
                    'keep theirs.',
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
              const _ApiKeyNote(),
              const _SectionHeader('Vertical pack'),
              _PackSection(org: org, isAdmin: isAdmin),
            ],
          ),
        ),
      ),
    );
  }
}

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

/// Packs: what is applied, what can be applied, and the sample data a pack
/// creates.
class _PackSection extends ConsumerStatefulWidget {
  const _PackSection({required this.org, required this.isAdmin});

  final OrgSettings org;
  final bool isAdmin;

  @override
  ConsumerState<_PackSection> createState() => _PackSectionState();
}

class _PackSectionState extends ConsumerState<_PackSection> {
  bool _busy = false;

  Future<void> _apply(VerticalPack pack) async {
    // Additive-only and safe to repeat, so re-applying the current pack is
    // allowed rather than blocked. It reports everything skipped.
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Apply "${pack.name}"?'),
        content: const Text(
          'This adds starter pipelines, tags, custom fields, products and a '
          'set of sample records. Anything already set up is left exactly as '
          'it is.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Apply'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _busy = true);
    final result = await ref
        .read(orgSettingsProvider.notifier)
        .applyPack(pack.id);
    if (!mounted) return;
    setState(() => _busy = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(result.error ?? result.report!.summary)),
    );
  }

  Future<void> _clearSampleData() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Clear sample data?'),
        content: const Text(
          'Permanently deletes every sample record a pack created for this '
          'organization. Your real records are never touched, and any sample '
          'record you have since attached real work to is kept. This cannot '
          'be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Clear'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _busy = true);
    final result = await ref
        .read(orgSettingsProvider.notifier)
        .clearSampleData();
    if (!mounted) return;
    setState(() => _busy = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          result.error ??
              sampleDataResult(
                deleted: result.deleted,
                retained: result.retained,
              ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final org = widget.org;
    final packs = ref.watch(orgPacksProvider).value ?? const <VerticalPack>[];
    // The registry entry matching `org.vertical`, or null when no pack has been
    // applied or the id is one this build does not know.
    final applied = packs.where((pack) => pack.id == org.vertical).firstOrNull;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          color: AppColors.surface,
          margin: const EdgeInsets.only(bottom: 1),
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'First pack applied',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                applied?.name ??
                    (org.vertical.isEmpty ? 'None yet' : org.vertical),
                style: AppTypography.body.copyWith(fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 6),
              Text(
                'A pack adds starter pipelines, tags, custom fields, products '
                'and sample records for one kind of business. Applying one '
                'only fills in what this organization is missing.',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textTertiary,
                ),
              ),
            ],
          ),
        ),
        if (!widget.isAdmin)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Text(
              'Applying a pack or clearing sample data is limited to '
              'administrators.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          )
        else ...[
          for (final pack in packs)
            _PackRow(
              pack: pack,
              isApplied: pack.id == org.vertical,
              busy: _busy,
              onApply: () => _apply(pack),
            ),
          if (packs.isEmpty)
            Container(
              color: AppColors.surface,
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
              child: Text(
                'No packs available right now.',
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 20, 16, 0),
            child: SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _busy ? null : _clearSampleData,
                icon: const Icon(LucideIcons.trash2, size: 16),
                label: const Text('Clear sample data'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.danger600,
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: Text(
              'Removes only the records a pack created as samples. Your real '
              'records are never touched.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _PackRow extends StatelessWidget {
  const _PackRow({
    required this.pack,
    required this.isApplied,
    required this.busy,
    required this.onApply,
  });

  final VerticalPack pack;
  final bool isApplied;
  final bool busy;
  final VoidCallback onApply;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  pack.name,
                  style: AppTypography.body.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              if (isApplied)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.success50,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppColors.success200),
                  ),
                  child: Text(
                    'Applied',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.success600,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
            ],
          ),
          if (pack.description.isNotEmpty) ...[
            const SizedBox(height: 3),
            Text(
              pack.description,
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: busy ? null : onApply,
              child: Text(isApplied ? 'Apply again' : 'Apply'),
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
