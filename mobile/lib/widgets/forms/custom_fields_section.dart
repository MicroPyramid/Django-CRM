import 'package:flutter/material.dart';

import '../../core/theme/theme.dart';
import '../../data/models/custom_field_definition.dart';
import 'custom_fields_form.dart';

/// The custom fields of one form: an optional "Custom fields" heading over
/// [CustomFieldsForm], empty when the org has none. Once a save has flagged a
/// field, each edit re-checks them all, so the sentences clear as they are
/// fixed. The parent keeps both maps and runs [customFieldProblems] on submit.
class CustomFieldsSection extends StatelessWidget {
  const CustomFieldsSection({
    super.key,
    required this.definitions,
    required this.values,
    required this.errors,
    required this.onChanged,
    this.heading = true,
  });

  final List<CustomFieldDefinition> definitions;
  final Map<String, dynamic> values;
  final Map<String, String> errors;
  final void Function(Map<String, dynamic> values, Map<String, String> errors)
  onChanged;
  final bool heading;

  @override
  Widget build(BuildContext context) {
    if (definitions.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (heading) ...[
          const SizedBox(height: 8),
          Text(
            'Custom fields',
            style: AppTypography.label.copyWith(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 8),
        ],
        CustomFieldsForm(
          definitions: definitions,
          values: values,
          errors: errors,
          onChanged: (next) => onChanged(
            next,
            errors.isEmpty ? errors : customFieldProblems(definitions, next),
          ),
        ),
      ],
    );
  }
}
