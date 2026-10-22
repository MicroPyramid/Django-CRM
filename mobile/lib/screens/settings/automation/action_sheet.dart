import 'package:flutter/material.dart';

import '../../../core/theme/theme.dart';
import '../../../data/models/automation.dart';
import '../../../services/automation_text.dart';
import 'rule_sheet.dart';
import 'rule_value_field.dart';

const _typeLabels = {
  'set_field': 'Set a field',
  'assign': 'Assign',
  'create_task': 'Create a task',
  'notify': 'Notify',
  'webhook': 'Send to an endpoint',
};

const _nameHint = "{name} becomes the record's name.";
const _lostField = 'This field is no longer available. Choose another.';
const _priorities = ['Low', 'Medium', 'High'];

/// The "For" choice that names the record's parent, or null when the object
/// has no such choice (deal, ticket and task only).
String? taskParentLabel(AutomationObject? object) {
  for (final r in recipientsFor(object)) {
    if (r.value == 'parent_assignees') return r.label;
  }
  return null;
}

/// Adds or edits one action. Returns it, or null when cancelled.
Future<ActionDraft?> showActionSheet(
  BuildContext context, {
  required AutomationCatalogue catalogue,
  required AutomationObject object,
  ActionDraft? draft,
}) => showRuleSheet<ActionDraft>(
  context,
  (controller) => _ActionSheet(
    catalogue: catalogue,
    object: object,
    draft: draft,
    controller: controller,
  ),
);

class _ActionSheet extends StatefulWidget {
  const _ActionSheet({
    required this.catalogue,
    required this.object,
    required this.draft,
    required this.controller,
  });

  final AutomationCatalogue catalogue;
  final AutomationObject object;
  final ActionDraft? draft;
  final ScrollController controller;

  @override
  State<_ActionSheet> createState() => _ActionSheetState();
}

class _ActionSheetState extends State<_ActionSheet> {
  late ActionDraft _a;
  late bool _clear;

  /// What the value was before "Clear it instead" was ticked, so unticking
  /// brings it back.
  Object? _previous;

  Map<String, dynamic> get _v => _a.values;

  @override
  void initState() {
    super.initState();
    final types = actionTypes(widget.catalogue, widget.object);
    _a =
        widget.draft?.copy() ??
        blankAction(
          types.contains('create_task') ? 'create_task' : types.first,
        );
    _clear =
        _a.type == 'set_field' &&
        _v['value'] == null &&
        (_v['field'] ?? '').toString().isNotEmpty;
  }

  List<RuleTarget> get _targets => targetsFor(widget.catalogue, widget.object);

  RuleTarget? get _target {
    for (final t in _targets) {
      if (t.value == _v['target']) return t;
    }
    return null;
  }

  RuleField? get _setField =>
      fieldOf(_target?.object, (_v['field'] ?? '').toString());

  bool _empty(Object? v) => v == null || v == '' || (v is List && v.isEmpty);

  int _count(Object? v) => v is List ? v.length : 0;

  bool get _valid {
    switch (_a.type) {
      case 'set_field':
        if ((_v['field'] ?? '').toString().isEmpty || _target == null) {
          return false;
        }
        return _clear || !_empty(_v['value']);
      case 'assign':
        final n = _count(_v['people']);
        return _v['mode'] == 'rotate' ? n >= 2 && n <= 20 : n == 1;
      case 'create_task':
        final title = (_v['title'] ?? '').toString();
        final days = _v['due_in_days'];
        final daysOk =
            days == null || (days is int && days >= 0 && days <= 365);
        final personOk = _v['assign_to'] != 'person' || !_empty(_v['person']);
        return title.trim().isNotEmpty &&
            title.length <= 200 &&
            daysOk &&
            personOk;
      case 'notify':
        final message = (_v['message'] ?? '').toString();
        return (_count(_v['to']) + _count(_v['people']) > 0) &&
            message.trim().isNotEmpty &&
            message.length <= 500;
      case 'webhook':
        return !_empty(_v['endpoint']);
    }
    return false;
  }

  void _done() {
    final out = _a.copy();
    if (out.type == 'create_task' && out.values['assign_to'] != 'person') {
      out.values['person'] = null;
    }
    Navigator.of(context).pop(out);
  }

  void _pickType(String type) {
    if (type == _a.type) return;
    setState(() {
      _a = blankAction(type);
      _clear = false;
    });
  }

  Widget _select(
    String label,
    String? value,
    List<RuleOption> options,
    ValueChanged<String> onChanged, {
    Key? key,
  }) => DropdownButtonFormField<String>(
    key: key,
    initialValue: value == null || value.isEmpty ? null : value,
    isExpanded: true,
    decoration: InputDecoration(
      labelText: label,
      border: const OutlineInputBorder(),
    ),
    items: [
      for (final o in options)
        DropdownMenuItem(
          value: o.value,
          child: Text(optionLabel(o), overflow: TextOverflow.ellipsis),
        ),
    ],
    onChanged: (v) {
      if (v != null) onChanged(v);
    },
  );

