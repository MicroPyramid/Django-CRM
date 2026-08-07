import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import 'deal.dart' show Currency;

/// `invoices.models.ESTIMATE_STATUS`. Six values, no underscores this time.
enum EstimateStatus {
  draft('Draft', 'Draft', AppColors.gray500),
  sent('Sent', 'Sent', AppColors.primary600),
  viewed('Viewed', 'Viewed', AppColors.primary600),
  accepted('Accepted', 'Accepted', AppColors.success600),
  declined('Declined', 'Declined', AppColors.danger600),
  expired('Expired', 'Expired', AppColors.warning600);

  const EstimateStatus(this.value, this.label, this.color);

  final String value;
  final String label;
  final Color color;

  static EstimateStatus? fromString(String? raw) {
    if (raw == null) return null;
    for (final status in EstimateStatus.values) {
      if (status.value == raw) return status;
    }
    return null;
  }
}

/// A quote, from `EstimateListSerializer`.
///
/// `convertedToInvoiceNumber` is on the list row for a reason the serializer
/// spells out: the worklist exists to separate "accepted but not yet billed"
/// from "already billed". Without it the client would offer to raise a second
/// invoice for an estimate that already has one.
class Estimate {
  const Estimate({
    required this.id,
    this.estimateNumber = '',
    this.title = '',
    this.status,
    this.rawStatus = '',
    this.accountName,
    this.clientName = '',
    this.issueDate,
    this.expiryDate,
    this.totalAmount = 0,
    this.currency,
    this.isExpired = false,
    this.convertedInvoiceId,
    this.convertedInvoiceNumber,
    this.opportunityName,
  });

  final String id;
  final String estimateNumber;
  final String title;
  final EstimateStatus? status;
  final String rawStatus;
  final String? accountName;
  final String clientName;
  final DateTime? issueDate;
  final DateTime? expiryDate;
  final double totalAmount;
  final String? currency;
  final bool isExpired;

  final String? convertedInvoiceId;
  final String? convertedInvoiceNumber;
  final String? opportunityName;

  String get statusLabel => status?.label ?? rawStatus;

  Color get statusColor => status?.color ?? AppColors.gray500;

  Currency get currencyInfo => Currency.fromString(currency);

  bool get isConverted => convertedInvoiceId != null;

  /// Convert is refused once an invoice exists, and that is the only refusal
  /// `EstimateConvertView` makes. A declined estimate can still be converted,
  /// which is the server's rule and not this client's to tighten.
  bool get canConvert => !isConverted;

  /// Mirrors `EstimateSendView`, which refuses Accepted, Declined and Expired,
  /// and separately refuses anything already past its expiry date.
  ///
  /// `isExpired` is checked as well as the status for the reason the server
  /// checks both: `check_expired_estimates` relabels quotes once a day, so
  /// between the expiry date passing and that task running a lapsed quote
  /// still reads as Sent. Reading only the status would draw a Send button
  /// that answers 400.
  bool get canSend =>
      !isExpired &&
      (status == EstimateStatus.draft ||
          status == EstimateStatus.sent ||
          status == EstimateStatus.viewed);

  factory Estimate.fromJson(Map<String, dynamic> json) {
    final converted = json['converted_to_invoice'];
    final opportunity = json['opportunity'];
    return Estimate(
      id: json['id']?.toString() ?? '',
      estimateNumber: json['estimate_number']?.toString() ?? '',
      title: json['title'] as String? ?? '',
      status: EstimateStatus.fromString(json['status'] as String?),
      rawStatus: json['status']?.toString() ?? '',
      accountName: json['account_name'] as String?,
      clientName: json['client_name'] as String? ?? '',
      issueDate: _date(json['issue_date']),
      expiryDate: _date(json['expiry_date']),
      totalAmount: _num(json['total_amount']),
      currency: json['currency'] as String?,
      isExpired: json['is_expired'] as bool? ?? false,
      convertedInvoiceId: converted is Map<String, dynamic>
          ? converted['id']?.toString()
          : null,
      convertedInvoiceNumber: converted is Map<String, dynamic>
          ? converted['invoice_number'] as String?
          : null,
      opportunityName: opportunity is Map<String, dynamic>
          ? opportunity['name'] as String?
          : null,
    );
  }
}

double _num(dynamic value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}

/// A YYYY-MM-DD date as a local calendar date, never UTC midnight.
DateTime? _date(dynamic value) {
  final text = value?.toString().trim() ?? '';
  if (text.isEmpty || text == 'null') return null;
  if (RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(text)) {
    return DateTime.tryParse('${text}T00:00:00');
  }
  return DateTime.tryParse(text)?.toLocal();
}
