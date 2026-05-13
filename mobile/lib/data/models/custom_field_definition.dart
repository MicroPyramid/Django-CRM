/// Per-org schema row describing a single custom field on an entity.
///
/// Mirrors `common.models.CustomFieldDefinition` on the backend. The form
/// renderer uses `fieldType` to pick the input widget and `options` for
/// dropdown choices. Values live on the entity itself under `custom_fields`.
class CustomFieldDefinition {
  final String id;
  final String targetModel;
  final String key;
  final String label;
  final CustomFieldType fieldType;
  final List<CustomFieldOption> options;
  final bool isRequired;
  final int displayOrder;
  final bool isActive;

  const CustomFieldDefinition({
    required this.id,
    required this.targetModel,
    required this.key,
    required this.label,
    required this.fieldType,
    this.options = const [],
    this.isRequired = false,
    this.displayOrder = 0,
    this.isActive = true,
  });

  factory CustomFieldDefinition.fromJson(Map<String, dynamic> json) {
    final rawOptions = json['options'];
    final List<CustomFieldOption> parsedOptions = [];
    if (rawOptions is List) {
      for (final o in rawOptions) {
        if (o is Map<String, dynamic>) {
          final value = o['value']?.toString() ?? '';
          if (value.isEmpty) continue;
          parsedOptions.add(
            CustomFieldOption(
              value: value,
              label: o['label']?.toString() ?? value,
            ),
          );
        }
      }
    }
    return CustomFieldDefinition(
      id: json['id']?.toString() ?? '',
      targetModel: json['target_model'] as String? ?? '',
      key: json['key'] as String? ?? '',
      label: json['label'] as String? ?? '',
      fieldType: CustomFieldType.fromString(json['field_type'] as String?),
      options: parsedOptions,
      isRequired: json['is_required'] as bool? ?? false,
      displayOrder: json['display_order'] as int? ?? 0,
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}

class CustomFieldOption {
  final String value;
  final String label;
  const CustomFieldOption({required this.value, required this.label});
}

enum CustomFieldType {
  text('text'),
  textarea('textarea'),
  number('number'),
  dropdown('dropdown'),
  date('date'),
  checkbox('checkbox');

  final String value;
  const CustomFieldType(this.value);

  static CustomFieldType fromString(String? value) {
    return CustomFieldType.values.firstWhere(
      (t) => t.value == value,
      orElse: () => CustomFieldType.text,
    );
  }
}