  List<RuleOption> get _people => withStored([
    for (final p in widget.catalogue.people)
      RuleOption(value: p.id, label: p.name.isEmpty ? p.id : p.name),
  ], null);

  Widget _personSelect(String label, String? value, ValueChanged<String> on) {
    final options = withStored(_people, value, person: true);
    return _select(label, value, options, on, key: ValueKey('$label-$value'));
  }

  Widget _caption(String text) => Padding(
    padding: const EdgeInsets.only(bottom: 6),
    child: Text(
      text,
      style: AppTypography.label.copyWith(color: AppColors.textSecondary),
    ),
  );

  Widget _note(String text) => Padding(
    padding: const EdgeInsets.only(top: 6),
    child: Text(
      text,
      style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
    ),
  );

  Widget _peopleField(String label, Object? value, ValueChanged<Object?> on) =>
      RuleValueField(
        key: ValueKey('people-$label'),
        field: RuleField(key: 'people', label: label, type: 'people'),
        kind: ValueKind.people.name,
        value: value,
        onChanged: on,
        people: widget.catalogue.people,
      );

  List<Widget> _setFieldBody() {
    final target = _target;
    final targetOptions = withStored(
      [for (final t in _targets) RuleOption(value: t.value, label: t.label)],
      _v['target'],
      label: (_) => 'A removed link',
    );
    final fieldOptions = withStored([
      for (final f in target?.object.fields ?? const <RuleField>[])
        if (f.settable) RuleOption(value: f.key, label: f.label),
    ], _v['field']);
    final field = _setField;
    final stored = (_v['field'] ?? '').toString();
    return [
      _select('On', _v['target']?.toString(), targetOptions, (t) {
        if (t == _v['target']) return;
        setState(() {
          _v['target'] = t;
          _v['field'] = '';
          _v['value'] = null;
          _clear = false;
          _previous = null;
        });
      }),
      const SizedBox(height: 12),
      _select('Set', stored, fieldOptions, (f) {
        if (f == stored) return;
        setState(() {
          _v['field'] = f;
          _v['value'] = null;
          _clear = false;
          _previous = null;
        });
      }, key: ValueKey('set-${_v['target']}')),
      if (stored.isNotEmpty && field == null)
        _note(_lostField)
      else if (stored.isNotEmpty && field != null) ...[
        const SizedBox(height: 4),
        CheckboxListTile(
          contentPadding: EdgeInsets.zero,
          controlAffinity: ListTileControlAffinity.leading,
          title: const Text('Clear it instead'),
          value: _clear,
          onChanged: (on) => setState(() {
            _clear = on == true;
            if (_clear) {
              _previous = _v['value'];
              _v['value'] = null;
            } else {
              _v['value'] = _previous;
            }
          }),
        ),
        if (!_clear) ...[
          const SizedBox(height: 8),
          RuleValueField(
            key: ValueKey('value-${_v['target']}-$stored'),
            field: field,
            kind: valueKind(field, 'eq').name,
            value: _v['value'],
            settableOnly: true,
            onChanged: (v) => setState(() => _v['value'] = v),
            people: widget.catalogue.people,
          ),
        ],
      ],
    ];
  }

  List<Widget> _assignBody() {
    final rotate = _v['mode'] == 'rotate';
    final people = _v['people'] is List ? _v['people'] as List : const [];
    final modes = withStored(const [
      RuleOption(value: 'replace', label: 'One person'),
      RuleOption(value: 'rotate', label: 'In turn'),
    ], _v['mode']);
    return [
      _select('Who', _v['mode']?.toString(), modes, (m) {
        if (m == _v['mode']) return;
        setState(() {
          _v['mode'] = m;
          if (m == 'replace' && people.length > 1) {
            _v['people'] = [people.first];
          }
        });
      }),
      const SizedBox(height: 12),
      if (rotate) ...[
        _caption('People'),
        _peopleField(
          'People',
          _v['people'],
          (v) => setState(() => _v['people'] = v),
        ),
        _note('Choose 2 to 20 people; each new record goes to the next one.'),
      ] else ...[
        if (people.length > 1)
          _note('One person takes exactly one. Choose who stays.'),
        _personSelect(
          'Person',
          people.length == 1 ? people.first.toString() : null,
          (id) => setState(() => _v['people'] = [id]),
        ),
      ],
      _note('Replaces current assignees.'),
    ];
  }

