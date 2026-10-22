import '../config/api_config.dart';
import '../data/models/automation.dart';
import '../routes/record_routes.dart';
import 'api_service.dart';

/// Labels, sentences, request bodies and error rows for the automation
/// builder. The twin of `frontend/src/lib/v2/automation.js`: same copy, and
/// the catalogue is the only source of labels.

const _gone = 'Someone no longer active';
const _goneField = 'a field that is no longer available';
const _planLimit =
    "This rule can't be switched on for this organization right now.";
const _notRunning = 'This rule is not running for this organization right now.';

enum ValueKind {
  none,
  text,
  number,
  date,
  choice,
  choices,
  boolean,
  person,
  people,
}

class RuleOption {
  final String value;
  final String label;
  final String group;
  final bool settable;
  final bool gone;

  const RuleOption({
    required this.value,
    required this.label,
    this.group = '',
    this.settable = true,
    this.gone = false,
  });

  factory RuleOption.fromChoice(RuleChoice c) => RuleOption(
    value: c.value,
    label: c.label,
    group: c.group,
    settable: c.settable,
  );
}

class RuleTarget {
  final String value;
  final String label;
  final AutomationObject object;

  const RuleTarget({
    required this.value,
    required this.label,
    required this.object,
  });
}

AutomationObject? objectOf(AutomationCatalogue catalogue, String key) {
  for (final o in catalogue.objects) {
    if (o.key == key) return o;
  }
  return null;
}

RuleField? fieldOf(AutomationObject? object, String key) {
  for (final f in object?.fields ?? const <RuleField>[]) {
    if (f.key == key) return f;
  }
  return null;
}

/// Every field a trigger can watch: all but `people`.
List<RuleField> triggerFields(AutomationObject? object) => [
  for (final f in object?.fields ?? const <RuleField>[])
    if (f.type != 'people') f,
];

List<String> operatorsFor(
  AutomationCatalogue catalogue,
  RuleField? field,
  String event,
) {
  if (field == null) return const [];
  final base = catalogue.operators[field.type] ?? const <String>[];
  if (event == 'updated' && field.type != 'people') {
    return [...base, ...catalogue.updateOnlyOperators];
  }
  return [...base];
}

const _operatorLabels = {
  'eq': 'is',
  'neq': 'is not',
  'contains': 'contains',
  'not_contains': 'does not contain',
  'gt': 'is more than',
  'lt': 'is less than',
  'in': 'is any of',
  'not_in': 'is none of',
  'true': 'is true',
  'false': 'is false',
  'includes': 'includes',
  'excludes': 'does not include',
  'empty': 'is empty',
  'not_empty': 'is not empty',
  'was': 'was',
  'was_not': 'was not',
};

String operatorLabel(String op, [String? fieldType]) {
  if (fieldType == 'date' && op == 'gt') return 'is after';
  if (fieldType == 'date' && op == 'lt') return 'is before';
  if (fieldType == 'people' && op == 'eq') return 'is exactly';
  return _operatorLabels[op] ?? op;
}

ValueKind valueKind(RuleField field, String op) {
  if (_noValueOps.contains(op)) {
    return ValueKind.none;
  }
  if (op == 'in' || op == 'not_in') return ValueKind.choices;
  if (field.type == 'people') {
    return op == 'eq' ? ValueKind.people : ValueKind.person;
  }
  if ((op == 'was' || op == 'was_not') && field.type == 'boolean') {
    return ValueKind.boolean;
  }
  return switch (field.type) {
    'number' => ValueKind.number,
    'date' => ValueKind.date,
    'choice' => ValueKind.choice,
    'boolean' => ValueKind.boolean,
    'person' => ValueKind.person,
    _ => ValueKind.text,
  };
}

ActionDraft blankAction(String type) {
  switch (type) {
    case 'create_task':
      return ActionDraft(
        type: type,
        values: {
          'title': '',
          'due_in_days': 2,
          'priority': 'Medium',
          'assign_to': 'record',
          'person': null,
        },
      );
    case 'notify':
      return ActionDraft(
        type: type,
        values: {'to': <String>[], 'people': <String>[], 'message': ''},
      );
    case 'set_field':
      return ActionDraft(
        type: type,
        values: {'target': 'record', 'field': '', 'value': null},
      );
    case 'assign':
      return ActionDraft(
        type: type,
        values: {'mode': 'replace', 'people': <String>[]},
      );
    case 'webhook':
      return ActionDraft(type: type, values: {'endpoint': ''});
  }
  return ActionDraft(type: type);
}

