import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/theme.dart';
import '../../data/models/support_ticket.dart';
import '../../providers/support_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/common/menu_row.dart';

/// Help, in two tiers. See the web page at `routes/(app)/help/+page.svelte`.
///
/// The queue of tickets with the BottleCRM team is an enterprise feature, so a
/// community deployment has none and the provider raises [SupportUnavailable].
/// That is not an error state: it is the whole of what this deployment can
/// offer, so the screen shows the self-serve routes and how to reach a person.
class SupportListScreen extends ConsumerWidget {
  const SupportListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tickets = ref.watch(supportTicketsProvider);
    final unavailable = tickets.error is SupportUnavailable;
    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Help'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      floatingActionButton: unavailable
          ? null
          : FloatingActionButton.extended(
              onPressed: () async {
                final created = await context.push<bool>(AppRoutes.helpNew);
                if (created == true) {
                  ref.read(supportTicketsProvider.notifier).refresh();
                }
              },
              icon: const Icon(LucideIcons.plus),
              label: const Text('New ticket'),
            ),
      body: tickets.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => error is SupportUnavailable
            ? const _SelfServeHelp()
            : _ErrorState(
                message: error.toString().replaceFirst('Exception: ', ''),
                onRetry: () =>
                    ref.read(supportTicketsProvider.notifier).refresh(),
              ),
        data: (data) => RefreshIndicator(
          onRefresh: () => ref.read(supportTicketsProvider.notifier).refresh(),
          child: data.tickets.isEmpty
              ? const _EmptyState()
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 104),
                  itemCount: data.tickets.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) => _TicketRow(
                    ticket: data.tickets[index],
                    onTap: () => context.push(
                      AppRoutes.helpDetail.replaceFirst(
                        ':id',
                        data.tickets[index].id,
                      ),
                    ),
                  ),
                ),
        ),
      ),
    );
  }
}

class _TicketRow extends StatelessWidget {
  const _TicketRow({required this.ticket, required this.onTap});

  final SupportTicket ticket;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      shape: RoundedRectangleBorder(
        side: BorderSide(color: AppColors.border),
        borderRadius: BorderRadius.circular(8),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: onTap,
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 88),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Text(
                        ticket.subject,
                        style: AppTypography.body.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    _StatusChip(status: ticket.status),
                  ],
                ),
                const SizedBox(height: 7),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: [
                    Text(
                      ticket.reference,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    Text(
                      ticket.category.label,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    Text(
                      '${ticket.messageCount} messages',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    Text(
                      'Updated ${DateFormat('d MMM').format(ticket.lastActivityAt.toLocal())}',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final SupportStatus status;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    decoration: BoxDecoration(
      color: status.color.withValues(alpha: 0.1),
      borderRadius: BorderRadius.circular(99),
    ),
    child: Text(
      status.label,
      style: AppTypography.caption.copyWith(
        color: status.color,
        fontWeight: FontWeight.w600,
      ),
    ),
  );
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.fromLTRB(32, 80, 32, 120),
    children: [
      Icon(LucideIcons.lifeBuoy, size: 40, color: AppColors.textTertiary),
      const SizedBox(height: 14),
      Text(
        'No support tickets',
        textAlign: TextAlign.center,
        style: AppTypography.h3,
      ),
      const SizedBox(height: 7),
      Text(
        'Open a ticket when you need help with BottleCRM. Replies and status changes stay attached to it.',
        textAlign: TextAlign.center,
        style: AppTypography.body.copyWith(color: AppColors.textSecondary),
      ),
    ],
  );
}

/// What Help is on a deployment with no BottleCRM support queue.
class _SelfServeHelp extends StatelessWidget {
  const _SelfServeHelp();

  static const _issues = 'https://github.com/django-crm/Django-CRM/issues';
  static const _email = 'mailto:support@bottlecrm.io';

  Future<void> _open(BuildContext context, String url) async {
    final messenger = ScaffoldMessenger.of(context);
    final opened = await launchUrl(
      Uri.parse(url),
      mode: LaunchMode.externalApplication,
    );
    if (!opened) {
      messenger.showSnackBar(
        SnackBar(content: Text('Could not open $url on this device.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.only(bottom: 32),
    children: [
      _header('Start here'),
      MenuRow(
        icon: LucideIcons.bookOpen,
        label: 'Knowledge base',
        description: 'The answers your team has already written down',
        onTap: () => context.push(AppRoutes.solutions),
      ),
      MenuRow(
        icon: LucideIcons.lifeBuoy,
        label: 'Your tickets',
        description: 'Everything open, and who it is waiting on',
        onTap: () => context.push(AppRoutes.tickets),
      ),
      MenuRow(
        icon: LucideIcons.clipboardList,
        label: 'Settings',
        description: 'Routing, escalation, business hours and inbound email',
        onTap: () => context.push(AppRoutes.settings),
      ),
      _header('If that did not do it'),
      MenuRow(
        icon: LucideIcons.bug,
        label: 'Report a bug',
        description:
            'Public issue tracker, fastest route for anything '
            'reproducible',
        onTap: () => _open(context, _issues),
      ),
      MenuRow(
        icon: LucideIcons.mail,
        label: 'Email support@bottlecrm.io',
        description:
            'For anything involving your data, billing or an account '
            'you cannot get into',
        onTap: () => _open(context, _email),
      ),
      _header('What to include when you write'),
      Container(
        color: AppColors.surface,
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Two things turn a two-day exchange into one message.',
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 12),
            _fact(
              'What you expected',
              'The thing you were trying to do, in one sentence.',
            ),
            const SizedBox(height: 10),
            _fact(
              'What happened instead',
              'The exact wording of any error. "It did not work" and '
                  '"Something went wrong" are the same message to us.',
            ),
            const SizedBox(height: 14),
            Text(
              'Please do not attach screenshots containing an invoice link, an '
              'API token or a survey URL. Each of those is a working '
              'credential for whoever ends up holding it.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    ],
  );

  static Widget _header(String text) => Padding(
    padding: const EdgeInsets.fromLTRB(16, 22, 16, 8),
    child: Text(
      text.toUpperCase(),
      style: AppTypography.caption.copyWith(
        color: AppColors.textTertiary,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.6,
      ),
    ),
  );

  static Widget _fact(String term, String detail) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        term,
        style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
      ),
      const SizedBox(height: 2),
      Text(
        detail,
        style: AppTypography.body.copyWith(color: AppColors.textSecondary),
      ),
    ],
  );
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            LucideIcons.circleAlert,
            size: 36,
            color: AppColors.textTertiary,
          ),
          const SizedBox(height: 12),
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          OutlinedButton(onPressed: onRetry, child: const Text('Try again')),
        ],
      ),
    ),
  );
}
