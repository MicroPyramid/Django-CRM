import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/theme/theme.dart';
import '../../data/models/deal.dart' show Currency;
import '../../data/models/product.dart';

/// Add or edit a catalogue product.
///
/// A bottom sheet because the form is four fields and a switch: pushing a
/// whole route for that is more navigation than the task deserves, and the
/// sheet keeps the list visible behind it.
///
/// Every rule checked here is also checked by `ProductCreateSerializer` and by
/// the model (`name` is required, `sku` is unique per org). This is a courtesy
/// so the user is not made to wait on a round trip for a blank name; the 400
/// still comes back and is shown when the server disagrees.
Future<Product?> showProductFormSheet(BuildContext context, Product? existing) {
  return showModalBottomSheet<Product>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _ProductFormSheet(existing: existing),
  );
}

class _ProductFormSheet extends StatefulWidget {
  const _ProductFormSheet({this.existing});

  final Product? existing;

  @override
  State<_ProductFormSheet> createState() => _ProductFormSheetState();
}

class _ProductFormSheetState extends State<_ProductFormSheet> {
  late final TextEditingController _name;
  late final TextEditingController _sku;
  late final TextEditingController _price;
  late final TextEditingController _category;
  late String _currency;
  late bool _isActive;
  String? _nameError;
  String? _priceError;

  @override
  void initState() {
    super.initState();
    final p = widget.existing;
    _name = TextEditingController(text: p?.name ?? '');
    _sku = TextEditingController(text: p?.sku ?? '');
    _price = TextEditingController(
      text: p == null ? '' : p.price.toStringAsFixed(2),
    );
    _category = TextEditingController(text: p?.category ?? '');
    _currency = p?.currency ?? Currency.usd.value;
    _isActive = p?.isActive ?? true;
  }

  @override
  void dispose() {
    _name.dispose();
    _sku.dispose();
    _price.dispose();
    _category.dispose();
    super.dispose();
  }

  void _submit() {
    final name = _name.text.trim();
    final price = double.tryParse(_price.text.trim());

    setState(() {
      _nameError = name.isEmpty ? 'A product needs a name' : null;
      // The model defaults price to 0 and does not forbid a negative one, but
      // a negative list price would put a negative line on an invoice, so it
      // is refused here and worth refusing on the serializer too.
      _priceError = price == null
          ? 'Enter a price'
          : price < 0
          ? 'A price cannot be negative'
          : null;
    });
    if (_nameError != null || _priceError != null) return;

    final trimmedSku = _sku.text.trim();
    final trimmedCategory = _category.text.trim();
    Navigator.of(context).pop(
      Product(
        id: widget.existing?.id ?? '',
        name: name,
        // Empty rather than absent would claim an empty SKU, and SKU is
        // unique per org: two products with '' would collide.
        sku: trimmedSku.isEmpty ? null : trimmedSku,
        price: price!,
        currency: _currency,
        category: trimmedCategory.isEmpty ? null : trimmedCategory,
        isActive: _isActive,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.existing == null ? 'New product' : 'Edit product',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _name,
              textCapitalization: TextCapitalization.sentences,
              decoration: InputDecoration(
                labelText: 'Name',
                border: const OutlineInputBorder(),
                errorText: _nameError,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  flex: 3,
                  child: TextField(
                    controller: _price,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    inputFormatters: [
                      FilteringTextInputFormatter.allow(
                        RegExp(r'^\d*\.?\d{0,2}'),
                      ),
                    ],
                    decoration: InputDecoration(
                      labelText: 'Price',
                      border: const OutlineInputBorder(),
                      errorText: _priceError,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 2,
                  child: DropdownButtonFormField<String>(
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
                    onChanged: (v) =>
                        setState(() => _currency = v ?? _currency),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _sku,
              decoration: const InputDecoration(
                labelText: 'SKU (optional)',
                helperText: 'Has to be unique across the catalogue',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _category,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Category (optional)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 4),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: _isActive,
              onChanged: (v) => setState(() => _isActive = v),
              title: const Text('Available for new invoices'),
              subtitle: const Text(
                'Turning this off keeps it off new line items. Invoices '
                'already billed are untouched.',
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 46,
              child: FilledButton(
                onPressed: _submit,
                child: Text(widget.existing == null ? 'Add product' : 'Save'),
              ),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}
