import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/access_token.dart';
import '../../providers/auth_provider.dart';
import '../../providers/settings_provider.dart';
import 'api_token_form_sheet.dart';

/// Personal access tokens: the org-wide oversight view.
///
/// **THE ONE RULE THIS SCREEN EXISTS TO KEEP.** A token value is shown once, in
/// the response to the request that created it, and never again. The server
/// keeps a SHA-256 hash plus a 13-character prefix, so there is nothing to
/// re-display even if someone asks. Every row here shows the prefix and stops;
/// the reveal below is the only place a full value appears, and it is gone with
/// the dialog.
///
/// **Admin-only to read.** `/api/org/tokens/` lists every token across the org,
/// so it answers a member 403. The screen gates on role rather than issuing a
/// request it knows will fail. Creating is self-scoped underneath
/// (`POST /api/profile/tokens/` sets the owner from the caller's own profile),
/// so an admin here is always creating a token for themselves.
///
/// **"Owner deactivated" is a dormant row, not a live one.** Deactivating an
/// account sets `profile.is_active` false, and that is exactly the flag the
/// token authenticator checks, so the token is already refused at login. It is
/// worth revoking anyway: it would come back if the account were reactivated.
class ApiTokensScreen extends ConsumerWidget {
  const ApiTokensScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isAdmin = ref.watch(isOrgAdminProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('API tokens'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      body: isAdmin ? const _AdminBody() : const _MemberNotice(),
      floatingActionButton: isAdmin
          ? FloatingActionButton.extended(
              onPressed: () => _create(context, ref),
              icon: const Icon(LucideIcons.plus),
              label: const Text('New token'),
            )
          : null,
    );
  }

  Future<void> _create(BuildContext context, WidgetRef ref) async {
    final draft = await showApiTokenFormSheet(context);
    if (draft == null || !context.mounted) return;

    final result = await ref
        .read(accessTokensProvider.notifier)
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

/// The list itself is admin-gated server-side, so a member never issues it.
class _MemberNotice extends StatelessWidget {
  const _MemberNotice();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(LucideIcons.lock, size: 40, color: AppColors.textTertiary),
            const SizedBox(height: 16),
            Text(
              'Administrators only',
              style: AppTypography.h3,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'Reviewing every token in the organization is limited to '
              'administrators, because a token authenticates as its owner. Ask '
              'an admin if one needs issuing or revoking.',
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _AdminBody extends ConsumerWidget {
  const _AdminBody();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(accessTokensProvider);
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (_, _) => _ErrorState(
        onRetry: () => ref.read(accessTokensProvider.notifier).refresh(),
      ),
      data: (state) => RefreshIndicator(
        onRefresh: () => ref.read(accessTokensProvider.notifier).refresh(),
        child: ListView(
          padding: const EdgeInsets.only(bottom: 96),
          children: [
            _Totals(totals: state.totals),
            if (state.totals.orphaned > 0)
              _OrphanBanner(count: state.totals.orphaned),
            const _SectionHeader('Tokens'),
            if (state.tokens.isEmpty)
              const _Empty()
            else
              for (final token in state.tokens) _TokenRow(token: token),
            const _Footnote(),
          ],
        ),
      ),
    );
  }
}

class _Totals extends StatelessWidget {
  const _Totals({required this.totals});

  final TokenTotals totals;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Wrap(
        spacing: 22,
        runSpacing: 12,
        children: [
          _Stat(
            value: '${totals.live}',
            label: 'live',
            tone: AppColors.textPrimary,
          ),
          _Stat(
            value: '${totals.orphaned}',
            label: 'owner deactivated',
            tone: totals.orphaned > 0
                ? AppColors.warning600
                : AppColors.textPrimary,
          ),
          _Stat(
            // Measured from the last use, or from when the token was issued
            // when it has never been used. A token created a minute ago is not
            // "unused for 90 days", which is what this used to claim.
            value: '${totals.unused90d}',
            label: 'unused 90+ days',
            tone: totals.unused90d > 0
                ? AppColors.warning600
                : AppColors.textPrimary,
          ),
          _Stat(
            value: '${totals.count}',
            label: 'issued in total',
            tone: AppColors.textPrimary,
          ),
        ],
      ),
    );
  }
}

class _OrphanBanner extends ConsumerStatefulWidget {
  const _OrphanBanner({required this.count});

  final int count;

  @override
  ConsumerState<_OrphanBanner> createState() => _OrphanBannerState();
}

class _OrphanBannerState extends ConsumerState<_OrphanBanner> {
  bool _busy = false;

  Future<void> _revokeAll() async {
    setState(() => _busy = true);
    final result = await ref
        .read(accessTokensProvider.notifier)
        .revokeOrphaned();
    if (!mounted) return;
    setState(() => _busy = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          result.error ??
              'Revoked ${result.revoked} '
                  '${result.revoked == 1 ? 'token' : 'tokens'} on deactivated '
                  'accounts.',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final many = widget.count != 1;
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(LucideIcons.userX, size: 18, color: AppColors.warning600),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  '${widget.count} live ${many ? 'tokens belong' : 'token belongs'} '
                  'to a deactivated account. Deactivating already stops '
                  '${many ? 'them' : 'it'} at login, but '
                  '${many ? 'they are' : 'it is'} not revoked. Reactivating '
                  'the account would bring ${many ? 'them' : 'it'} back.',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: _busy ? null : _revokeAll,
              child: Text(many ? 'Revoke them all' : 'Revoke it'),
            ),
          ),
        ],
      ),
    );
  }
}

class _TokenRow extends ConsumerWidget {
  const _TokenRow({required this.token});

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
        .read(accessTokensProvider.notifier)
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
            // The prefix, and only the prefix. There is no full value to show:
            // the server keeps a hash.
            Text(
              '${token.tokenPrefix}...',
              style: AppTypography.caption.copyWith(
                fontFamily: 'monospace',
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '${token.owner.name} · ${token.owner.roleLabel}'
              '${token.owner.isActive ? '' : ' · deactivated'}',
              style: AppTypography.caption.copyWith(
                color: token.owner.isActive
                    ? AppColors.textSecondary
                    : AppColors.warning600,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              token.scopeSummary,
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

class _Stat extends StatelessWidget {
  const _Stat({required this.value, required this.label, required this.tone});

  final String value;
  final String label;
  final Color tone;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: AppTypography.h2.copyWith(
            fontWeight: FontWeight.w600,
            color: tone,
          ),
        ),
        Text(
          label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
      ],
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

class _Empty extends StatelessWidget {
  const _Empty();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 20),
      child: Text(
        'No tokens have been issued in this organization.',
        style: AppTypography.body.copyWith(color: AppColors.textSecondary),
      ),
    );
  }
}

class _Footnote extends StatelessWidget {
  const _Footnote();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 0),
      child: Text(
        'A token authenticates as its owner and inherits their role and '
        'organization. Issue one per integration so a single revocation stops '
        'a single thing, set an expiry, and revoke anything you cannot name a '
        'use for.',
        style: AppTypography.caption.copyWith(color: AppColors.textTertiary),
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
              'Could not load tokens',
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
