import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/deal.dart' show Currency;
import '../../data/models/lookup_models.dart';
import '../../providers/auth_provider.dart';
import '../../providers/invoices_provider.dart';
import '../../providers/lookup_provider.dart';
import '../../routes/app_router.dart';
import 'invoice_format.dart';
import 'line_item_sheet.dart';

/// Raise an invoice.
///
/// The densest form in the web app, rebuilt for a 390px column. The web puts
/// the builder and a live preview side by side; there is no room for two
/// columns here, so the running total sits in a bar pinned above the keyboard
/// and the line items are cards you tap to edit rather than a grid of inputs.
///
/// Only what `InvoiceCreateSerializer` accepts is sent. `status` is read-only
/// server-side (a new invoice is always Draft), and the number, public token,
/// org, creator and every total are the server's to derive, so none appear
/// here. The one field the API requires that is easy to miss is
/// `invoice_title`: `Invoice.invoice_title` is not blank, so the form blocks
/// submit until it has one.
class NewInvoiceScreen extends ConsumerStatefulWidget {
  const NewInvoiceScreen({super.key});

  @override
  ConsumerState<NewInvoiceScreen> createState() => _NewInvoiceScreenState();
}

class _NewInvoiceScreenState extends ConsumerState<NewInvoiceScreen> {
  final _title = TextEditingController();
  final _notes = TextEditingController();

  String? _accountId;
  String? _contactId;
  late String _currency;
  DateTime _issueDate = DateTime.now();
  String _paymentTerms = 'NET_30';
  DateTime? _customDueDate;

  final List<LineItemDraft> _items = [];
  bool _saving = false;
  String? _error;

  /// `invoices.models.PAYMENT_TERMS`.
  static const _terms = {
    'DUE_ON_RECEIPT': 'Due on receipt',
    'NET_15': 'Net 15',
    'NET_30': 'Net 30',
    'NET_45': 'Net 45',
    'NET_60': 'Net 60',
    'CUSTOM': 'Pick a date',
  };

  @override
  void initState() {
    super.initState();
    _currency =
        ref.read(selectedOrgProvider)?.defaultCurrency ?? Currency.usd.value;
  }

  @override
  void dispose() {
    _title.dispose();
    _notes.dispose();
    super.dispose();
  }

  String get _symbol => Currency.fromString(_currency).symbol;

  /// `quantity x unit_price` summed, matching `InvoiceLineItem`. Shown as a
  /// guide only: the server recomputes every total on save and its figure is
  /// the one that ends up on the invoice.
  double get _subtotal =>
      _items.fold(0, (sum, item) => sum + item.quantity * item.unitPrice);

  /// Lines with nothing on them are dropped rather than rejected, so a half
  /// typed row does not block the save.
  List<LineItemDraft> get _usableItems =>
      _items.where((i) => i.name.trim().isNotEmpty && i.quantity > 0).toList();

  bool get _ready =>
      _accountId != null &&
      _contactId != null &&
      _title.text.trim().isNotEmpty &&
      _usableItems.isNotEmpty &&
      !_saving;

  @override
  Widget build(BuildContext context) {
    final accounts = ref.watch(accountsLookupProvider);
    final contacts = ref.watch(contactsLookupProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('New invoice'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.only(bottom: 24),
              children: [
                if (_error != null)
                  Container(
                    width: double.infinity,
                    color: AppColors.danger50,
                    padding: const EdgeInsets.all(12),
                    child: Text(
                      _error!,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.danger700,
                      ),
                    ),
                  ),
                _whoAndWhen(accounts, contacts),
                _lineItems(),
                _extras(),
              ],
            ),
          ),
          _totalBar(),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------------
  // Who and when
  // -------------------------------------------------------------------------

