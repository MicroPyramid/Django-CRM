import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/custom_field_definition.dart';

/// Add or edit a custom field definition.
///
/// Returns the request body to send, or `null` if the sheet was dismissed. It
/// returns a payload rather than a `CustomFieldDefinition` because create and
/// edit send genuinely different bodies: the edit body must not carry `key`,
/// `target_model` or `field_type`, and a model instance cannot express that
/// absence. See [customFieldCreatePayload] and [customFieldUpdatePayload].
///
/// Every rule checked here is also checked by
/// `CustomFieldDefinitionSerializer`. This is a courtesy so a hyphen in the key
/// is caught before a round trip, not a guard: the server's 400 still arrives
/// and is shown when it disagrees.
Future<Map<String, dynamic>?> showCustomFieldFormSheet(
  BuildContext context,
  CustomFieldDefinition? existing,
) {
  return showModalBottomSheet<Map<String, dynamic>>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _CustomFieldFormSheet(existing: existing),
  );
}

class _CustomFieldFormSheet extends StatefulWidget {
  const _CustomFieldFormSheet({this.existing});

  final CustomFieldDefinition? existing;

  @override
  State<_CustomFieldFormSheet> createState() => _CustomFieldFormSheetState();
}

class _CustomFieldFormSheetState extends State<_CustomFieldFormSheet> {
  late final TextEditingController _label;
  late final TextEditingController _key;
  late final TextEditingController _order;
  late String _targetModel;
  late CustomFieldType _fieldType;
  late bool _isRequired;
  late bool _isFilterable;

  /// Option rows for a dropdown. An existing row keeps its stored `value`
  /// untouched, because every record already holding that option refers to it;
  /// a row added here has an empty value and gets one slugified from its label
  /// at submit time.
  late List<_OptionDraft> _options;

  /// True once the admin edits the key by hand, after which the label stops
  /// writing into it. Without this, correcting the label would silently
  /// overwrite a key they had deliberately chosen.
  bool _keyTouched = false;

  String? _error;

  bool get _isCreate => widget.existing == null;

  @override
  void initState() {
    super.initState();
    final f = widget.existing;
    _label = TextEditingController(text: f?.label ?? '');
    _key = TextEditingController(text: f?.key ?? '');
    _order = TextEditingController(text: '${f?.displayOrder ?? 0}');
    _targetModel = f?.targetModel ?? customFieldTargets.keys.first;
    _fieldType = f?.fieldType ?? CustomFieldType.text;
    _isRequired = f?.isRequired ?? false;
    _isFilterable = f?.isFilterable ?? false;
    _options = [
      for (final o in f?.options ?? const <CustomFieldOption>[])
        _OptionDraft(value: o.value, label: o.label),
    ];
  }

  @override
  void dispose() {
    _label.dispose();
    _key.dispose();
    _order.dispose();
    for (final option in _options) {
      option.controller.dispose();
    }
    super.dispose();
  }

  void _onLabelChanged(String value) {
    if (!_isCreate || _keyTouched) return;
    final suggestion = suggestCustomFieldKey(value);
    if (suggestion == _key.text) return;
    _key.value = TextEditingValue(
      text: suggestion,
      selection: TextSelection.collapsed(offset: suggestion.length),
    );
  }

  void _addOption() {
    setState(() => _options.add(_OptionDraft(value: '', label: '')));
  }

  void _removeOption(int index) {
    setState(() => _options.removeAt(index).controller.dispose());
  }

  void _submit() {
    final options = [
      for (final o in _options)
        CustomFieldOption(value: o.value, label: o.controller.text),
    ];
    final problem = validateCustomFieldDraft(
      isCreate: _isCreate,
      label: _label.text,
      key: _key.text,
      targetModel: _targetModel,
      fieldType: _fieldType,
      options: options,
    );
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }

    final displayOrder = int.tryParse(_order.text.trim()) ?? 0;
    Navigator.of(context).pop(
      _isCreate
          ? customFieldCreatePayload(
              targetModel: _targetModel,
              key: _key.text,
              label: _label.text,
              fieldType: _fieldType,
              isRequired: _isRequired,
              isFilterable: _isFilterable,
              displayOrder: displayOrder,
              options: options,
            )
          : customFieldUpdatePayload(
              label: _label.text,
              fieldType: _fieldType,
              isRequired: _isRequired,
              isFilterable: _isFilterable,
              displayOrder: displayOrder,
              options: options,
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
              _isCreate ? 'New custom field' : 'Edit ${widget.existing!.label}',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _label,
              onChanged: _onLabelChanged,
              textCapitalization: TextCapitalization.sentences,
              maxLength: 128,
              decoration: const InputDecoration(
                labelText: 'Label',
                helperText: 'What the field is called on the record',
                border: OutlineInputBorder(),
                counterText: '',
              ),
            ),
            const SizedBox(height: 12),
            if (_isCreate)
              TextField(
                controller: _key,
                onChanged: (_) => _keyTouched = true,
                maxLength: 64,
                inputFormatters: [
                  FilteringTextInputFormatter.allow(RegExp(r'[a-z0-9_]')),
                ],
                decoration: const InputDecoration(
                  labelText: 'Key',
                  helperText:
                      'Lowercase letters, numbers and underscores. '
                      'Cannot be changed later.',
                  helperMaxLines: 2,
                  border: OutlineInputBorder(),
                  counterText: '',
                ),
              )
            else
              _Frozen(
                label: 'Key',
                value: widget.existing!.key,
                note:
                    'Fixed after creation. Every value already stored is filed '
                    'under this key, and changing it would leave them behind.',
              ),
            const SizedBox(height: 12),
            if (_isCreate)
              DropdownButtonFormField<String>(
                initialValue: _targetModel,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'On record type',
                  border: OutlineInputBorder(),
                ),
                items: [
                  for (final entry in customFieldTargets.entries)
                    DropdownMenuItem(
                      value: entry.key,
                      child: Text(entry.value),
                    ),
                ],
                onChanged: (v) =>
                    setState(() => _targetModel = v ?? _targetModel),
              )
            else
              _Frozen(
                label: 'On record type',
                value: customFieldTargetLabel(widget.existing!.targetModel),
                note: 'Fixed after creation.',
              ),
            const SizedBox(height: 12),
            if (_isCreate)
              DropdownButtonFormField<CustomFieldType>(
                initialValue: _fieldType,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Type',
                  border: OutlineInputBorder(),
                ),
                items: [
                  for (final type in CustomFieldType.values)
                    DropdownMenuItem(value: type, child: Text(type.label)),
                ],
                onChanged: (v) => setState(() => _fieldType = v ?? _fieldType),
              )
            else
              _Frozen(
                label: 'Type',
                value: widget.existing!.fieldType.label,
                note:
                    'Fixed after creation. Values already stored were written '
                    'as this type and a new one would reinterpret them.',
              ),
            if (_fieldType == CustomFieldType.dropdown) ...[
              const SizedBox(height: 16),
              _OptionsEditor(
                options: _options,
                onAdd: _addOption,
                onRemove: _removeOption,
              ),
            ],
            const SizedBox(height: 12),
            TextField(
              controller: _order,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              decoration: const InputDecoration(
                labelText: 'Position',
                helperText: 'Lower numbers come first on the record',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 4),
            // Material, not a bare Container: a SwitchListTile inside a
            // ColoredBox asserts in debug because its ink splash would be
            // painted over and never seen.
            Material(
              color: Colors.transparent,
              child: Column(
                children: [
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    value: _isRequired,
                    onChanged: (v) => setState(() => _isRequired = v),
                    title: const Text('Required'),
                    subtitle: const Text(
                      'Binds new saves only. Records saved before this keep '
                      'their gap.',
                    ),
                  ),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    value: _isFilterable,
                    onChanged: (v) => setState(() => _isFilterable = v),
                    title: const Text('Offer as a filter'),
                  ),
                ],
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(
                _error!,
                style: AppTypography.caption.copyWith(
                  color: AppColors.danger600,
                ),
              ),
            ],
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Cancel'),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: FilledButton(
                      onPressed: _submit,
                      child: Text(_isCreate ? 'Add field' : 'Save field'),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// One dropdown option being edited.
///
/// [value] is what records store. It is empty for a row added in this sheet
/// and is left exactly as it was for a row that came back from the server,
/// because relabelling an option must not move the records that hold it.
class _OptionDraft {
  _OptionDraft({required this.value, required String label})
    : controller = TextEditingController(text: label);

  final String value;
  final TextEditingController controller;
}

class _OptionsEditor extends StatelessWidget {
  const _OptionsEditor({
    required this.options,
    required this.onAdd,
    required this.onRemove,
  });

  final List<_OptionDraft> options;
  final VoidCallback onAdd;
  final void Function(int index) onRemove;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Options',
          style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 4),
        Text(
          'Renaming an option keeps the records that already use it.',
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 8),
        for (var i = 0; i < options.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: options[i].controller,
                    textCapitalization: TextCapitalization.sentences,
                    decoration: InputDecoration(
                      isDense: true,
                      hintText: 'Option ${i + 1}',
                      border: const OutlineInputBorder(),
                    ),
                  ),
                ),
                IconButton(
                  onPressed: () => onRemove(i),
                  tooltip: 'Remove option',
                  icon: Icon(
                    LucideIcons.x,
                    size: 18,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        SizedBox(
          height: 44,
          child: OutlinedButton.icon(
            onPressed: onAdd,
            icon: const Icon(LucideIcons.plus, size: 16),
            label: const Text('Add option'),
          ),
        ),
      ],
    );
  }
}

/// A value the server will not let change after creation, shown as text with
/// the reason. Offering the input and letting the save fail would teach the
/// rule the expensive way.
class _Frozen extends StatelessWidget {
  const _Frozen({required this.label, required this.value, required this.note});

  final String label;
  final String value;
  final String note;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 2),
        Text(value, style: AppTypography.body),
        const SizedBox(height: 2),
        Text(
          note,
          style: AppTypography.caption.copyWith(color: AppColors.textTertiary),
        ),
      ],
    );
  }
}
