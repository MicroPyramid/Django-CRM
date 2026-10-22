import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../../data/models/automation.dart';
import '../../../services/automation_text.dart';
import '../../../services/org_date.dart';
import '../../../widgets/forms/multi_select_sheet.dart';

/// "Sales: Won" for a grouped option, else its label.
String optionLabel(RuleOption o) =>
    o.group.isEmpty ? o.label : '${o.group}: ${o.label}';

InputDecoration _decoration(String label) =>
    InputDecoration(labelText: label, border: const OutlineInputBorder());

/// One value of a condition, a trigger's "changes to" or a set field, drawn by
/// [kind] (a [ValueKind] name). A stored value the catalogue no longer offers
/// stays selectable and marked, so an untouched row sends what it holds.
class RuleValueField extends StatelessWidget {
  const RuleValueField({
    super.key,
    required this.field,
    required this.kind,
    required this.value,
    required this.onChanged,
    required this.people,
    this.settableOnly = false,
  });

  final RuleField field;
  final String kind;
  final Object? value;
  final ValueChanged<Object?> onChanged;
  final List<RulePerson> people;

  /// Offer only the options a rule may set.
  final bool settableOnly;

  List<RuleOption> get _choices => withStored([
    for (final c in field.choices)
      if (!settableOnly || c.settable) RuleOption.fromChoice(c),
  ], value);

  List<RuleOption> get _people => withStored(
    [
      for (final p in people)
        RuleOption(value: p.id, label: p.name.isEmpty ? p.id : p.name),
    ],
    value,
    person: true,
  );

  String? get _single {
    final v = value;
    if (v == null || v == '' || v is List) return null;
    return v.toString();
  }

  List<String> get _many => [
    if (value is List)
      for (final v in value as List)
        if (v != null) v.toString(),
  ];

  static String _numberText(Object? v) {
    if (v is double && v == v.truncateToDouble()) return v.toInt().toString();
    return v?.toString() ?? '';
  }

  @override
  Widget build(BuildContext context) {
    switch (kind) {
      case 'none':
        return const SizedBox.shrink();
      case 'number':
        return TextFormField(
          initialValue: _numberText(value),
          keyboardType: const TextInputType.numberWithOptions(
            decimal: true,
            signed: true,
          ),
          decoration: _decoration('Value'),
          // A number that does not parse goes as typed, so the server names
          // the row rather than the phone dropping it.
          onChanged: (t) {
            final text = t.trim();
            onChanged(text.isEmpty ? null : (num.tryParse(text) ?? text));
          },
        );
      case 'date':
        return _PickButton(
          icon: LucideIcons.calendar,
          text: _single ?? 'Choose a date',
          onPressed: () => _pickDate(context),
        );
      case 'choice':
        return _Select<String>(
          value: _single,
          items: [for (final o in _choices) (o.value, optionLabel(o))],
          onChanged: onChanged,
        );
      case 'person':
        return _Select<String>(
          value: _single,
          items: [for (final o in _people) (o.value, o.label)],
          onChanged: onChanged,
        );
      case 'boolean':
        final v = value;
        return _Select<bool>(
          value: v == true || v == 'true'
              ? true
              : (v == false || v == 'false' ? false : null),
          items: const [(true, 'Yes'), (false, 'No')],
          onChanged: onChanged,
        );
      case 'choices':
        return _pickMany(context, _choices, optionLabel);
      case 'people':
        return _pickMany(context, _people, (o) => o.label);
    }
    return TextFormField(
      initialValue: value?.toString() ?? '',
      decoration: _decoration('Value'),
      onChanged: (t) => onChanged(t.isEmpty ? null : t),
    );
  }

  Future<void> _pickDate(BuildContext context) async {
    final first = DateTime(1900);
    final last = DateTime(2100, 12, 31);
    // A stored date outside the bounds would fail the picker's assertion.
    var start = DateTime.tryParse(_single ?? '') ?? orgToday();
    if (start.isAfter(last)) start = last;
    if (start.isBefore(first)) start = first;
    final picked = await showDatePicker(
      context: context,
      initialDate: start,
      firstDate: first,
      lastDate: last,
    );
    if (picked != null) onChanged(DateFormat('yyyy-MM-dd').format(picked));
  }

  Widget _pickMany(
    BuildContext context,
    List<RuleOption> options,
    String Function(RuleOption) labelOf,
  ) {
    final chosen = _many;
    final selected = [
      for (final o in options)
        if (chosen.contains(o.value)) o,
    ];
    return _PickButton(
      icon: LucideIcons.listChecks,
      text: selected.isEmpty ? 'Choose' : selected.map(labelOf).join(', '),
      onPressed: () async {
        final picked = await MultiSelectSheet.show<RuleOption>(
          context: context,
          title: field.label,
          items: options,
          initialSelection: selected,
          labelOf: labelOf,
          searchText: labelOf,
        );
        if (picked == null) return;
        onChanged([
          for (final o in options)
            if (picked.contains(o)) o.value,
        ]);
      },
    );
  }
}

class _Select<T> extends StatelessWidget {
  const _Select({
    required this.value,
    required this.items,
    required this.onChanged,
  });

  final T? value;
  final List<(T, String)> items;
  final ValueChanged<Object?> onChanged;

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<T>(
    initialValue: value,
    isExpanded: true,
    decoration: _decoration('Value'),
    items: [
      for (final (v, label) in items)
        DropdownMenuItem<T>(
          value: v,
          child: Text(label, overflow: TextOverflow.ellipsis),
        ),
    ],
    onChanged: (v) => onChanged(v),
  );
}

class _PickButton extends StatelessWidget {
  const _PickButton({
    required this.icon,
    required this.text,
    required this.onPressed,
  });

  final IconData icon;
  final String text;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    style: OutlinedButton.styleFrom(
      minimumSize: const Size.fromHeight(48),
      alignment: Alignment.centerLeft,
    ),
    onPressed: onPressed,
    icon: Icon(icon, size: 18),
    label: Text(text),
  );
}
