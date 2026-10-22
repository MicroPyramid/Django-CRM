Map<String, dynamic> _map(dynamic v) =>
    v is Map ? Map<String, dynamic>.from(v) : <String, dynamic>{};

List<Map<String, dynamic>> _maps(dynamic v) => v is List
    ? [
        for (final e in v)
          if (e is Map) _map(e),
      ]
    : const [];

String _str(dynamic v, [String fallback = '']) => v?.toString() ?? fallback;

String _label(dynamic v, String fallback) {
  final s = _str(v);
  return s.isEmpty ? fallback : s;
}

int _int(dynamic v, int fallback) => v is int ? v : fallback;

DateTime? _date(dynamic v) => v is String ? DateTime.tryParse(v) : null;

List<String> _strings(dynamic v) => v is List
    ? [
        for (final e in v)
          if (e is String) e,
      ]
    : const [];

/// A deep copy of decoded JSON, so a draft never shares a list or map.
dynamic _clone(dynamic v) {
  if (v is Map) {
    return <String, dynamic>{
      for (final e in v.entries) e.key.toString(): _clone(e.value),
    };
  }
  if (v is List) return [for (final e in v) _clone(e)];
  return v;
}

class RulePerson {
  final String id;
  final String name;

  const RulePerson({required this.id, this.name = ''});

  factory RulePerson.fromJson(Map<String, dynamic> json) =>
      RulePerson(id: _str(json['id']), name: _str(json['name']));

  static RulePerson? maybe(dynamic v) =>
      v is Map ? RulePerson.fromJson(_map(v)) : null;
}

class RuleEndpoint {
  final String id;
  final String description;

  const RuleEndpoint({required this.id, this.description = ''});

  factory RuleEndpoint.fromJson(Map<String, dynamic> json) => RuleEndpoint(
    id: _str(json['id']),
    description: _str(json['description']),
  );
}

class RuleChoice {
  final String value;
  final String label;
  final String group;
  final bool settable;

  const RuleChoice({
    required this.value,
    required this.label,
    this.group = '',
    this.settable = true,
  });

  factory RuleChoice.fromJson(Map<String, dynamic> json) {
    final value = _str(json['value']);
    return RuleChoice(
      value: value,
      label: _label(json['label'], value),
      group: _str(json['group']),
      settable: json['settable'] as bool? ?? true,
    );
  }
}

class RuleField {
  final String key;
  final String label;
  final String type;
  final List<RuleChoice> choices;
  final bool settable;

  const RuleField({
    required this.key,
    required this.label,
    this.type = 'text',
    this.choices = const [],
    this.settable = true,
  });

  factory RuleField.fromJson(Map<String, dynamic> json) {
    final key = _str(json['key']);
    return RuleField(
      key: key,
      label: _label(json['label'], key),
      type: _str(json['type'], 'text'),
      choices: _maps(json['choices']).map(RuleChoice.fromJson).toList(),
      settable: json['settable'] as bool? ?? true,
    );
  }
}

class RuleLinkSpec {
  final String id;
  final String label;
  final String objectKey;

  const RuleLinkSpec({required this.id, this.label = '', this.objectKey = ''});

  factory RuleLinkSpec.fromJson(Map<String, dynamic> json) => RuleLinkSpec(
    id: _str(json['id']),
    label: _str(json['label']),
    objectKey: _str(json['object_key']),
  );
}

class RuleParent {
  final String key;
  final String label;

  const RuleParent({required this.key, this.label = ''});

  factory RuleParent.fromJson(Map<String, dynamic> json) =>
      RuleParent(key: _str(json['key']), label: _str(json['label']));
}

class AutomationObject {
  final String key;
  final String label;
  final String labelPlural;
  final List<RuleField> fields;
  final RuleParent? parent;
  final List<RuleLinkSpec> links;

  const AutomationObject({
    required this.key,
    required this.label,
    required this.labelPlural,
    this.fields = const [],
    this.parent,
    this.links = const [],
  });

  factory AutomationObject.fromJson(Map<String, dynamic> json) {
    final key = _str(json['key']);
    final label = _label(json['label'], key);
    return AutomationObject(
      key: key,
      label: label,
      labelPlural: _label(json['label_plural'], label),
      fields: _maps(json['fields']).map(RuleField.fromJson).toList(),
      parent: json['parent'] is Map
          ? RuleParent.fromJson(_map(json['parent']))
          : null,
      links: _maps(json['links']).map(RuleLinkSpec.fromJson).toList(),
    );
  }
}

