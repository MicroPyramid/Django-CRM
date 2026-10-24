import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/lead_intake.dart';
import '../../data/models/mailbox.dart';
import '../../providers/auth_provider.dart';
import '../../providers/lead_intakes_provider.dart';
import '../../providers/settings_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/common/common.dart';
import 'mailbox_form_sheet.dart';

/// Every way a lead arrives without anyone typing it: web forms, webhooks and
/// lead addresses, as on the web's Lead capture page.
///
/// Webhooks are admin-only server-side, reads included, so a member is never
/// shown them; an API that predates them answers 404 and the part is hidden.
/// Lead addresses come from the inbound mailbox list, which any member reads,
/// and show only where the API has them. Creating a webhook and mapping its
/// fields are web only.
class LeadCaptureScreen extends ConsumerWidget {
  const LeadCaptureScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isAdmin = ref.watch(isOrgAdminProvider);
    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Lead capture'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await Future.wait([
            if (isAdmin) ref.read(leadIntakesProvider.notifier).refresh(),
            ref.read(mailboxesProvider.notifier).refresh(),
          ]);
        },
        child: ListView(
          padding: const EdgeInsets.only(bottom: 48),
          children: [
            const _SectionHeader('Web forms'),
            MenuRow(
              icon: LucideIcons.clipboardList,
              label: 'Web forms',
              description: 'Forms you embed on your own site',
              onTap: () => context.push(AppRoutes.settingsWebForms),
            ),
            if (isAdmin) const _Webhooks(),
            _LeadAddresses(isAdmin: isAdmin),
          ],
        ),
      ),
    );
  }
}

class _Webhooks extends ConsumerWidget {
  const _Webhooks();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(leadIntakesProvider);
    if (leadIntakesNotOffered(async)) return const SizedBox.shrink();
    final Widget body;
    if (async.isLoading) {
      body = const Padding(
        padding: EdgeInsets.all(16),
        child: Center(child: CircularProgressIndicator()),
      );
    } else if (async.hasError) {
      body = _Retry(
        message: 'Could not load the webhooks.',
        onRetry: () => ref.read(leadIntakesProvider.notifier).refresh(),
      );
    } else if (async.value!.isEmpty) {
      body = const _Note(
        'No webhooks yet. Create one on the web, where its fields are mapped. '
        'Here you can copy its URL, replace its key, switch it off and read '
        'its deliveries.',
      );
    } else {
      body = Column(
        children: [
          for (final intake in async.value!) _IntakeRow(intake: intake),
        ],
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [const _SectionHeader('Webhooks'), body],
    );
  }
}

class _IntakeRow extends StatelessWidget {
  const _IntakeRow({required this.intake});

  final LeadIntake intake;

  @override
  Widget build(BuildContext context) {
    final received = intake.lastReceivedAt;
    return Material(
      color: AppColors.surface,
      child: InkWell(
        onTap: () =>
            context.push(AppRoutes.settingsLeadCaptureWebhook(intake.id)),
        child: Container(
          constraints: const BoxConstraints(minHeight: 56),
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
          decoration: BoxDecoration(
            border: Border(bottom: BorderSide(color: AppColors.gray100)),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      intake.name.isEmpty ? 'Untitled webhook' : intake.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.body.copyWith(
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      received == null
                          ? '${intake.presetLabel} · nothing received yet'
                          : '${intake.presetLabel} · last post '
                                '${intakeWhen.format(received)}',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    if (intake.lastError.isNotEmpty) ...[
                      const SizedBox(height: 3),
                      Text(
                        intake.lastError,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.caption.copyWith(
                          color: AppColors.warning600,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 10),
              IntakeStatePill(intake: intake),
            ],
          ),
        ),
      ),
    );
  }
}

final DateFormat intakeWhen = DateFormat('d MMM yyyy, HH:mm');

class IntakeStatePill extends StatelessWidget {
  const IntakeStatePill({super.key, required this.intake});

  final LeadIntake intake;

  @override
  Widget build(BuildContext context) {
    final color = intake.stateLabel == 'Receiving'
        ? AppColors.success600
        : AppColors.textSecondary;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        intake.stateLabel,
        style: AppTypography.caption.copyWith(
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _LeadAddresses extends ConsumerWidget {
  const _LeadAddresses({required this.isAdmin});

  final bool isAdmin;

  Future<void> _edit(
    BuildContext context,
    WidgetRef ref,
    MailboxesState state,
    Mailbox? existing,
  ) async {
    final payload = await showMailboxFormSheet(
      context,
      existing: existing,
      leadsOffered: true,
      generatedDomain: state.generatedDomain,
      startAsLeads: true,
    );
    if (payload == null || !context.mounted) return;
    final notifier = ref.read(mailboxesProvider.notifier);
    final error = existing == null
        ? await notifier.createMailbox(payload)
        : await notifier.updateMailbox(existing.id, payload);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error ?? (existing == null ? 'Address added' : 'Address saved'),
        ),
      ),
    );
  }

  Future<void> _toggle(
    BuildContext context,
    WidgetRef ref,
    Mailbox mailbox,
  ) async {
    final notifier = ref.read(mailboxesProvider.notifier);
    final error = mailbox.isActive
        ? await notifier.deactivateMailbox(mailbox.id)
        : await notifier.activateMailbox(mailbox.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error ??
              (mailbox.isActive ? 'Address turned off' : 'Address turned on'),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(mailboxesProvider);
    if (async.isLoading) return const SizedBox.shrink();
    if (async.hasError) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionHeader('Lead addresses'),
          _Retry(
            message: 'Could not load the lead addresses.',
            onRetry: () => ref.read(mailboxesProvider.notifier).refresh(),
          ),
        ],
      );
    }
    final state = async.value!;
    if (!state.leadsOffered) return const SizedBox.shrink();
    final addresses = state.mailboxes.where((m) => m.createsLeads).toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader('Lead addresses'),
        if (addresses.isEmpty)
          const _Note(
            'No lead address yet. Forward an enquiry to one, or point a '
            'portal\'s notification emails at it, and each email becomes a '
            'lead.',
          ),
        for (final mailbox in addresses)
          _AddressRow(
            mailbox: mailbox,
            canEdit: isAdmin,
            onEdit: () => _edit(context, ref, state, mailbox),
            onToggle: () => _toggle(context, ref, mailbox),
          ),
        if (isAdmin)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: SizedBox(
              height: 44,
              child: OutlinedButton.icon(
                onPressed: () => _edit(context, ref, state, null),
                icon: const Icon(LucideIcons.plus, size: 16),
                label: const Text('Add a lead address'),
              ),
            ),
          ),
      ],
    );
  }
}