  Widget _whoAndWhen(
    AsyncValue<List<AccountLookup>> accounts,
    AsyncValue<List<ContactLookup>> contacts,
  ) {
    final options = _contactOptions(contacts.value ?? const []);

    return _card('Who and when', [
      DropdownButtonFormField<String>(
        initialValue: _accountId,
        isExpanded: true,
        decoration: const InputDecoration(
          labelText: 'Account',
          border: OutlineInputBorder(),
        ),
        items: [
          for (final a in accounts.value ?? const <AccountLookup>[])
            DropdownMenuItem(value: a.id, child: Text(a.name)),
        ],
        onChanged: (value) => setState(() {
          _accountId = value;
          // The chosen contact may not be billable for the new account, and
          // silently keeping it would submit a pairing the API refuses.
          if (_contactId != null) {
            final kept = (contacts.value ?? const <ContactLookup>[])
                .where((c) => c.id == _contactId)
                .firstOrNull;
            if (kept == null || !kept.billableFor(value)) _contactId = null;
          }
        }),
      ),
      const SizedBox(height: 12),
      DropdownButtonFormField<String>(
        initialValue: _contactId,
        isExpanded: true,
        decoration: InputDecoration(
          labelText: 'Bill to',
          border: const OutlineInputBorder(),
          helperText: _accountId == null ? 'Pick an account first' : null,
        ),
        items: [
          for (final c in options)
            DropdownMenuItem(
              value: c.id,
              child: Text(
                c.accountName == null
                    ? c.fullName
                    : '${c.fullName} · ${c.accountName}',
                overflow: TextOverflow.ellipsis,
              ),
            ),
        ],
        onChanged: _accountId == null
            ? null
            : (value) => setState(() => _contactId = value),
      ),
      const SizedBox(height: 12),
      TextField(
        controller: _title,
        textCapitalization: TextCapitalization.sentences,
        onChanged: (_) => setState(() {}),
        decoration: const InputDecoration(
          labelText: 'What it is for',
          hintText: 'March retainer',
          border: OutlineInputBorder(),
        ),
      ),
      const SizedBox(height: 12),
      Row(
        children: [
          Expanded(
            child: _dateField(
              label: 'Issued',
              value: _issueDate,
              onPick: (d) => setState(() => _issueDate = d),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: DropdownButtonFormField<String>(
              initialValue: _paymentTerms,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Terms',
                border: OutlineInputBorder(),
              ),
              items: [
                for (final entry in _terms.entries)
                  DropdownMenuItem(value: entry.key, child: Text(entry.value)),
              ],
              onChanged: (value) =>
                  setState(() => _paymentTerms = value ?? _paymentTerms),
            ),
          ),
        ],
      ),
      // Only for CUSTOM. On every other term the server derives the due date
      // from the issue date, so asking for it would invite a contradiction.
      if (_paymentTerms == 'CUSTOM') ...[
        const SizedBox(height: 12),
        _dateField(
          label: 'Due',
          value: _customDueDate,
          onPick: (d) => setState(() => _customDueDate = d),
        ),
      ],
    ]);
  }

  /// Contacts offerable for the chosen account.
  ///
  /// Mirrors `InvoiceCreateSerializer.validate`, which refuses only a contact
  /// carrying a *different* account: an unbound one attaches to anyone. That
  /// matters more than it looks, because the `account` FK on Contact is
  /// usually empty (the populated link is the `Account.contacts` M2M, which
  /// this rule does not consult). Filtering on strict equality would leave the
  /// picker all but empty.
  List<ContactLookup> _contactOptions(List<ContactLookup> all) {
    if (_accountId == null) return const [];
    return all.where((c) => c.billableFor(_accountId)).toList();
  }