/// The answer of `GET /api/automation/catalogue/`.
class AutomationCatalogue {
  final List<AutomationObject> objects;
  final Map<String, List<String>> operators;
  final List<String> updateOnlyOperators;
  final List<String> actions;
  final List<RulePerson> people;
  final List<RuleEndpoint> endpoints;
  final int maxConditions;
  final int maxActions;

  const AutomationCatalogue({
    this.objects = const [],
    this.operators = const {},
    this.updateOnlyOperators = const [],
    this.actions = const [],
    this.people = const [],
    this.endpoints = const [],
    this.maxConditions = 20,
    this.maxActions = 10,
  });

  factory AutomationCatalogue.fromJson(Map<String, dynamic> json) {
    final limits = _map(json['limits']);
    final operators = json['operators'];
    return AutomationCatalogue(
      objects: _maps(json['objects']).map(AutomationObject.fromJson).toList(),
      operators: operators is Map
          ? {
              for (final e in operators.entries)
                e.key.toString(): _strings(e.value),
            }
          : const {},
      updateOnlyOperators: _strings(json['update_only_operators']),
      actions: _strings(json['actions']),
      people: _maps(json['people']).map(RulePerson.fromJson).toList(),
      endpoints: _maps(json['endpoints']).map(RuleEndpoint.fromJson).toList(),
      maxConditions: _int(limits['conditions'], 20),
      maxActions: _int(limits['actions'], 10),
    );
  }
}

class TriggerDraft {
  String event;
  String? field;
  dynamic to;

  TriggerDraft({this.event = 'created', this.field, this.to});

  factory TriggerDraft.fromJson(dynamic json) {
    final m = _map(json);
    final field = m['field'];
    return TriggerDraft(
      event: _str(m['event'], 'created'),
      field: field is String ? field : null,
      to: _clone(m['to']),
    );
  }

  TriggerDraft copy() =>
      TriggerDraft(event: event, field: field, to: _clone(to));
}

class ConditionDraft {
  String field;
  String op;
  dynamic value;

  ConditionDraft({this.field = '', this.op = '', this.value});

  factory ConditionDraft.fromJson(Map<String, dynamic> json) => ConditionDraft(
    field: _str(json['field']),
    op: _str(json['op']),
    value: _clone(json['value']),
  );

  ConditionDraft copy() =>
      ConditionDraft(field: field, op: op, value: _clone(value));
}

class ActionDraft {
  String type;
  Map<String, dynamic> values;

  ActionDraft({this.type = '', Map<String, dynamic>? values})
    : values = values ?? <String, dynamic>{};

  factory ActionDraft.fromJson(Map<String, dynamic> json) => ActionDraft(
    type: _str(json['type']),
    values: {
      for (final e in json.entries)
        if (e.key != 'type') e.key: _clone(e.value),
    },
  );

  ActionDraft copy() =>
      ActionDraft(type: type, values: _clone(values) as Map<String, dynamic>);
}

class AutomationRule {
  final String id;
  final String name;
  final String objectKey;
  final TriggerDraft trigger;
  final String match;
  final List<ConditionDraft> conditions;
  final List<ActionDraft> actions;
  final bool isActive;
  final RulePerson? owner;
  final DateTime? switchedOnAt;
  final String pausedReason;

  const AutomationRule({
    required this.id,
    this.name = '',
    this.objectKey = '',
    required this.trigger,
    this.match = 'all',
    this.conditions = const [],
    this.actions = const [],
    this.isActive = false,
    this.owner,
    this.switchedOnAt,
    this.pausedReason = '',
  });

  factory AutomationRule.fromJson(Map<String, dynamic> json) => AutomationRule(
    id: _str(json['id']),
    name: _str(json['name']),
    objectKey: _str(json['object_key']),
    trigger: TriggerDraft.fromJson(json['trigger']),
    match: _str(json['match'], 'all'),
    conditions: _maps(json['conditions']).map(ConditionDraft.fromJson).toList(),
    actions: _maps(json['actions']).map(ActionDraft.fromJson).toList(),
    isActive: json['is_active'] == true,
    owner: RulePerson.maybe(json['owner']),
    switchedOnAt: _date(json['switched_on_at']),
    pausedReason: _str(json['paused_reason']),
  );
}

/// A rule as `GET rules/` lists it: the detail route carries no status.
class AutomationRuleRow extends AutomationRule {
  final String status;
  final String statusText;
  final int runs7d;
  final int failures7d;

  const AutomationRuleRow({
    required super.id,
    super.name,
    super.objectKey,
    required super.trigger,
    super.match,
    super.conditions,
    super.actions,
    super.isActive,
    super.owner,
    super.switchedOnAt,
    super.pausedReason,
    this.status = 'off',
    this.statusText = '',
    this.runs7d = 0,
    this.failures7d = 0,
  });

