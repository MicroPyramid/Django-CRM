import 'package:flutter/material.dart';

import '../../core/theme/theme.dart';
import '../../data/models/custom_field_definition.dart';
import '../../widgets/forms/custom_fields_section.dart';

/// Edits an invoice's custom fields on their own, the twin of the web detail
/// page's "Edit fields" form. Resolves to the values to save, or null when
/// the sheet is dismissed.
Future<Map<String, dynamic>?> showInvoiceFieldsSheet(
  BuildContext context, {
  required List<CustomFieldDefinition> definitions,
  required Map<String, dynamic> values,
}) {
  return showModalBottomSheet<Map<String, dynamic>>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) =>
        _InvoiceFieldsSheet(definitions: definitions, values: values),
  );
}

class _InvoiceFieldsSheet extends StatefulWidget {
  const _InvoiceFieldsSheet({required this.definitions, required this.values});

  final List<CustomFieldDefinition> definitions;
  final Map<String, dynamic> values;

  @override
  State<_InvoiceFieldsSheet> createState() => _InvoiceFieldsSheetState();
}

class _InvoiceFieldsSheetState extends State<_InvoiceFieldsSheet> {
  late Map<String, dynamic> _values = Map<String, dynamic>.from(widget.values);
  Map<String, String> _errors = const {};

  void _save() {
    final missing = customFieldProblems(widget.definitions, _values);
    if (missing.isNotEmpty) {
      setState(() => _errors = missing);
      return;
    }
    Navigator.of(
      context,
    ).pop(sendableCustomFields(widget.definitions, _values));
  }

  @override
  Widget build(BuildContext context) {
    final media = MediaQuery.of(context);
    return Padding(
      padding: EdgeInsets.only(bottom: media.viewInsets.bottom),
      child: SafeArea(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxHeight: media.size.height * 0.85),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                child: Text('Edit fields', style: AppTypography.h3),
              ),
              Flexible(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                  child: CustomFieldsSection(
                    heading: false,
                    definitions: widget.definitions,
                    values: _values,
                    errors: _errors,
                    onChanged: (next, errors) => setState(() {
                      _values = next;
                      _errors = errors;
                    }),
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                child: Row(
                  children: [
                    Expanded(
                      child: SizedBox(
                        height: 46,
                        child: OutlinedButton(
                          onPressed: () => Navigator.of(context).pop(),
                          child: const Text('Cancel'),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: SizedBox(
                        height: 46,
                        child: FilledButton(
                          onPressed: _save,
                          child: const Text('Save'),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
