import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/theme/theme.dart';
import '../../data/models/invoice.dart';
import 'invoice_format.dart';

/// What the sheet collected.
class PaymentEntry {
  const PaymentEntry({
    required this.amount,
    required this.method,
    this.reference = '',
  });

  /// Null means settle the whole outstanding balance, which is what the API
  /// does with an absent amount. Kept distinct from "the user typed the full
  /// balance" so a payment recorded seconds after another one still settles
  /// what is left rather than a number that has since gone stale.
  final double? amount;
  final String method;
  final String reference;
}

/// Records a payment against [invoice].
///
/// A bottom sheet rather than a dialog: it sits above the keyboard, which
/// matters because the one field here is numeric and the keyboard covers half
/// a phone. Returns null if dismissed.
Future<PaymentEntry?> showRecordPaymentSheet(
  BuildContext context,
  Invoice invoice,
) {
  return showModalBottomSheet<PaymentEntry>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _RecordPaymentSheet(invoice: invoice),
  );
}

class _RecordPaymentSheet extends StatefulWidget {
  const _RecordPaymentSheet({required this.invoice});

  final Invoice invoice;

  @override
  State<_RecordPaymentSheet> createState() => _RecordPaymentSheetState();
}

class _RecordPaymentSheetState extends State<_RecordPaymentSheet> {
  late final TextEditingController _amount;
  String _method = 'BANK_TRANSFER';
  final _reference = TextEditingController();
  String? _error;

  /// True while the amount box still holds exactly the balance it was seeded
  /// with, so an untouched sheet sends no amount at all and lets the server
  /// settle the real balance.
  bool _untouched = true;

  @override
  void initState() {
    super.initState();
    _amount = TextEditingController(
      text: widget.invoice.amountDue.toStringAsFixed(2),
    );
    _amount.addListener(() {
      if (_untouched) setState(() => _untouched = false);
    });
  }

  @override
  void dispose() {
    _amount.dispose();
    _reference.dispose();
    super.dispose();
  }

  /// Local validation is a courtesy so the user is not made to wait on a round
  /// trip to be told a blank box is blank. The server re-checks all of it:
  /// `PaymentCreateSerializer` rejects zero, negative, and anything above
  /// `amount_due`, and that is the check that counts.
  void _submit() {
    if (_untouched) {
      Navigator.of(context).pop(
        PaymentEntry(amount: null, method: _method, reference: _reference.text),
      );
      return;
    }

    final value = double.tryParse(_amount.text.trim());
    if (value == null) {
      setState(() => _error = 'Enter an amount');
      return;
    }
    if (value <= 0) {
      setState(() => _error = 'The amount has to be more than zero');
      return;
    }
    if (value > widget.invoice.amountDue) {
      setState(() {
        _error =
            'That is more than the '
            '${money(widget.invoice.amountDue, widget.invoice.currencyInfo.symbol)} '
            'still owed';
      });
      return;
    }
    Navigator.of(context).pop(
      PaymentEntry(amount: value, method: _method, reference: _reference.text),
    );
  }

  @override
  Widget build(BuildContext context) {
    final symbol = widget.invoice.currencyInfo.symbol;
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        // Lifts the sheet clear of the keyboard.
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Record a payment',
            style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          Text(
            '${money(widget.invoice.amountDue, symbol)} outstanding on '
            '${widget.invoice.invoiceNumber}',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _amount,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: [
              FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}')),
            ],
            decoration: InputDecoration(
              labelText: 'Amount',
              prefixText: symbol,
              border: const OutlineInputBorder(),
              errorText: _error,
            ),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _method,
            isExpanded: true,
            decoration: const InputDecoration(
              labelText: 'How it was paid',
              border: OutlineInputBorder(),
            ),
            items: [
              for (final entry in paymentMethods.entries)
                DropdownMenuItem(value: entry.key, child: Text(entry.value)),
            ],
            onChanged: (value) => setState(() => _method = value ?? _method),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _reference,
            decoration: const InputDecoration(
              labelText: 'Reference (optional)',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            height: 46,
            child: FilledButton(
              onPressed: _submit,
              child: const Text('Record payment'),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}