List<String> actionTypes(
  AutomationCatalogue catalogue,
  AutomationObject? object,
) {
  final assignees = fieldOf(object, 'assigned_to');
  final canAssign =
      assignees != null && assignees.type == 'people' && assignees.settable;
  final canHook =
      !(object?.key ?? '').startsWith('obj:') && catalogue.endpoints.isNotEmpty;
  return [
    for (final a in catalogue.actions)
      if ((a != 'assign' || canAssign) && (a != 'webhook' || canHook)) a,
  ];
}

String _lowerFirst(String s) =>
    s.isEmpty ? s : s[0].toLowerCase() + s.substring(1);

/// Where `set_field` can write: the record, its parent, then each link.
List<RuleTarget> targetsFor(
  AutomationCatalogue catalogue,
  AutomationObject? object,
) {
  if (object == null) return const [];
  AutomationObject stand(String key, String label) =>
      objectOf(catalogue, key) ??
      AutomationObject(key: key, label: label, labelPlural: label);
  final parent = object.parent;
  return [
    RuleTarget(
      value: 'record',
      label: 'This ${object.label.toLowerCase()}',
      object: object,
    ),
    if (parent != null)
      RuleTarget(
        value: 'parent',
        label: 'Its ${parent.label.toLowerCase()}',
        object: stand(parent.key, parent.label),
      ),
    for (final link in object.links)
      RuleTarget(
        value: link.id,
        label: link.label,
        object: stand(link.objectKey, link.label),
      ),
  ];
}

List<RuleOption> recipientsFor(AutomationObject? object) {
  final parent = object?.parent;
  return [
    const RuleOption(value: 'record_assignees', label: 'Its assignees'),
    const RuleOption(value: 'record_creator', label: 'Who created it'),
    if (object?.key == 'task')
      const RuleOption(
        value: 'parent_assignees',
        label: "Its parent's assignees",
      )
    else if ((object?.key == 'deal' || object?.key == 'ticket') &&
        parent != null)
      RuleOption(
        value: 'parent_assignees',
        label: "The ${parent.label.toLowerCase()}'s assignees",
      ),
    const RuleOption(value: 'admins', label: 'All admins'),
    for (final link in object?.links ?? const <RuleLinkSpec>[])
      RuleOption(
        value: 'linked:${link.id}',
        label: 'Assignees of ${link.label}',
      ),
  ];
}

/// How a recipient or task audience the object no longer offers reads.
String recipientLabel(String value) {
  if (value.startsWith('linked:')) return 'Assignees of a removed link';
  return switch (value) {
    'record_assignees' || 'record' => 'Its assignees',
    'record_creator' => 'Who created it',
    'parent_assignees' ||
    'parent' => "Its parent's assignees (no longer available)",
    'admins' => 'All admins',
    'owner' => "The rule's owner",
    'person' => 'A chosen person',
    _ => '$value (no longer available)',
  };
}

/// Options plus any stored value they no longer carry, so editing a rule never
/// silently drops what it holds. [stored] is one value, a list, or empty;
/// [label] says how a lost value reads.
List<RuleOption> withStored(
  List<RuleOption> options,
  dynamic stored, {
  bool person = false,
  String Function(String value)? label,
}) {
  final out = [...options];
  final seen = {for (final o in options) o.value};
  final values = stored is List ? stored : [stored];
  for (final raw in values) {
    if (raw == null || raw == '') continue;
    final value = raw.toString();
    if (!seen.add(value)) continue;
    out.add(
      RuleOption(
        value: value,
        label:
            label?.call(value) ??
            (person ? _gone : '$value (no longer available)'),
        settable: false,
        gone: true,
      ),
    );
  }
  return out;
}

String _personName(AutomationCatalogue c, dynamic id) {
  for (final p in c.people) {
    if (p.id == id) return p.name.isEmpty ? _gone : p.name;
  }
  return _gone;
}

String _scalar(AutomationCatalogue c, RuleField? field, dynamic v) {
  switch (field?.type) {
    case 'boolean':
      return v == true || v == 'true' ? 'Yes' : 'No';
    case 'choice':
      for (final ch in field!.choices) {
        if (ch.value == v.toString()) return ch.label;
      }
      return '$v (no longer available)';
    case 'person':
    case 'people':
      return _personName(c, v);
  }
  if (v is double && v == v.truncateToDouble()) return v.toInt().toString();
  return v.toString();
}

