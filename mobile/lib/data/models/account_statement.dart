/// An account's statement (#810), from `GET /api/invoices/statements/<id>/`.
///
/// Per currency the server sends an opening balance, the period's invoices,
/// payments and cancellations in date order with a running balance, and a
/// closing balance. It does all the arithmetic, and the web page and the PDF
/// show the same figures; nothing here adds money up.
///
/// **Admin-only on the server**, like the invoice reports: a statement sums
/// every invoice on the account, including ones a member may not open.
class AccountStatement {
  const AccountStatement({
    required this.accountId,
    required this.accountName,
    required this.startDate,
    required this.endDate,
    required this.sections,
  });

  final String accountId;
  final String accountName;

  /// The period, `YYYY-MM-DD`, both days included.
  final String startDate;
  final String endDate;

  /// One per currency, ordered by code. Empty when nothing was billed or paid
  /// in the period and nothing is owed.
  final List<StatementSection> sections;

  factory AccountStatement.fromJson(Map<String, dynamic> json) {
    final account = json['account'] is Map ? json['account'] as Map : const {};
    return AccountStatement(
      accountId: '${account['id'] ?? ''}',
      accountName: '${account['name'] ?? ''}',
      startDate: '${json['start_date'] ?? ''}',
      endDate: '${json['end_date'] ?? ''}',
      sections: [
        for (final section in (json['currencies'] as List? ?? const []))
          if (section is Map<String, dynamic>)
            StatementSection.fromJson(section),
      ],
    );
  }
}

/// The statement in one currency. Never added to another: there are no
/// exchange rates.
class StatementSection {
  const StatementSection({
    required this.currency,
    required this.openingBalance,
    required this.invoiced,
    required this.paid,
    required this.cancelled,
    required this.closingBalance,
    required this.entries,
  });

  final String currency;
  final double openingBalance;
  final double invoiced;
  final double paid;
  final double cancelled;

  /// Negative when the account is in credit.
  final double closingBalance;
  final List<StatementEntry> entries;

  factory StatementSection.fromJson(Map<String, dynamic> json) =>
      StatementSection(
        currency: '${json['currency'] ?? ''}',
        openingBalance: _num(json['opening_balance']),
        invoiced: _num(json['invoiced']),
        paid: _num(json['paid']),
        cancelled: _num(json['cancelled']),
        closingBalance: _num(json['closing_balance']),
        entries: [
          for (final entry in (json['entries'] as List? ?? const []))
            if (entry is Map<String, dynamic>) StatementEntry.fromJson(entry),
        ],
      );
}

/// One line: an invoice billed, a payment, or a cancellation.
class StatementEntry {
  const StatementEntry({
    required this.date,
    required this.kind,
    required this.invoiceId,
    required this.invoiceNumber,
    required this.description,
    required this.amount,
    required this.balance,
  });

  /// `YYYY-MM-DD`.
  final String date;

  /// `invoice`, `payment` or `cancellation`.
  final String kind;
  final String invoiceId;
  final String invoiceNumber;
  final String description;

  /// Signed: positive adds to what the account owes, negative takes from it.
  final double amount;

  /// What the account owes after this line.
  final double balance;

  factory StatementEntry.fromJson(Map<String, dynamic> json) => StatementEntry(
    date: '${json['date'] ?? ''}',
    kind: '${json['kind'] ?? ''}',
    invoiceId: '${json['invoice_id'] ?? ''}',
    invoiceNumber: '${json['invoice_number'] ?? ''}',
    description: '${json['description'] ?? ''}',
    amount: _num(json['amount']),
    balance: _num(json['balance']),
  );
}

/// The whole calendar month before the one [iso] (`YYYY-MM-DD`) falls in.
/// Statements are read a month at a time, and stepping back by a tap beats
/// two date pickers.
({String start, String end}) previousMonth(String iso) {
  final day = DateTime.parse(iso);
  final first = DateTime(day.year, day.month - 1, 1);
  // Day 0 of the following month is this month's last day.
  final last = DateTime(first.year, first.month + 1, 0);
  String ymd(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';
  return (start: ymd(first), end: ymd(last));
}

double _num(Object? value) =>
    value is num ? value.toDouble() : double.tryParse('$value') ?? 0;
