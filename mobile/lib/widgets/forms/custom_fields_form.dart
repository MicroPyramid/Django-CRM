import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/custom_field_definition.dart';
import '../../providers/lookup_provider.dart';
import '../../services/org_date.dart';
import '../common/common.dart';

/// Schema-driven custom-fields editor.
///
/// Loads the per-org `CustomFieldDefinition` rows for the given `targetModel`
/// (or renders the [definitions] it is handed) with one input per definition.
/// The current value map is held by the parent; we only call `onChanged` so
/// the parent decides when to persist.
class CustomFieldsForm extends ConsumerWidget {
  final String? targetModel;
  final List<CustomFieldDefinition>? definitions;
  final Map<String, dynamic> values;
  final ValueChanged<Map<String, dynamic>> onChanged;

  /// A sentence to show under a field, keyed by field key.
  final Map<String, String> errors;

  const CustomFieldsForm({
    super.key,
    this.targetModel,
    this.definitions,
    required this.values,
    required this.onChanged,
    this.errors = const {},
  }) : assert(
         (targetModel == null) != (definitions == null),
         'Give exactly one of targetModel and definitions',
       );

  /// A cleared field stays in the map as null. The server keeps every key a
  /// save leaves out, so removing it would leave the old value in place.
  void _setValue(String key, dynamic value) {
    final next = Map<String, dynamic>.from(values);
    next[key] = (value is String && value.isEmpty) ? null : value;
    onChanged(next);
  }

  Widget _fields(List<CustomFieldDefinition> defs) {
    if (defs.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final def in defs) ...[
          _CustomFieldInput(
            definition: def,
            value: values[def.key],
            onChanged: (v) => _setValue(def.key, v),
          ),
          if (errors[def.key] ?? customFieldNumberError(def, values[def.key])
              case final error?) ...[
            const SizedBox(height: 4),
            Text(
              error,
              style: AppTypography.caption.copyWith(color: AppColors.danger600),
            ),
          ],
          const SizedBox(height: 16),
        ],
      ],
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final given = definitions;
    if (given != null) return _fields(given);
    final asyncDefs = ref.watch(customFieldDefinitionsProvider(targetModel!));

    return asyncDefs.when(
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 12),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      ),
      error: (err, _) => Text(
        'Failed to load custom fields',
        style: AppTypography.caption.copyWith(color: AppColors.danger500),
      ),
      data: _fields,
    );
  }
}

class _CustomFieldInput extends StatelessWidget {
  final CustomFieldDefinition definition;
  final dynamic value;
  final ValueChanged<dynamic> onChanged;

