import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/deal.dart' show Currency;
import '../../providers/auth_provider.dart';
import '../../providers/invoice_extras_provider.dart';
import 'invoice_format.dart';
import 'invoice_shell.dart';

/// Invoice reports: the money summary and the receivables ageing.
///
/// **Both endpoints are admin-only.** A non-admin gets a 403, and this screen
/// says so plainly instead of showing an empty report with a Retry button that
/// can never work.
///
/// Every figure is an org-wide sum with no currency grouping, which is right
/// for a single-currency org and adds unlike things in a mixed one. Neither
/// endpoint sends a breakdown, so unlike the invoice list this screen cannot
/// detect the mixed case and does not claim to: it uses the org's own currency
/// symbol, the same choice the web reports page makes.
class InvoiceReportsScreen extends ConsumerWidget {
  const InvoiceReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(invoiceReportsProvider);
    final symbol = Currency.fromString(
      ref.watch(selectedOrgProvider)?.defaultCurrency,
    ).symbol;

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Reports'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) {
          if (error is ReportsForbidden) {
            return InvoiceErrorState(
              message: 'Reports are for administrators',
              detail: error.message,
              // No Retry: a 403 does not become a 200 by asking again.
            );
          }
          return InvoiceErrorState(
            message: 'Could not load the reports',
            onRetry: () => ref.invalidate(invoiceReportsProvider),
          );
        },
        data: (reports) {
          final d = reports.dashboard;
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(invoiceReportsProvider),
            child: ListView(
              padding: const EdgeInsets.only(bottom: 32),
              children: [
                _card('Money', [
                  InvoiceFactRow(
                    label: 'Invoiced, all time',
                    value: money(d.totalInvoiced, symbol),
                  ),
                  InvoiceFactRow(
                    label: 'Paid',
                    value: money(d.totalPaid, symbol),
                  ),
                  InvoiceFactRow(
                    label: 'Still owed',
                    value: money(d.totalDue, symbol),
                  ),
                  InvoiceFactRow(
                    label: 'Invoices raised',
                    value: '${d.invoiceCount}',
                  ),
                  // Hidden rather than shown as zero: an org that has never
                  // been paid has no average, and "0 days to pay" reads as
                  // instant payment.
                  if (d.averageDaysToPay > 0)
                    InvoiceFactRow(
                      label: 'Average days to pay',
                      value: '${d.averageDaysToPay}',
                    ),
                ]),
                if (d.overdueCount > 0)
                  _card('Overdue', [
                    InvoiceFactRow(
                      label: 'Invoices past due',
                      value: '${d.overdueCount}',
                    ),
                    InvoiceFactRow(
                      label: 'Amount',
                      value: money(d.overdueAmount, symbol),
                    ),
                  ], tone: AppColors.danger600),
                _card('Last 30 days', [
                  InvoiceFactRow(
                    label: 'Collected',
                    value: money(d.revenue30d, symbol),
                  ),
                  InvoiceFactRow(
                    label: 'Invoiced',
                    value: money(d.invoiced30d, symbol),
                  ),
                ]),
                _card('Receivables ageing', [
                  for (final bucket in reports.aging.buckets)
                    InvoiceFactRow(
                      label: '${bucket.label} (${bucket.count})',
                      value: money(bucket.amount, symbol),
                    ),
                  const Divider(height: 18),
                  InvoiceFactRow(
                    label: 'Outstanding in total',
                    value: money(reports.aging.total, symbol),
                  ),
                ]),
                if (d.estimatesPending +
                        d.estimatesAccepted +
                        d.estimatesDeclined >
                    0)
                  _card('Estimates', [
                    InvoiceFactRow(
                      label: 'Waiting on the client',
                      value: '${d.estimatesPending}',
                    ),
                    InvoiceFactRow(
                      label: 'Accepted',
                      value: '${d.estimatesAccepted}',
                    ),
                    InvoiceFactRow(
                      label: 'Declined',
                      value: '${d.estimatesDeclined}',
                    ),
                  ]),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        LucideIcons.info,
                        size: 14,
                        color: AppColors.textTertiary,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Figures cover the whole organisation and are summed '
                          'without regard to currency.',
                          style: AppTypography.caption.copyWith(
                            color: AppColors.textTertiary,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _card(String title, List<Widget> rows, {Color? tone}) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: AppTypography.caption.copyWith(
              color: tone ?? AppColors.textSecondary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          ...rows,
        ],
      ),
    );
  }
}