class _AddressRow extends StatelessWidget {
  const _AddressRow({
    required this.mailbox,
    required this.canEdit,
    required this.onEdit,
    required this.onToggle,
  });

  final Mailbox mailbox;
  final bool canEdit;
  final VoidCallback onEdit;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final why = mailbox.deliveryExplanation;
    final live = mailbox.delivery.isLive;
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            mailbox.address,
            style: AppTypography.body.copyWith(
              fontWeight: FontWeight.w600,
              color: live ? AppColors.textPrimary : AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 6),
          StatusBadge(
            label: mailbox.deliveryLabel,
            color: live ? AppColors.success600 : AppColors.gray500,
          ),
          const SizedBox(height: 6),
          Text(
            mailbox.opensAs,
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          if (why != null) ...[
            const SizedBox(height: 6),
            Text(
              why,
              style: AppTypography.caption.copyWith(
                color: AppColors.warning600,
              ),
            ),
          ],
          if (canEdit) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                SizedBox(
                  height: 44,
                  child: OutlinedButton(
                    onPressed: onEdit,
                    child: const Text('Edit'),
                  ),
                ),
                SizedBox(
                  height: 44,
                  child: OutlinedButton(
                    onPressed: onToggle,
                    child: Text(mailbox.isActive ? 'Turn off' : 'Turn on'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

/// The one place a webhook key is shown. Nothing keeps a copy after the
/// dialog closes, and nothing logs it on the way here.
Future<void> showIntakeKey(BuildContext context, {required String keyValue}) {
  return showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (ctx) => AlertDialog(
      title: const Text('Copy the new key now'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'This is the only time the key is shown. Paste it into the tool '
              'that posts to this webhook; replace it again if it is lost.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 14),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.surfaceDim,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.border),
              ),
              child: SelectableText(
                keyValue,
                style: AppTypography.caption.copyWith(
                  fontFamily: 'monospace',
                  color: AppColors.textPrimary,
                ),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton.icon(
          onPressed: () async {
            await Clipboard.setData(ClipboardData(text: keyValue));
            if (!ctx.mounted) return;
            ScaffoldMessenger.of(
              ctx,
            ).showSnackBar(const SnackBar(content: Text('Key copied')));
          },
          icon: const Icon(LucideIcons.copy, size: 16),
          label: const Text('Copy'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(ctx),
          child: const Text('Done'),
        ),
      ],
    ),
  );
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

class _Note extends StatelessWidget {
  const _Note(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
      child: Text(
        text,
        style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
      ),
    );
  }
}

class _Retry extends StatelessWidget {
  const _Retry({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
      child: Row(
        children: [
          Expanded(
            child: Text(
              message,
              style: AppTypography.caption.copyWith(color: AppColors.danger600),
            ),
          ),
          TextButton(
            style: TextButton.styleFrom(minimumSize: const Size(48, 44)),
            onPressed: onRetry,
            child: const Text('Try again'),
          ),
        ],
      ),
    );
  }
}