String _valueText(AutomationCatalogue c, RuleField? field, dynamic v) {
  if (v == null) return '';
  if (v is List) return v.map((e) => _scalar(c, field, e)).join(', ');
  return _scalar(c, field, v);
}

String triggerSentence(AutomationRule rule, AutomationCatalogue catalogue) {
  final trigger = rule.trigger;
  if (trigger.event == 'created') return 'Created';
  final key = trigger.field;
  if (key == null || key.isEmpty) return 'Updated';
  final field = fieldOf(objectOf(catalogue, rule.objectKey), key);
  if (field == null) return 'A field that is no longer available changes';
  final base = '${field.label} changes';
  if (trigger.to == null) return base;
  return '$base to ${_valueText(catalogue, field, trigger.to)}';
}

/// The note under a "changes to" value, or null until there is one.
String? changeHint(RuleField? field, Object? to) {
  if (field == null || to == null || to == '') return null;
  var value = to.toString();
  if (field.type == 'boolean') {
    value = to == true || to == 'true' ? 'Yes' : 'No';
  }
  if (field.type == 'choice') {
    for (final c in field.choices) {
      if (c.value == value) {
        value = c.label;
        break;
      }
    }
  }
  return 'Runs once, when the ${field.label.toLowerCase()} moves into '
      '$value; later edits do not run it again.';
}

String conditionSentence(
  ConditionDraft condition,
  AutomationObject? object,
  AutomationCatalogue catalogue,
) {
  final field = fieldOf(object, condition.field);
  final label = field?.label ?? 'A field that is no longer available';
  final op = operatorLabel(condition.op, field?.type);
  final none = const [
    'empty',
    'not_empty',
    'true',
    'false',
  ].contains(condition.op);
  final value = none ? '' : _valueText(catalogue, field, condition.value);
  return value.isEmpty ? '$label $op' : '$label $op $value';
}

String _names(AutomationCatalogue c, dynamic ids) => [
  if (ids is List)
    for (final id in ids) _personName(c, id),
].join(', ');

String actionSentence(
  ActionDraft action,
  AutomationObject? object,
  AutomationCatalogue catalogue,
) {
  final v = action.values;
  switch (action.type) {
    case 'create_task':
      final title = (v['title'] ?? '').toString();
      return title.isEmpty ? 'Create a task' : 'Create a task: $title';
    case 'notify':
      final labels = {for (final r in recipientsFor(object)) r.value: r.label};
      final parts = [
        if (v['to'] is List)
          for (final to in v['to'] as List)
            _lowerFirst(labels[to] ?? recipientLabel(to.toString())),
        if (v['people'] is List && (v['people'] as List).isNotEmpty) ...[
          for (final id in v['people'] as List) _personName(catalogue, id),
        ],
      ];
      return parts.isEmpty ? 'Notify' : 'Notify ${parts.join(', ')}';
    case 'set_field':
      RuleTarget? target;
      for (final t in targetsFor(catalogue, object)) {
        if (t.value == v['target']) target = t;
      }
      final field = fieldOf(target?.object, (v['field'] ?? '').toString());
      final where = target == null
          ? 'a target that is no longer available'
          : target.value == 'record' || target.value == 'parent'
          ? _lowerFirst(target.label)
          : target.label;
      final name = field?.label ?? _goneField;
      if (v['value'] == null) return 'Clear $name on $where';
      return 'Set $name to ${_valueText(catalogue, field, v['value'])} on $where';
    case 'assign':
      final who = _names(catalogue, v['people']);
      if (who.isEmpty) return 'Assign';
      return v['mode'] == 'rotate'
          ? 'Assign in turn to $who'
          : 'Assign to $who';
    case 'webhook':
      for (final e in catalogue.endpoints) {
        if (e.id == v['endpoint']) {
          return e.description.isEmpty
              ? 'Send to an endpoint'
              : 'Send to ${e.description}';
        }
      }
      return 'Send to an endpoint that is no longer available';
  }
  return 'An action that is no longer available';
}

String runsLabel(AutomationRuleRow row) {
  if (row.runs7d == 0) return 'No runs';
  final text = '${row.runs7d} ${row.runs7d == 1 ? 'run' : 'runs'}';
  return row.failures7d > 0 ? '$text, ${row.failures7d} failed' : text;
}

