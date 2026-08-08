import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/access_token.dart';
import '../../providers/settings_provider.dart';
import 'api_token_form_sheet.dart';

/// Your own API tokens: issue one, see what you have, revoke one.
///
/// **The screen that was missing.** `/api/profile/tokens/` has always been
/// self-scoped and open to every member, and nothing in either client called
/// it. The only token screen either app carried was the org-wide oversight
/// list, which answers a member 403, so somebody who wanted to script against
/// their own CRM had to be handed a token by an admin.
///
/// **What is deliberately absent.** No owner line, because every row is yours.
/// No org totals, because you cannot see anybody else's rows to count. No
/// "revoke them all", because that is an offboarding action and offboarding is
/// the admin's screen. Copying the oversight layout here would draw an org-wide
/// surface out of a self-scoped one.
///
/// **A token value is shown once.** The server keeps a SHA-256 hash and a
/// 13-character prefix, so there is nothing to re-display later. The reveal
/// dialog is the only place a full value appears, and nothing logs it.
class MyApiTokensScreen extends ConsumerWidget {
  const MyApiTokensScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(myAccessTokensProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Your API tokens'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => _ErrorState(
          onRetry: () => ref.read(myAccessTokensProvider.notifier).refresh(),
        ),
        data: (tokens) => RefreshIndicator(
          onRefresh: () => ref.read(myAccessTokensProvider.notifier).refresh(),
          child: tokens.isEmpty
              ? const _EmptyState()
              : ListView(
                  padding: const EdgeInsets.only(bottom: 96),
                  children: [
                    _Summary(tokens: tokens),
                    for (final token in tokens) _MyTokenRow(token: token),
                    const _SafetyNote(),
                  ],
                ),
        ),
      ),
      // No role gate. Every member may hold their own token, and the endpoint
      // already answers only their rows.
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _create(context, ref),
        icon: const Icon(LucideIcons.plus),
        label: const Text('New token'),
      ),
    );
  }

  Future<void> _create(BuildContext context, WidgetRef ref) async {
    final draft = await showApiTokenFormSheet(context);
    if (draft == null || !context.mounted) return;

    final result = await ref
        .read(myAccessTokensProvider.notifier)
        .createToken(
          name: draft.name,
          expiryChoice: draft.expiryChoice,
          accessChoice: draft.accessChoice,
        );
    if (!context.mounted) return;

    if (result.error != null) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(result.error!)));
      return;
    }
    await _reveal(
      context,
      name: result.name ?? draft.name,
      value: result.value!,
    );
  }

  /// The one and only time the value is shown. Nothing keeps a copy after this
  /// dialog closes, and nothing logs it on the way here.
  Future<void> _reveal(
    BuildContext context, {
    required String name,
    required String value,
  }) {
    return showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: Text('"$name" created, copy it now'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                tokenRevealWarning,
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
                  value,
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
              await Clipboard.setData(ClipboardData(text: value));
              if (!ctx.mounted) return;
              ScaffoldMessenger.of(
                ctx,
              ).showSnackBar(const SnackBar(content: Text('Token copied')));
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
}

class _Summary extends StatelessWidget {
  const _Summary({required this.tokens});

  final List<AccessToken> tokens;

  @override
  Widget build(BuildContext context) {
    final live = tokens.where((t) => t.isLive).length;
    return Container(
      width: double.infinity,
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Text(
        '$live live of ${tokens.length} you have issued',
        style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
      ),
    );
  }
}

class _MyTokenRow extends ConsumerWidget {
  const _MyTokenRow({required this.token});

  final AccessToken token;

  Future<void> _revoke(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Revoke "${token.name}"?'),
        content: Text(tokenRevokeExplanation),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Revoke'),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;

    final error = await ref
        .read(myAccessTokensProvider.notifier)
        .revokeToken(token.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? 'Token revoked')));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stale = token.stalenessNote(DateTime.now());
    return Opacity(
      opacity: token.isLive ? 1 : 0.6,
      child: Container(
        color: AppColors.surface,
        margin: const EdgeInsets.only(bottom: 1),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    token.name,
                    style: AppTypography.body.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                _StatusChip(label: token.statusLabel, isLive: token.isLive),
              ],
            ),
            const SizedBox(height: 3),
            // The prefix, and only the prefix. The server keeps a hash.
            Text(
              '${token.tokenPrefix}...',
              style: AppTypography.caption.copyWith(
                fontFamily: 'monospace',
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 6),
            // No owner line: every row here is yours.
            Text(
              token.scopeSummaryFor(ownerLabel: 'you'),
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              tokenActivityLine(token),
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
              ),
            ),
            if (stale != null) ...[
              const SizedBox(height: 2),
              Text(
                stale,
                style: AppTypography.caption.copyWith(
                  color: AppColors.warning600,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
            if (token.isLive) ...[
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () => _revoke(context, ref),
                  child: const Text('Revoke'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label, required this.isLive});

  final String label;
  final bool isLive;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: isLive ? AppColors.success50 : AppColors.surfaceDim,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
          color: isLive ? AppColors.success200 : AppColors.border,
        ),
      ),
      child: Text(
        label,
        style: AppTypography.caption.copyWith(
          color: isLive ? AppColors.success600 : AppColors.textSecondary,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _SafetyNote extends StatelessWidget {
  const _SafetyNote();

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(LucideIcons.shieldAlert, size: 18, color: AppColors.warning600),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'A token is you',
                  style: AppTypography.body.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'It authenticates as your profile and inherits your role and '
                  'your org, so anyone holding it can do what you can. Revoke '
                  'it here the moment it is not needed. An admin can see and '
                  'revoke it too.',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(32, 72, 32, 32),
          child: Column(
            children: [
              Icon(
                LucideIcons.keyRound,
                size: 40,
                color: AppColors.textTertiary,
              ),
              const SizedBox(height: 16),
              Text('No tokens yet', style: AppTypography.h3),
              const SizedBox(height: 8),
              Text(
                'A token lets a script, an integration or an agent call the '
                'API as you, with your role and your org. Create one when you '
                'need it, and revoke it the moment you do not.',
                style: AppTypography.body.copyWith(
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ],
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
              size: 36,
              color: AppColors.textTertiary,
            ),
            const SizedBox(height: 14),
            Text('Could not load your tokens', style: AppTypography.h3),
            const SizedBox(height: 14),
            OutlinedButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
