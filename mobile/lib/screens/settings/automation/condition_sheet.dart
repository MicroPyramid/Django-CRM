import 'package:flutter/material.dart';

import '../../../core/theme/theme.dart';
import '../../../data/models/automation.dart';
import '../../../services/automation_text.dart';
import 'rule_sheet.dart';
import 'rule_value_field.dart';

/// Adds or edits one condition. Returns it, or null when cancelled.
Future<ConditionDraft?> showConditionSheet(
  BuildContext context, {
  required AutomationCatalogue catalogue,
  required AutomationObject object,
  required String event,
  ConditionDraft? draft,
}) => showRuleSheet<ConditionDraft>(
  context,
  (controller) => _ConditionSheet(
    catalogue: catalogue,
    object: object,
    event: event,
    draft: draft,
    controller: controller,
  ),
);

class _ConditionSheet extends StatefulWidget {
  const _ConditionSheet({
    required this.catalogue,
    required this.object,
    required this.event,
    required this.draft,
    required this.controller,
  });

  final AutomationCatalogue catalogue;
  final AutomationObject object;
  final String event;
  final ConditionDraft? draft;
  final ScrollController controller;

  @override
  State<_ConditionSheet> createState() => _ConditionSheetState();
}

class _ConditionSheetState extends State<_ConditionSheet> {
  late String _field;
  late String _op;
  Object? _value;

  @override
  void initState() {
    super.initState();
    final d = widget.draft?.copy() ?? ConditionDraft();
    _field = d.field;
    _op = d.op;
    _value = d.value;
  }

  RuleField? get _rule => fieldOf(widget.object, _field);

  List<String> _ops(RuleField? field) =>
      operatorsFor(widget.catalogue, field, widget.event);

  void _pickField(String key) => setState(() {
    _field = key;
    final ops = _ops(_rule);
    _op = ops.isEmpty ? '' : ops.first;
    _value = null;
  });

  void _pickOp(String op) => setState(() {
    final field = _rule;
    final kept =
        field != null &&
        valueKind(field, op) != ValueKind.none &&
        valueKind(field, op) == valueKind(field, _op);
    _op = op;
    if (!kept) _value = null;
  });

  void _done() {
    final field = _rule;
    final none = field != null && valueKind(field, _op) == ValueKind.none;
    Navigator.of(
      context,
    ).pop(ConditionDraft(field: _field, op: _op, value: none ? null : _value));
  }

  @override
  Widget build(BuildContext context) {
    final field = _rule;
    final fields = withStored([
      for (final f in widget.object.fields)
        RuleOption(value: f.key, label: f.label),
    ], _field);
    final ops = [
      for (final op in withStored([
        for (final op in _ops(field))
          RuleOption(value: op, label: operatorLabel(op, field?.type)),
      ], _op))
        op.gone
            ? RuleOption(
                value: op.value,
                label:
                    '${operatorLabel(op.value, field?.type)} '
                    '(no longer available)',
              )
            : op,
    ];
    final kind = field == null || _op.isEmpty ? null : valueKind(field, _op);
    return RuleSheetFrame(
      title: widget.draft == null ? 'Add condition' : 'Edit condition',
      controller: widget.controller,
      onDone: _field.isEmpty || _op.isEmpty ? null : _done,
      children: [
        DropdownButtonFormField<String>(
          initialValue: _field.isEmpty ? null : _field,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: 'Field',
            border: OutlineInputBorder(),
          ),
          items: [
            for (final o in fields)
              DropdownMenuItem(
                value: o.value,
                child: Text(o.label, overflow: TextOverflow.ellipsis),
              ),
          ],
          onChanged: (v) {
            if (v != null && v != _field) _pickField(v);
          },
        ),
        if (_field.isNotEmpty) ...[
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            key: ValueKey('op-$_field'),
            initialValue: _op.isEmpty ? null : _op,
            isExpanded: true,
            decoration: const InputDecoration(
              labelText: 'Operator',
              border: OutlineInputBorder(),
            ),
            items: [
              for (final o in ops)
                DropdownMenuItem(
                  value: o.value,
                  child: Text(o.label, overflow: TextOverflow.ellipsis),
                ),
            ],
            onChanged: (v) {
              if (v != null && v != _op) _pickOp(v);
            },
          ),
        ],
        if (field == null && _field.isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(
            'This field is no longer available. Choose another.',
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ] else if (field != null && kind != null && kind != ValueKind.none) ...[
          const SizedBox(height: 12),
          RuleValueField(
            key: ValueKey('value-$_field-${kind.name}'),
            field: field,
            kind: kind.name,
            value: _value,
            onChanged: (v) => setState(() => _value = v),
            people: widget.catalogue.people,
          ),
        ],
      ],
    );
  }
}
