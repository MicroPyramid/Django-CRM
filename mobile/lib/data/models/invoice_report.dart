/// The invoice reports, from `/invoices/reports/dashboard/` and
/// `/invoices/reports/aging/`.
///
/// **Both endpoints are admin-only.** `_forbid_non_admin_reports` answers 403
/// to everyone else, so a non-admin opening this screen gets a refusal from
/// the server rather than an empty report, and the screen says so.
///
/// Every amount here is an org-wide sum with no currency grouping, exactly as
/// the invoice list totals are. In a single-currency org that is right; in a
/// mixed one it adds unlike things, and neither endpoint sends a breakdown
/// that would let a client correct it.
class InvoiceDashboard {
  const InvoiceDashboard({
    this.totalInvoiced = 0,
    this.totalPaid = 0,
    this.totalDue = 0,
    this.invoiceCount = 0,
    this.averageDaysToPay = 0,
    this.overdueCount = 0,
    this.overdueAmount = 0,
    this.revenue30d = 0,
    this.invoiced30d = 0,
    this.statusCounts = const {},
    this.estimatesPending = 0,
    this.estimatesAccepted = 0,
    this.estimatesDeclined = 0,
  });

  final double totalInvoiced;
  final double totalPaid;
  final double totalDue;
  final int invoiceCount;

  /// Issue date to payment date, in whole days, over paid invoices carrying
  /// both dates. Zero when nothing has been paid yet, which is why the screen
  /// hides it rather than printing "0 days to pay" for a new org.
  final int averageDaysToPay;

  final int overdueCount;
  final double overdueAmount;
  final double revenue30d;
  final double invoiced30d;
  final Map<String, int> statusCounts;
  final int estimatesPending;
  final int estimatesAccepted;
  final int estimatesDeclined;

  factory InvoiceDashboard.fromJson(Map<String, dynamic> json) {
    final summary = _map(json['summary']);
    final overdue = _map(json['overdue']);
    final recent = _map(json['recent_activity']);
    final estimates = _map(json['estimates']);
    final counts = _map(json['status_counts']);
    return InvoiceDashboard(
      totalInvoiced: _num(summary['total_invoiced']),
      totalPaid: _num(summary['total_paid']),
      totalDue: _num(summary['total_due']),
      invoiceCount: json['invoice_count'] as int? ?? 0,
      averageDaysToPay: json['average_days_to_pay'] as int? ?? 0,
      overdueCount: overdue['count'] as int? ?? 0,
      overdueAmount: _num(overdue['amount']),
      revenue30d: _num(recent['revenue_30d']),
      invoiced30d: _num(recent['invoiced_30d']),
      statusCounts: {
        for (final entry in counts.entries)
          if (entry.value is int) entry.key: entry.value as int,
      },
      estimatesPending: estimates['pending'] as int? ?? 0,
      estimatesAccepted: estimates['accepted'] as int? ?? 0,
      estimatesDeclined: estimates['declined'] as int? ?? 0,
    );
  }
}

/// One ageing bucket. The server caps `invoices` at ten per bucket while
/// `count` and `amount` cover the whole bucket, so the two disagree on purpose
/// and the screen must not present the listed rows as the total.
class AgingBucket {
  const AgingBucket({required this.label, this.count = 0, this.amount = 0});

  final String label;
  final int count;
  final double amount;

  factory AgingBucket.fromJson(String label, dynamic node) {
    final map = _map(node);
    return AgingBucket(
      label: label,
      count: map['count'] as int? ?? 0,
      amount: _num(map['amount']),
    );
  }
}

/// Accounts receivable ageing, oldest money first.
class AgingReport {
  const AgingReport({
    this.buckets = const [],
    this.total = 0,
    this.overdue = 0,
  });

  final List<AgingBucket> buckets;

  /// The server's own figure over every unpaid invoice, not a sum of the
  /// buckets above. They should agree, and when they do not the server is
  /// right: it counted the whole queryset while a bucket list can be capped.
  final double total;

  /// Past the due date only, so `total` minus what is merely not yet due.
  final double overdue;

  factory AgingReport.fromJson(Map<String, dynamic> json) {
    return AgingReport(
      buckets: [
        AgingBucket.fromJson('Not yet due', json['current']),
        AgingBucket.fromJson('1 to 30 days', json['1_30_days']),
        AgingBucket.fromJson('31 to 60 days', json['31_60_days']),
        AgingBucket.fromJson('61 to 90 days', json['61_90_days']),
        AgingBucket.fromJson('Over 90 days', json['over_90_days']),
      ],
      total: _num(_map(json['total'])['amount']),
      overdue: _num(_map(json['overdue'])['amount']),
    );
  }
}

Map<String, dynamic> _map(dynamic value) =>
    value is Map<String, dynamic> ? value : const {};

double _num(dynamic value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}