  factory AutomationRuleRow.fromJson(Map<String, dynamic> json) {
    final rule = AutomationRule.fromJson(json);
    return AutomationRuleRow(
      id: rule.id,
      name: rule.name,
      objectKey: rule.objectKey,
      trigger: rule.trigger,
      match: rule.match,
      conditions: rule.conditions,
      actions: rule.actions,
      isActive: rule.isActive,
      owner: rule.owner,
      switchedOnAt: rule.switchedOnAt,
      pausedReason: rule.pausedReason,
      status: _str(json['status'], 'off'),
      statusText: _str(json['status_text']),
      runs7d: _int(json['runs_7d'], 0),
      failures7d: _int(json['failures_7d'], 0),
    );
  }
}

class AutomationRulesAnswer {
  final String? summary;
  final List<AutomationRuleRow> rules;

  const AutomationRulesAnswer({this.summary, this.rules = const []});

  factory AutomationRulesAnswer.fromJson(Map<String, dynamic> json) =>
      AutomationRulesAnswer(
        summary: json['summary'] is String ? json['summary'] as String : null,
        rules: _maps(json['results']).map(AutomationRuleRow.fromJson).toList(),
      );
}

class RunStep {
  final int action;
  final String type;
  final String status;
  final String text;

  const RunStep({
    this.action = 0,
    this.type = '',
    this.status = '',
    this.text = '',
  });

  factory RunStep.fromJson(Map<String, dynamic> json) => RunStep(
    action: _int(json['action'], 0),
    type: _str(json['type']),
    status: _str(json['status']),
    text: _str(json['text']),
  );
}

class AutomationRun {
  final String id;
  final DateTime? createdAt;
  final String recordId;
  final String recordName;
  final String objectKey;
  final String status;
  final String reason;
  final List<RunStep> steps;
  final int skippedCount;
  final String? triggeredByRuleName;

  const AutomationRun({
    required this.id,
    this.createdAt,
    this.recordId = '',
    this.recordName = '',
    this.objectKey = '',
    this.status = '',
    this.reason = '',
    this.steps = const [],
    this.skippedCount = 0,
    this.triggeredByRuleName,
  });

  factory AutomationRun.fromJson(Map<String, dynamic> json) {
    final by = json['triggered_by'];
    final byName = by is Map ? _str(by['rule_name']) : '';
    return AutomationRun(
      id: _str(json['id']),
      createdAt: _date(json['created_at']),
      recordId: _str(json['record_id']),
      recordName: _str(json['record_name']),
      objectKey: _str(json['object_key']),
      status: _str(json['status']),
      reason: _str(json['reason']),
      steps: _maps(json['steps']).map(RunStep.fromJson).toList(),
      skippedCount: _int(json['skipped_count'], 0),
      triggeredByRuleName: byName.isEmpty ? null : byName,
    );
  }
}

class RunPage {
  final List<AutomationRun> runs;
  final int count;
  final int offset;

  const RunPage({this.runs = const [], this.count = 0, this.offset = 0});

  factory RunPage.fromJson(Map<String, dynamic> json, {int offset = 0}) {
    final runs = _maps(json['results']).map(AutomationRun.fromJson).toList();
    return RunPage(
      runs: runs,
      count: _int(json['count'], runs.length),
      offset: offset,
    );
  }
}

/// The editable form of a rule. Task 2's body builder turns it into JSON.
class RuleDraft {
  String name;
  String objectKey;
  TriggerDraft trigger;
  String match;
  List<ConditionDraft> conditions;
  List<ActionDraft> actions;

  RuleDraft({
    this.name = '',
    required this.objectKey,
    TriggerDraft? trigger,
    this.match = 'all',
    List<ConditionDraft>? conditions,
    List<ActionDraft>? actions,
  }) : trigger = trigger ?? TriggerDraft(),
       conditions = conditions ?? [],
       actions = actions ?? [];

  factory RuleDraft.blank(String objectKey) => RuleDraft(objectKey: objectKey);

  factory RuleDraft.from(AutomationRule rule) => RuleDraft(
    name: rule.name,
    objectKey: rule.objectKey,
    trigger: rule.trigger,
    match: rule.match,
    conditions: rule.conditions,
    actions: rule.actions,
  ).copy();

  RuleDraft copy() => RuleDraft(
    name: name,
    objectKey: objectKey,
    trigger: trigger.copy(),
    match: match,
    conditions: [for (final c in conditions) c.copy()],
    actions: [for (final a in actions) a.copy()],
  );
}
