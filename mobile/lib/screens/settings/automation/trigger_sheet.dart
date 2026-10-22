import 'package:flutter/material.dart';

import '../../../core/theme/theme.dart';
import '../../../data/models/automation.dart';
import '../../../services/automation_text.dart';
import 'rule_sheet.dart';
import 'rule_value_field.dart';

/// Edits a rule's trigger. Returns the new trigger, or null when cancelled.
Future<TriggerDraft?> showTriggerSheet(
  BuildContext context, {
  required AutomationCatalogue catalogue,
  required AutomationObject object,
  required TriggerDraft draft,
}) => showRuleSheet<TriggerDraft>(
  context,
  (controller) => _TriggerSheet(
    catalogue: catalogue,
    object: object,
    draft: draft,
    controller: controller,
  ),
);

class _TriggerSheet extends StatefulWidget {
  const _TriggerSheet({
    required this.catalogue,
    required this.object,
    required this.draft,
    required this.controller,
  });

  final AutomationCatalogue catalogue;
  final AutomationObject object;
  final TriggerDraft draft;
  final ScrollController controller;

  @override
  State<_TriggerSheet> createState() => _TriggerSheetState();
}

class _TriggerSheetState extends State<_TriggerSheet> {
  late String _event;
  late String _field;
  late bool _onlyWhen;
  Object? _to;

  @override
  void initState() {
    super.initState();
    final d = widget.draft.copy();
    _event = d.event == 'created' ? 'created' : 'updated';
    _field = d.field ?? '';
    _to = d.to;
    _onlyWhen = d.to != null && d.to != '';
  }

  void _done() {
    final watching = _event == 'updated' && _field.isNotEmpty;
    Navigator.of(context).pop(
      TriggerDraft(
        event: _event,
        field: watching ? _field : null,
        to: watching && _onlyWhen ? _to : null,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final fields = withStored([
      for (final f in triggerFields(widget.object))
        RuleOption(value: f.key, label: f.label),
    ], _field);
    final field = fieldOf(widget.object, _field);
    final hint = _onlyWhen ? changeHint(field, _to) : null;
    return RuleSheetFrame(
      title: 'When',
      controller: widget.controller,
      onDone: _done,
      children: [
        Text(
          widget.object.label,
          style: AppTypography.label.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 8),
        SegmentedButton<String>(
          showSelectedIcon: false,
          segments: const [
            ButtonSegment(value: 'created', label: Text('is created')),
            ButtonSegment(value: 'updated', label: Text('is updated')),
          ],
          selected: {_event},
          onSelectionChanged: (s) => setState(() => _event = s.first),
        ),
        if (_event == 'updated') ...[
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            initialValue: _field,
            isExpanded: true,
            decoration: const InputDecoration(
              labelText: 'Field',
              border: OutlineInputBorder(),
            ),
            items: [
              const DropdownMenuItem(value: '', child: Text('Any field')),
              for (final o in fields)
                DropdownMenuItem(
                  value: o.value,
                  child: Text(o.label, overflow: TextOverflow.ellipsis),
                ),
            ],
            onChanged: (v) => setState(() {
              _field = v ?? '';
              _to = null;
            }),
          ),
          if (_field.isNotEmpty) ...[
            const SizedBox(height: 8),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Only when it changes to'),
              value: _onlyWhen,
              onChanged: (v) => setState(() => _onlyWhen = v),
            ),
            if (_onlyWhen && field != null)
              RuleValueField(
                key: ValueKey('to-$_field'),
                field: field,
                kind: valueKind(field, 'eq').name,
                value: _to,
                onChanged: (v) => setState(() => _to = v),
                people: widget.catalogue.people,
              )
            else if (_onlyWhen)
              Text(
                'This field is no longer available. Choose another.',
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            if (hint != null) ...[
              const SizedBox(height: 8),
              Text(
                hint,
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ],
        ],
      ],
    );
  }
}