/// A saved rule's status: its list row's, or else what the rule itself says,
/// as the web's `ruleStatus` reads it. Null for a rule not saved yet.
String? ruleStatus(AutomationRule? rule, AutomationRuleRow? row) {
  if (rule == null) return null;
  if (row != null && row.status.isNotEmpty) return row.status;
  if (rule.isActive) return 'on';
  return rule.pausedReason.isEmpty ? 'off' : 'paused';
}

String statusLabel(String status) => switch (status) {
  'on' => 'On',
  'paused' => 'Paused',
  'over_limit' => 'Not running',
  'needs_attention' => 'Needs attention',
  _ => 'Off',
};

/// The server's words for a paused or failing rule; the plan's own wording
/// never reaches the screen.
String? statusText(AutomationRuleRow row) {
  switch (row.status) {
    case 'over_limit':
      return _notRunning;
    case 'paused':
    case 'needs_attention':
      return row.statusText.isEmpty ? null : row.statusText;
  }
  return null;
}

const _noValueOps = ['empty', 'not_empty', 'true', 'false'];

const _actionKeys = {
  'set_field': ['target', 'field', 'value'],
  'assign': ['mode', 'people'],
  'create_task': ['title', 'due_in_days', 'priority', 'assign_to', 'person'],
  'notify': ['to', 'people', 'message'],
  'webhook': ['endpoint'],
};

Map<String, dynamic> ruleBody(
  RuleDraft draft, {
  required bool create,
  bool switchOn = false,
}) {
  final trigger = draft.trigger;
  final field = trigger.field;
  final watching =
      trigger.event == 'updated' && field != null && field.isNotEmpty;
  return {
    'name': draft.name,
    if (create) 'object_key': draft.objectKey,
    'match': draft.match,
    'trigger': {
      'event': trigger.event,
      if (watching) 'field': field,
      if (watching && trigger.to != null && trigger.to != '') 'to': trigger.to,
    },
    'conditions': [
      for (final c in draft.conditions)
        {
          'field': c.field,
          'op': c.op,
          'value': _noValueOps.contains(c.op) ? null : c.value,
        },
    ],
    'actions': [
      for (final a in draft.actions)
        {
          'type': a.type,
          for (final key in _actionKeys[a.type] ?? const <String>[])
            if (key == 'value' && a.type == 'set_field')
              key: a.values[key]
            else if (key == 'person' &&
                a.type == 'create_task' &&
                a.values['assign_to'] != 'person')
              key: null
            else if (a.values.containsKey(key))
              key: a.values[key],
        },
    ],
    if (switchOn) 'is_active': true,
  };
}

class RuleErrors {
  String? general;
  Map<String, String> rows;

  RuleErrors({this.general, Map<String, String>? rows}) : rows = rows ?? {};

  static final _row = RegExp(r'^(conditions|actions)\[(\d+)\]');

  static final _known = RegExp(
    r'^(name|match|trigger|conditions|actions|(conditions|actions)\.\d+)$',
  );

  static String _rowKey(String path) {
    final m = _row.firstMatch(path);
    if (m != null) return '${m[1]}.${m[2]}';
    if (path == 'trigger' || path.startsWith('trigger.')) return 'trigger';
    return path;
  }

  static RuleErrors fromResponse(ApiResponse r) {
    final body = r.data;
    final rows = <String, String>{};
    String? unmapped;
    if (r.statusCode == 400 && body is Map && body['errors'] is Map) {
      for (final e in (body['errors'] as Map).entries) {
        final m = e.value is List && (e.value as List).isNotEmpty
            ? (e.value as List).first
            : e.value;
        final key = _rowKey(e.key.toString());
        if (m is! String || m.isEmpty) continue;
        if (_known.hasMatch(key)) {
          rows.putIfAbsent(key, () => m);
        } else {
          unmapped ??= m;
        }
      }
      if (rows.isNotEmpty || unmapped != null) {
        return RuleErrors(general: unmapped, rows: rows);
      }
    }
    if (r.statusCode == 403 && body is Map && body['code'] == 'plan_limit') {
      return RuleErrors(general: _planLimit);
    }
    final message = r.message;
    return RuleErrors(
      general: message == null || message.isEmpty
          ? 'Could not save the rule.'
          : message,
    );
  }
}

/// The route to a run's record, or null. The id came from the server, so it
/// must be a UUID before it reaches the router.
String? recordPath(String objectKey, String id) =>
    ApiConfig.isUuid(id) ? linkedRecordRoute(objectKey, id) : null;