  List<Widget> _taskBody() {
    final parent = taskParentLabel(widget.object);
    final forOptions = withStored(
      [
        const RuleOption(value: 'record', label: 'Its assignees'),
        if (parent != null) RuleOption(value: 'parent', label: parent),
        const RuleOption(value: 'owner', label: "The rule's owner"),
        const RuleOption(value: 'person', label: 'A chosen person'),
      ],
      _v['assign_to'],
      label: recipientLabel,
    );
    final days = _v['due_in_days'];
    return [
      TextFormField(
        initialValue: (_v['title'] ?? '').toString(),
        maxLength: 200,
        decoration: const InputDecoration(
          labelText: 'Title',
          helperText: _nameHint,
          border: OutlineInputBorder(),
        ),
        onChanged: (t) => setState(() => _v['title'] = t),
      ),
      const SizedBox(height: 12),
      TextFormField(
        initialValue: days?.toString() ?? '',
        keyboardType: TextInputType.number,
        decoration: const InputDecoration(
          labelText: 'Due in',
          suffixText: 'days',
          helperText: 'From 0 to 365. Leave empty for no due date.',
          border: OutlineInputBorder(),
        ),
        onChanged: (t) => setState(() {
          final text = t.trim();
          _v['due_in_days'] = text.isEmpty
              ? null
              : (int.tryParse(text) ?? text);
        }),
      ),
      const SizedBox(height: 12),
      _select(
        'Priority',
        _v['priority']?.toString(),
        withStored([
          for (final p in _priorities) RuleOption(value: p, label: p),
        ], _v['priority']),
        (p) => setState(() => _v['priority'] = p),
      ),
      const SizedBox(height: 12),
      _select(
        'For',
        _v['assign_to']?.toString(),
        forOptions,
        (w) => setState(() {
          _v['assign_to'] = w;
          if (w != 'person') _v['person'] = null;
        }),
      ),
      if (_v['assign_to'] == 'person') ...[
        const SizedBox(height: 12),
        _personSelect(
          'Person',
          _v['person']?.toString(),
          (id) => setState(() => _v['person'] = id),
        ),
      ],
    ];
  }

  List<Widget> _notifyBody() {
    final to = _v['to'] is List ? [..._v['to'] as List] : <dynamic>[];
    final options = withStored(
      recipientsFor(widget.object),
      to,
      label: recipientLabel,
    );
    return [
      _caption('Who'),
      for (final o in options)
        CheckboxListTile(
          contentPadding: EdgeInsets.zero,
          controlAffinity: ListTileControlAffinity.leading,
          title: Text(o.label),
          value: to.contains(o.value),
          onChanged: (on) => setState(() {
            _v['to'] = [
              for (final x in options)
                if (x.value == o.value ? on == true : to.contains(x.value))
                  x.value,
            ];
          }),
        ),
      const SizedBox(height: 8),
      _caption('And these people'),
      _peopleField(
        'And these people',
        _v['people'],
        (v) => setState(() => _v['people'] = v),
      ),
      const SizedBox(height: 12),
      TextFormField(
        initialValue: (_v['message'] ?? '').toString(),
        maxLength: 500,
        minLines: 3,
        maxLines: 6,
        decoration: const InputDecoration(
          labelText: 'Message',
          helperText: _nameHint,
          border: OutlineInputBorder(),
        ),
        onChanged: (t) => setState(() => _v['message'] = t),
      ),
      _note('In the app and by email, to active members only.'),
    ];
  }

  List<Widget> _webhookBody() => [
    _select(
      'Endpoint',
      _v['endpoint']?.toString(),
      withStored(
        [
          for (final e in widget.catalogue.endpoints)
            RuleOption(
              value: e.id,
              label: e.description.isEmpty ? e.id : e.description,
            ),
        ],
        _v['endpoint'],
        label: (_) => 'An endpoint no longer available',
      ),
      (id) => setState(() => _v['endpoint'] = id),
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final types = [
      for (final o in withStored([
        for (final t in actionTypes(widget.catalogue, widget.object))
          RuleOption(value: t, label: _typeLabels[t] ?? t),
      ], _a.type))
        o.gone
            ? RuleOption(
                value: o.value,
                label:
                    '${_typeLabels[o.value] ?? o.value} (no longer available)',
              )
            : o,
    ];
    final body = switch (_a.type) {
      'set_field' => _setFieldBody(),
      'assign' => _assignBody(),
      'create_task' => _taskBody(),
      'notify' => _notifyBody(),
      'webhook' => _webhookBody(),
      _ => <Widget>[_note('This action is no longer available.')],
    };
    return RuleSheetFrame(
      title: widget.draft == null ? 'Add action' : 'Edit action',
      controller: widget.controller,
      onDone: _valid ? _done : null,
      children: [
        _select('Action', _a.type, types, _pickType),
        const SizedBox(height: 12),
        KeyedSubtree(
          key: ValueKey('action-body-${_a.type}'),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: body,
          ),
        ),
      ],
    );
  }
}
