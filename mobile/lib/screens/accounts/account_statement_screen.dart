import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../config/api_config.dart';
import '../../core/theme/theme.dart';
import '../../data/models/account_statement.dart';
import '../../data/models/deal.dart' show Currency;
import '../../providers/account_statement_provider.dart';
import '../../routes/app_router.dart';
import '../../services/attachment_upload.dart';
import '../invoices/invoice_format.dart';
import '../invoices/invoice_shell.dart';

/// An account's statement (#810): per currency, the opening balance, the
/// period's invoices, payments and cancellations with a running balance, and
/// the closing balance. The web page `/accounts/<id>/statement` and the PDF
/// show the same figures, all computed by the server.
///
/// **Admin-only on the server.** The account screen offers this only to
/// admins, and a member who reaches it anyway is told so, with no Retry: a
/// 403 does not become a 200 by asking again.
class AccountStatementScreen extends ConsumerStatefulWidget {
  const AccountStatementScreen({super.key, required this.accountId});

  final String accountId;

  @override
  ConsumerState<AccountStatementScreen> createState() =>
      _AccountStatementScreenState();
}

class _AccountStatementScreenState
    extends ConsumerState<AccountStatementScreen> {
  // Null asks for the server's default: this month so far, in the org's day.
  String? _start;
  String? _end;
  bool _saving = false;

  StatementRequest get _request =>
      (accountId: widget.accountId, start: _start, end: _end);

  void _show(String? start, String? end) => setState(() {
    _start = start;
    _end = end;
  });

  Future<void> _pickPeriod(AccountStatement? shown) async {
    final now = DateTime.now();
    final current = shown == null
        ? null
        : DateTimeRange(
            start: DateTime.parse(shown.startDate),
            end: DateTime.parse(shown.endDate),
          );
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2000),
      lastDate: DateTime(now.year + 5),
      initialDateRange: current,
    );
    if (picked == null) return;
    // The server caps a period at 366 days and says so if this is longer.
    _show(_ymd(picked.start), _ymd(picked.end));
  }

  Future<void> _savePdf(AccountStatement statement) async {
    setState(() => _saving = true);
    final result = await downloadAttachment(
      url: ApiConfig.accountStatementPdf(
        widget.accountId,
        start: statement.startDate,
        end: statement.endDate,
      ),
      fileName: 'Statement_${statement.startDate}_${statement.endDate}.pdf',
    );
    if (!mounted) return;
    setState(() => _saving = false);
    if (!result.success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.error ?? 'Could not save the statement'),
          backgroundColor: AppColors.danger600,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(accountStatementProvider(_request));
    final statement = async.value;

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Statement'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        leading: IconButton(
          icon: const Icon(LucideIcons.chevronLeft),
          onPressed: () => context.pop(),
        ),
        actions: [
          if (statement != null && !async.hasError)
            IconButton(
              icon: const Icon(LucideIcons.download, size: 20),
              tooltip: 'Save PDF',
              onPressed: _saving ? null : () => _savePdf(statement),
            ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) {
          if (error is StatementRefusal && error.forbidden) {
            return InvoiceErrorState(
              message: 'Statements are for administrators',
              detail: error.message,
            );
          }
          if (error is StatementRefusal && error.statusCode == 404) {
            return const InvoiceErrorState(
              message:
                  'This account does not exist, or you do not have access to it',
            );
          }
          if (error is StatementRefusal) {
            // A period the server will not cover: say why, keep the controls.
            return ListView(
              padding: const EdgeInsets.only(bottom: 32),
              children: [
                _periodCard(null),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                  child: Text(
                    error.message,
                    style: AppTypography.body.copyWith(
                      color: AppColors.danger600,
                    ),
                  ),
                ),
              ],
            );
          }
          return InvoiceErrorState(
            message: 'Could not load the statement',
            onRetry: () => ref.invalidate(accountStatementProvider(_request)),
          );
        },
        data: (statement) => RefreshIndicator(
          onRefresh: () async =>
              ref.invalidate(accountStatementProvider(_request)),
          child: ListView(
            padding: const EdgeInsets.only(bottom: 32),
            children: [
              _periodCard(statement),
              if (statement.sections.isEmpty)
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 20, 16, 0),
                  child: Text(
                    'Nothing was billed or paid in this period, and nothing '
                    'is owed.',
                    style: AppTypography.body.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
              for (final section in statement.sections) ...[
                _summary(section, labelled: statement.sections.length > 1),
                _entries(section),
              ],
            ],
          ),
        ),
      ),
    );
  }

  /// The account, the period shown and the ways to change it. With no
  /// statement (a refused period) it shows the dates that were asked for.
  Widget _periodCard(AccountStatement? statement) {
    final start = statement?.startDate ?? _start;
    final end = statement?.endDate ?? _end;
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (statement != null && statement.accountName.isNotEmpty)
            Text(
              statement.accountName,
              style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
            ),
          if (start != null && end != null)
            Text(
              '${_day(start)} to ${_day(end)}',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 4,
            runSpacing: 0,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              OutlinedButton.icon(
                icon: const Icon(LucideIcons.calendarRange, size: 16),
                label: const Text('Change period'),
                onPressed: () => _pickPeriod(statement),
              ),
              if (start != null)
                TextButton(
                  onPressed: () {
                    final previous = previousMonth(start);
                    _show(previous.start, previous.end);
                  },
                  child: const Text('Previous month'),
                ),
              TextButton(
                onPressed: () => _show(null, null),
                child: const Text('This month'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _summary(StatementSection section, {required bool labelled}) {
    final symbol = Currency.symbolFor(section.currency);
    final inCredit = section.closingBalance < 0;
    return Container(
      margin: const EdgeInsets.only(top: 8),
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (labelled)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(
                'In ${section.currency}',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          InvoiceFactRow(
            label: 'Opening balance',
            value: money(section.openingBalance, symbol),
          ),
          InvoiceFactRow(
            label: 'Invoiced',
            value: money(section.invoiced, symbol),
          ),
          InvoiceFactRow(label: 'Paid', value: money(section.paid, symbol)),
          if (section.cancelled > 0)
            InvoiceFactRow(
              label: 'Cancelled',
              value: money(section.cancelled, symbol),
            ),
          const Divider(height: 18),
          InvoiceFactRow(
            label: inCredit ? 'In credit' : 'Balance due',
            value: money(section.closingBalance.abs(), symbol),
          ),
        ],
      ),
    );
  }

  /// One row per entry; tapping it opens the invoice it belongs to.
  Widget _entries(StatementSection section) {
    final symbol = Currency.symbolFor(section.currency);
    return Container(
      color: AppColors.surface,
      child: Column(
        children: [
          for (final entry in section.entries)
            InkWell(
              onTap: () =>
                  context.push('${AppRoutes.invoices}/${entry.invoiceId}'),
              child: Container(
                constraints: const BoxConstraints(minHeight: 56),
                padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
                decoration: BoxDecoration(
                  border: Border(top: BorderSide(color: Colors.grey.shade200)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _day(entry.date),
                            style: AppTypography.caption.copyWith(
                              color: AppColors.textSecondary,
                            ),
                          ),
                          Text(entry.description, style: AppTypography.body),
                          Text(
                            entry.invoiceNumber,
                            style: AppTypography.caption.copyWith(
                              color: AppColors.textTertiary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          money(entry.amount, symbol),
                          style: AppTypography.body.copyWith(
                            fontWeight: FontWeight.w600,
                            color: entry.amount < 0
                                ? AppColors.success600
                                : AppColors.textPrimary,
                          ),
                        ),
                        Text(
                          'Balance ${money(entry.balance, symbol)}',
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
        ],
      ),
    );
  }
}

String _ymd(DateTime d) =>
    '${d.year}-${d.month.toString().padLeft(2, '0')}-'
    '${d.day.toString().padLeft(2, '0')}';

String _day(String iso) {
  final day = DateTime.tryParse(iso);
  return day == null ? iso : DateFormat('d MMM yyyy').format(day);
}