  Widget _dateField({
    required String label,
    required DateTime? value,
    required ValueChanged<DateTime> onPick,
  }) {
    return InkWell(
      onTap: () async {
        final picked = await showDatePicker(
          context: context,
          initialDate: value ?? DateTime.now(),
          firstDate: DateTime(2000),
          lastDate: DateTime(2100),
        );
        if (picked != null) onPick(picked);
      },
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
        ),
        child: Text(
          value == null
              ? 'Pick a date'
              : DateFormat('d MMM yyyy').format(value),
          style: AppTypography.body.copyWith(
            color: value == null
                ? AppColors.textSecondary
                : AppColors.textPrimary,
          ),
        ),
      ),
    );
  }

  // -------------------------------------------------------------------------
  // Line items
  // -------------------------------------------------------------------------

  Widget _lineItems() {
    return _card('What you are billing', [
      if (_items.isEmpty)
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(
            'An invoice needs at least one line.',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ),
      for (var i = 0; i < _items.length; i++) _lineRow(i),
      const SizedBox(height: 4),
      SizedBox(
        width: double.infinity,
        height: 44,
        child: OutlinedButton.icon(
          onPressed: () => _editLine(null),
          icon: const Icon(LucideIcons.plus, size: 16),
          label: const Text('Add a line'),
        ),
      ),
    ]);
  }

  Widget _lineRow(int index) {
    final item = _items[index];
    return InkWell(
      onTap: () => _editLine(index),
      child: Container(
        decoration: BoxDecoration(
          border: Border(bottom: BorderSide(color: AppColors.gray200)),
        ),
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.name.isEmpty ? 'Untitled line' : item.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${item.quantityLabel} x ${money(item.unitPrice, _symbol)}',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text(
              money(item.quantity * item.unitPrice, _symbol),
              style: AppTypography.caption.copyWith(
                color: AppColors.textPrimary,
              ),
            ),
            IconButton(
              icon: const Icon(LucideIcons.x, size: 16),
              tooltip: 'Remove this line',
              constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
              onPressed: () => setState(() => _items.removeAt(index)),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _editLine(int? index) async {
    final result = await showLineItemSheet(
      context,
      existing: index == null ? null : _items[index],
      symbol: _symbol,
    );
    if (result == null || !mounted) return;
    setState(() {
      if (index == null) {
        _items.add(result);
      } else {
        _items[index] = result;
      }
    });
  }

  // -------------------------------------------------------------------------
  // Extras
  // -------------------------------------------------------------------------

  Widget _extras() {
    return _card('Anything else', [
      DropdownButtonFormField<String>(
        initialValue: _currency,
        isExpanded: true,
        decoration: const InputDecoration(
          labelText: 'Currency',
          border: OutlineInputBorder(),
        ),
        items: [
          for (final c in Currency.values)
            DropdownMenuItem(value: c.value, child: Text(c.label)),
        ],
        onChanged: (value) => setState(() => _currency = value ?? _currency),
      ),
      const SizedBox(height: 12),
      TextField(
        controller: _notes,
        maxLines: 3,
        textCapitalization: TextCapitalization.sentences,
        decoration: const InputDecoration(
          labelText: 'Notes for the client (optional)',
          border: OutlineInputBorder(),
        ),
      ),
    ]);
  }

  // -------------------------------------------------------------------------
  // The pinned total and submit
  // -------------------------------------------------------------------------

  Widget _totalBar() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.gray200)),
      ),
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 10,
        bottom: MediaQuery.of(context).viewInsets.bottom + 10,
      ),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    money(_subtotal, _symbol),
                    style: AppTypography.h3.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  Text(
                    // Said plainly rather than labelled "Total": tax, discount
                    // and shipping are applied server-side and are not on this
                    // form, so this figure can be lower than the invoice.
                    'before any tax or discount',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              height: 46,
              child: FilledButton(
                onPressed: _ready ? _submit : null,
                child: _saving
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Create draft'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    setState(() {
      _saving = true;
      _error = null;
    });

    final payload = <String, dynamic>{
      'account_id': _accountId,
      'contact_id': _contactId,
      'invoice_title': _title.text.trim(),
      'currency': _currency,
      'issue_date': DateFormat('yyyy-MM-dd').format(_issueDate),
      'payment_terms': _paymentTerms,
      'line_items': [
        for (var i = 0; i < _usableItems.length; i++)
          _usableItems[i].toPayload(order: i),
      ],
      if (_paymentTerms == 'CUSTOM' && _customDueDate != null)
        'due_date': DateFormat('yyyy-MM-dd').format(_customDueDate!),
      if (_notes.text.trim().isNotEmpty) 'notes': _notes.text.trim(),
    };

    final result = await ref
        .read(invoicesProvider.notifier)
        .createInvoice(payload);
    if (!mounted) return;
    setState(() => _saving = false);

    if (result.error != null) {
      setState(() => _error = result.error);
      return;
    }
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Draft invoice created')));
    final id = result.invoiceId;
    if (id != null && id.isNotEmpty) {
      // Replace rather than push: going back to a form that has already been
      // submitted invites a second identical invoice.
      context.pushReplacement('${AppRoutes.invoices}/$id');
    } else {
      context.pop();
    }
  }

  Widget _card(String title, List<Widget> children) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }
}
