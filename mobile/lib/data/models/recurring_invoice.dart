import 'deal.dart' show Currency;

/// `invoices.models.RECURRING_FREQUENCIES`, value to label.
const Map<String, String> recurringFrequencies = {
  'WEEKLY': 'Weekly',
  'BIWEEKLY': 'Every two weeks',
  'MONTHLY': 'Monthly',
  'QUARTERLY': 'Quarterly',
  'SEMI_ANNUALLY': 'Twice a year',
  'YEARLY': 'Yearly',
  'CUSTOM': 'Custom',
};

/// Whether a cadence says enough to bill on.
///
/// Mirrors `RecurringInvoiceCreateSerializer.validate`: a CUSTOM frequency
/// needs a positive interval, every other frequency carries its own. This is a
/// free function rather than form state because it is a rule about the API
/// contract, and a rule buried in a widget's private getter cannot be tested
/// without driving the whole form.
///
/// Zero is refused for the same reason the server refuses it: it is falsy in
/// `RecurringInvoice.calculate_next_date`, so it behaved exactly like a
/// missing interval and billed monthly.
bool cadenceIsComplete(String frequency, int? customDays) {
  if (frequency != 'CUSTOM') return true;
  return customDays != null && customDays >= 1;
}

/// A billing schedule, from `RecurringInvoiceListSerializer`.
class RecurringInvoice {
  const RecurringInvoice({
    required this.id,
    this.title = '',
    this.accountName,
    this.clientName = '',
    this.frequency = '',
    this.customDays,
    this.startDate,
    this.endDate,
    this.nextGenerationDate,
    this.isActive = true,
    this.autoSend = false,
    this.totalAmount = 0,
    this.currency,
    this.invoicesGenerated = 0,
  });

  final String id;
  final String title;
  final String? accountName;
  final String clientName;
  final String frequency;

  /// Null unless `frequency == 'CUSTOM'`, in which case it is the cadence.
  final int? customDays;

  final DateTime? startDate;
  final DateTime? endDate;
  final DateTime? nextGenerationDate;
  final bool isActive;

  /// Whether a generated invoice is emailed to the client without review.
  final bool autoSend;

  final double totalAmount;
  final String? currency;
  final int invoicesGenerated;

  Currency get currencyInfo => Currency.fromString(currency);

  /// "Every 10 days" for a custom cadence, the plain label otherwise. A CUSTOM
  /// schedule showing only the word "Custom" tells the reader nothing, and the
  /// interval is the one thing they came to check.
  String get frequencyLabel {
    if (frequency == 'CUSTOM' && customDays != null) {
      return 'Every $customDays days';
    }
    return recurringFrequencies[frequency] ?? frequency;
  }

  /// A paused schedule has no next run, whatever date is stored on it. The
  /// server keeps `next_generation_date` while `is_active` is false, so
  /// showing it unqualified would promise an invoice that is not coming.
  DateTime? get effectiveNextRun => isActive ? nextGenerationDate : null;

  factory RecurringInvoice.fromJson(Map<String, dynamic> json) {
    return RecurringInvoice(
      id: json['id']?.toString() ?? '',
      title: json['title'] as String? ?? '',
      accountName: json['account_name'] as String?,
      clientName: json['client_name'] as String? ?? '',
      frequency: json['frequency']?.toString() ?? '',
      customDays: json['custom_days'] as int?,
      startDate: _date(json['start_date']),
      endDate: _date(json['end_date']),
      nextGenerationDate: _date(json['next_generation_date']),
      isActive: json['is_active'] as bool? ?? true,
      autoSend: json['auto_send'] as bool? ?? false,
      totalAmount: _num(json['total_amount']),
      currency: json['currency'] as String?,
      invoicesGenerated: json['invoices_generated'] as int? ?? 0,
    );
  }
}

double _num(dynamic value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}

DateTime? _date(dynamic value) {
  final text = value?.toString().trim() ?? '';
  if (text.isEmpty || text == 'null') return null;
  if (RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(text)) {
    return DateTime.tryParse('${text}T00:00:00');
  }
  return DateTime.tryParse(text)?.toLocal();
}