  const _CustomFieldInput({
    required this.definition,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    switch (definition.fieldType) {
      case CustomFieldType.text:
        return _textInput(maxLines: 1);
      case CustomFieldType.textarea:
        return _textInput(maxLines: 4);
      case CustomFieldType.number:
        return _numberInput();
      case CustomFieldType.dropdown:
        return _dropdownInput(context);
      case CustomFieldType.date:
        return _dateInput(context);
      case CustomFieldType.checkbox:
        return _checkboxInput();
    }
  }

  String _label() =>
      definition.isRequired ? '${definition.label} *' : definition.label;

  Widget _textInput({required int maxLines}) {
    return _TypedInput(
      label: _label(),
      value: value,
      maxLines: maxLines,
      onChanged: onChanged,
    );
  }

  Widget _numberInput() {
    return _TypedInput(
      label: _label(),
      value: value,
      number: true,
      onChanged: (v) {
        if (v.isEmpty) {
          onChanged(null);
          return;
        }
        final n = num.tryParse(v);
        onChanged(n ?? v);
      },
    );
  }

  Widget _dropdownInput(BuildContext context) {
    final selectedLabel = definition.options
        .where((o) => o.value == value?.toString())
        .map((o) => o.label)
        .firstOrNull;
    // A stored value that is no longer an option shows as itself; only the
    // user choosing something else changes it.
    final stored = value?.toString() ?? '';
    final shown = selectedLabel ?? (stored.isEmpty ? null : stored);
    return _DropdownField(
      label: _label(),
      valueLabel: shown ?? 'Select…',
      hasValue: shown != null,
      onTap: () => _showDropdownSheet(context),
    );
  }

  void _showDropdownSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              margin: const EdgeInsets.only(top: 12),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.gray300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(definition.label, style: AppTypography.h3),
            ),
            if (!definition.isRequired && value != null)
              InkWell(
                onTap: () {
                  onChanged(null);
                  Navigator.pop(context);
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 14,
                  ),
                  child: Row(
                    children: [
                      Icon(LucideIcons.x, size: 18, color: AppColors.gray500),
                      const SizedBox(width: 12),
                      Text(
                        'Clear',
                        style: AppTypography.body.copyWith(
                          color: AppColors.gray600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            for (final opt in definition.options)
              InkWell(
                onTap: () {
                  onChanged(opt.value);
                  Navigator.pop(context);
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 14,
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          opt.label,
                          style: AppTypography.body.copyWith(
                            fontWeight: opt.value == value?.toString()
                                ? FontWeight.w600
                                : FontWeight.normal,
                            color: opt.value == value?.toString()
                                ? AppColors.primary600
                                : AppColors.textPrimary,
                          ),
                        ),
                      ),
                      if (opt.value == value?.toString())
                        Icon(
                          LucideIcons.check,
                          size: 20,
                          color: AppColors.primary600,
                        ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _dateInput(BuildContext context) {
    DateTime? parsed;
    if (value is String && (value as String).isNotEmpty) {
      parsed = DateTime.tryParse(value as String);
    }
    final display = parsed == null
        ? 'Select date'
        : '${parsed.year.toString().padLeft(4, '0')}-'
              '${parsed.month.toString().padLeft(2, '0')}-'
              '${parsed.day.toString().padLeft(2, '0')}';
    return _DropdownField(
      label: _label(),
      valueLabel: display,
      hasValue: parsed != null,
      icon: LucideIcons.calendar,
      onTap: () async {
        final picked = await showDatePicker(
          context: context,
          initialDate: parsed ?? orgToday(),
          firstDate: DateTime(2000),
          lastDate: DateTime(2100),
        );
        if (picked != null) {
          final iso =
              '${picked.year.toString().padLeft(4, '0')}-'
              '${picked.month.toString().padLeft(2, '0')}-'
              '${picked.day.toString().padLeft(2, '0')}';
          onChanged(iso);
        }
      },
    );
  }

  Widget _checkboxInput() {
    final checked = value == true || value == 'true' || value == 1;
    return InkWell(
      onTap: () => onChanged(!checked),
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          children: [
            Checkbox(value: checked, onChanged: (v) => onChanged(v ?? false)),
            Expanded(child: Text(_label(), style: AppTypography.body)),
          ],
        ),
      ),
    );
  }
}

/// A text or number input that keeps one controller for its lifetime, so a
/// parent rebuilding on every keystroke does not reset the cursor. The value
/// from outside replaces the text only when it says something different, such
/// as a form cleared after a save.
class _TypedInput extends StatefulWidget {
  const _TypedInput({
    required this.label,
    required this.value,
    required this.onChanged,
    this.maxLines = 1,
    this.number = false,
  });

  final String label;
  final dynamic value;
  final ValueChanged<String> onChanged;
  final int maxLines;
  final bool number;

  @override
  State<_TypedInput> createState() => _TypedInputState();
}

class _TypedInputState extends State<_TypedInput> {
  late final TextEditingController _controller = TextEditingController(
    text: widget.value?.toString() ?? '',
  );

  bool _shows(dynamic value) {
    final text = _controller.text;
    if (value == null) return text.isEmpty;
    if (widget.number && value is num) return num.tryParse(text) == value;
    return text == value.toString();
  }

  @override
  void didUpdateWidget(_TypedInput oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!_shows(widget.value)) {
      _controller.text = widget.value?.toString() ?? '';
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FloatingLabelInput(
      label: widget.label,
      controller: _controller,
      maxLines: widget.maxLines,
      keyboardType: widget.number
          ? const TextInputType.numberWithOptions(decimal: true)
          : null,
      inputFormatters: widget.number
          ? [FilteringTextInputFormatter.allow(RegExp(r'[0-9.\-]'))]
          : null,
      onChanged: widget.onChanged,
    );
  }
}

class _DropdownField extends StatelessWidget {
  final String label;
  final String valueLabel;
  final bool hasValue;
  final IconData? icon;
  final VoidCallback onTap;

  const _DropdownField({
    required this.label,
    required this.valueLabel,
    required this.hasValue,
    required this.onTap,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: onTap,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            decoration: BoxDecoration(
              color: AppColors.gray50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              children: [
                if (icon != null) ...[
                  Icon(icon, size: 18, color: AppColors.textSecondary),
                  const SizedBox(width: 12),
                ],
                Expanded(
                  child: Text(
                    valueLabel,
                    style: AppTypography.body.copyWith(
                      color: hasValue
                          ? AppColors.textPrimary
                          : AppColors.textSecondary,
                    ),
                  ),
                ),
                Icon(
                  LucideIcons.chevronDown,
                  size: 20,
                  color: AppColors.textSecondary,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
