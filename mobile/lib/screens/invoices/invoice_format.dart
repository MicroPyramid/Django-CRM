import 'package:intl/intl.dart';

import '../../data/models/invoice.dart';

/// Formatting shared by the invoice list and the invoice detail.
///
/// Money on this app is per-record rather than per-org, so the symbol is always
/// passed in from the invoice being drawn. Nothing here reaches for an org
/// default: an invoice raised in euros stays in euros on a dollar org.

final _money = NumberFormat('#,##0.00');
final _wholeMoney = NumberFormat('#,##0');

/// An exact amount, for anything a person might reconcile against a bank line.
String money(double value, String symbol) => '$symbol${_money.format(value)}';

/// A shortened amount for header figures, where the magnitude is the point and
/// the cents are noise. An empty [symbol] is a deliberate caller choice, used
/// when the underlying sum spans more than one currency.
String compactMoney(double value, String symbol) {
  final absolute = value.abs();
  if (absolute >= 1000000) {
    return '$symbol${(value / 1000000).toStringAsFixed(1)}M';
  }
  if (absolute >= 1000) {
    return '$symbol${(value / 1000).toStringAsFixed(1)}k';
  }
  return '$symbol${_wholeMoney.format(value)}';
}

/// How late an invoice is, or how long is left.
///
/// Null on a settled or undated invoice rather than a placeholder, so the
/// caller can leave the slot out entirely. Once an invoice is paid or
/// cancelled its due date stops meaning anything, and "4d late" against a paid
/// invoice was on screen in v1.
String? ageLabel(Invoice invoice) {
  final days = invoice.daysLate;
  if (days == null) return null;
  if (days > 0) return '${days}d late';
  if (days == 0) return 'due today';
  return '${days.abs()}d left';
}

/// The status pill is the shared `StatusBadge`, drawn from
/// `invoice.statusLabel` and `invoice.statusColor`. There is no invoice-only
/// pill widget here on purpose: the app already had one badge and did not need
/// a second.
