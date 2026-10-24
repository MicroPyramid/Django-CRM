import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/theme/theme.dart';
import '../../data/models/custom_field_definition.dart';

/// A record's custom fields for reading, one row per definition. Every detail
/// screen uses this; the card around it is the screen's own.
///
/// Every active definition is listed, filled or not, as the web's detail pages
/// list them: a blank field the org decided to track is worth seeing.
class CustomFieldsDisplay extends StatelessWidget {
  const CustomFieldsDisplay({
    super.key,
    required this.definitions,
    required this.values,
  });

  final List<CustomFieldDefinition> definitions;
  final Map<String, dynamic> values;

  /// Whether a detail screen shows the block. Detail responses carry active
  /// definitions only, and a value whose field was turned off is hidden with
  /// the field, so the block follows the definitions.
  static bool shows(List<CustomFieldDefinition> definitions) =>
      definitions.isNotEmpty;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < definitions.length; i++) ...[
          if (i > 0) const Divider(height: 24),
          _row(definitions[i]),
        ],
      ],
    );
  }

  Widget _row(CustomFieldDefinition def) {
    final shown = customFieldDisplayValue(def, values[def.key]);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          def.label.toUpperCase(),
          style: AppTypography.overline.copyWith(
            color: AppColors.textTertiary,
            fontSize: 10,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          shown.isEmpty ? 'Not set' : shown,
          style: AppTypography.body.copyWith(
            color: shown.isEmpty ? AppColors.textTertiary : null,
          ),
        ),
      ],
    );
  }
}

/// One stored value as a reader sees it, or '' when there is none.
///
/// The server stores values already coerced (a number as a number, a checkbox
/// as a boolean, a date as YYYY-MM-DD), so this formats rather than parses.
/// Twin of `displayValue` in `frontend/src/lib/server/v2/record-fields.js`.
String customFieldDisplayValue(CustomFieldDefinition def, Object? raw) {
  if (raw == null || (raw is String && raw.trim().isEmpty)) return '';
  switch (def.fieldType) {
    case CustomFieldType.checkbox:
      return raw == true || raw == 'true' || raw == 1 ? 'Yes' : 'No';
    case CustomFieldType.number:
      return raw is num
          ? NumberFormat.decimalPattern().format(raw)
          : raw.toString();
    case CustomFieldType.dropdown:
      final value = raw.toString();
      return def.options
              .where((o) => o.value == value)
              .map((o) => o.label)
              .firstOrNull ??
          value;
    case CustomFieldType.date:
      final parsed = DateTime.tryParse(raw.toString());
      return parsed == null
          ? raw.toString()
          : DateFormat('MMM d, y').format(parsed);
    case CustomFieldType.text:
    case CustomFieldType.textarea:
      return raw.toString().trim();
  }
}
