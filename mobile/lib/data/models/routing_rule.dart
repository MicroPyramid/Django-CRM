/// Auto-routing rules: who a new ticket lands on.
///
/// **The order is the behaviour.** `cases.routing.evaluate` walks the active
/// rules by `priority_order`, runs the first match's strategy, and when that
/// rule sets `stop_processing` it skips every rule below. A list that does not
/// show the order shows a set of rules that look independent and are not.
library;

/// One `{field, op, value}` triple. AND across a rule's conditions; OR is
/// modeled by writing a second rule.
class RoutingCondition {
  const RoutingCondition({required this.field, this.op = 'eq', this.value});

  final String field;
  final String op;

  /// A `String` for every operator except `in`, which stores a list. Kept
  /// loose on purpose: the type is the whole trap. See [routingConditionValue].
  final dynamic value;

  factory RoutingCondition.fromJson(Map<String, dynamic> json) {
    return RoutingCondition(
      field: json['field']?.toString() ?? '',
      op: json['op']?.toString() ?? 'eq',
      value: json['value'],
    );
  }
}

/// A person or a team a rule can assign to, flattened from the full profile or
/// team object the API returns.
class RoutingTarget {
  const RoutingTarget({required this.id, this.name = '', this.isActive = true});

  final String id;
  final String name;

  /// Only meaningful for people. A rule pointing at a deactivated profile still
  /// looks configured and assigns nothing, so the row flags it.
  final bool isActive;

  factory RoutingTarget.person(Map<String, dynamic> json) {
    final details = json['user_details'];
    final name = details is Map ? details['name'] : null;
    final email = details is Map ? details['email'] : null;
    return RoutingTarget(
      id: json['id']?.toString() ?? '',
      name: (name as String?)?.trim().isNotEmpty == true
          ? name as String
          : (email as String?) ?? 'Unnamed',
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  factory RoutingTarget.team(Map<String, dynamic> json) => RoutingTarget(
    id: json['id']?.toString() ?? '',
    name: json['name'] as String? ?? '',
  );
}

class RoutingRule {
  const RoutingRule({
    required this.id,
    this.name = '',
    this.priorityOrder = 0,
    this.isActive = true,
    this.conditions = const [],
    this.strategy = strategyDirect,
    this.stopProcessing = false,
    this.targetAssignees = const [],
    this.targetTeam,
    this.matchedLast30d = 0,
    this.lastAssignedIndex,
  });

  static const String strategyDirect = 'direct';
  static const String strategyRoundRobin = 'round_robin';
  static const String strategyLeastBusy = 'least_busy';
  static const String strategyByTeam = 'by_team';

  final String id;
  final String name;

  /// Lower runs first, ties broken by creation time.
  final int priorityOrder;

  final bool isActive;
  final List<RoutingCondition> conditions;
  final String strategy;

  /// When this rule matches, no lower-priority rule is considered. Combined
  /// with an empty assignee pool this is how a rule silently swallows tickets,
  /// which is why the row says so.
  final bool stopProcessing;

  final List<RoutingTarget> targetAssignees;
  final RoutingTarget? targetTeam;

  /// From the ROUTED activity log, server-side. A rule that has matched nothing
  /// in thirty days is either dead or newly written, and only the admin knows
  /// which, so it is reported rather than judged.
  final int matchedLast30d;

  /// The round-robin cursor, so the row can name who is next in the rotation.
  /// Null for every other strategy, and for a rotation that has not run.
  final int? lastAssignedIndex;

  bool get routesToTeam => strategy == strategyByTeam;

  /// A rule that matches tickets and can assign none of them. Every branch here
  /// is a live failure: `cases/routing.py` sets `reason = "empty_pool"` and, if
  /// `stop_processing` is on, returns immediately, so the ticket is left
  /// unassigned AND no lower rule gets to try.
  bool get assignsNobody {
    if (!isActive) return false;
    if (routesToTeam) return targetTeam == null;
    return targetAssignees.where((p) => p.isActive).isEmpty;
  }

  /// The list the engine actually rotates over, which is not
  /// [targetAssignees].
  ///
  /// `cases.routing._active_pool` is
  /// `rule.target_assignees.filter(is_active=True).order_by("id")`. Indexing
  /// the cursor into the serializer's list instead can name a deactivated
  /// profile as the next assignee, which is the one answer that is certainly
  /// wrong. Sorting the id strings matches Postgres's uuid ordering: the
  /// canonical lowercase hex form compares the same lexically as by byte.
  List<RoutingTarget> get rotationPool =>
      targetAssignees.where((p) => p.isActive).toList()
        ..sort((a, b) => a.id.compareTo(b.id));

  /// Who the next round-robin ticket goes to, or null when that cannot be
  /// answered.
  ///
  /// **`last_assigned_index` is the NEXT index, not the last one**, despite its
  /// name: `_round_robin` reads `pool[state.last_assigned_index % len(pool)]`
  /// and only then stores `idx + 1`. Its own dry-run preview is
  /// `pool[(state.last_assigned_index if state else 0) % len(pool)]`, which is
  /// this, missing state included. Adding one skips a person.
  ///
  /// Only knowable for round robin. Least busy depends on live workload and
  /// direct and by team depend on nothing, so guessing would be worse than
  /// silence.
  RoutingTarget? get nextInRotation {
    if (strategy != strategyRoundRobin) return null;
    final pool = rotationPool;
    if (pool.isEmpty) return null;
    return pool[(lastAssignedIndex ?? 0) % pool.length];
  }

  factory RoutingRule.fromJson(Map<String, dynamic> json) {
    final conditions = json['conditions'];
    final assignees = json['target_assignees'];
    final team = json['target_team'];
    final state = json['state'];
    return RoutingRule(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      priorityOrder: json['priority_order'] as int? ?? 0,
      isActive: json['is_active'] as bool? ?? true,
      conditions: conditions is List
          ? [
              for (final c in conditions)
                if (c is Map<String, dynamic>) RoutingCondition.fromJson(c),
            ]
          : const [],
      strategy: json['strategy']?.toString() ?? strategyDirect,
      stopProcessing: json['stop_processing'] as bool? ?? false,
      targetAssignees: assignees is List
          ? [
              for (final p in assignees)
                if (p is Map<String, dynamic>) RoutingTarget.person(p),
            ]
          : const [],
      targetTeam: team is Map<String, dynamic>
          ? RoutingTarget.team(team)
          : null,
      matchedLast30d: json['matched_last_30d'] as int? ?? 0,
      lastAssignedIndex: state is Map
          ? state['last_assigned_index'] as int?
          : null,
    );
  }
}

/// `RoutingRule.STRATEGY_CHOICES`, in the words the rest of the app uses.
const Map<String, String> routingStrategyLabels = {
  RoutingRule.strategyDirect: 'Direct',
  RoutingRule.strategyRoundRobin: 'Round robin',
  RoutingRule.strategyLeastBusy: 'Least busy',
  RoutingRule.strategyByTeam: 'By team',
};

String routingStrategyLabel(String strategy) =>
    routingStrategyLabels[strategy] ?? strategy;

/// `RoutingRuleSerializer.SUPPORTED_FIELDS`, labelled.
const Map<String, String> routingConditionFields = {
  'priority': 'Priority',
  'case_type': 'Type',
  'account': 'Account',
  'tags': 'Tags',
  'from_email_domain': 'Sender domain',
  'mailbox_id': 'Mailbox',
};

/// `RoutingRuleSerializer.SUPPORTED_OPS`, labelled.
const Map<String, String> routingConditionOps = {
  'eq': 'is',
  'in': 'is one of',
  'contains': 'includes',
  'regex': 'matches',
};

String routingConditionFieldLabel(String field) {
  final known = routingConditionFields[field];
  if (known != null) return known;
  // A custom field is a supported target the label map cannot enumerate.
  if (field.startsWith('custom_fields.')) {
    return field.substring('custom_fields.'.length);
  }
  return field;
}

String routingConditionOpLabel(String op) => routingConditionOps[op] ?? op;

/// Whether the serializer would accept this field. Mirrors
/// `validate_conditions`: a known field, or anything under `custom_fields.`.
bool isSupportedConditionField(String field) =>
    routingConditionFields.containsKey(field) ||
    field.startsWith('custom_fields.');

/// A condition's value as one editable string. `in` stores a list, everything
/// else a string, and both have to come back as text the form can hold.
String routingConditionValue(RoutingCondition condition) {
  final value = condition.value;
  if (value is List) return value.map((v) => v.toString()).join(', ');
  return value?.toString() ?? '';
}

/// "Priority is one of High, Urgent", for the row.
String routingConditionSentence(RoutingCondition condition) {
  final value = routingConditionValue(condition);
  final label = routingConditionFieldLabel(condition.field);
  final op = routingConditionOpLabel(condition.op);
  return value.isEmpty ? '$label $op' : '$label $op $value';
}

/// What a rule matches, in one line. A rule with no conditions matches every
/// new ticket, which is the single most consequential thing a row can say.
String routingMatchSentence(RoutingRule rule) {
  if (rule.conditions.isEmpty) return 'Matches every new ticket';
  return rule.conditions.map(routingConditionSentence).join(' and ');
}

/// A condition as the form holds it: three strings, no type games.
class RoutingConditionDraft {
  RoutingConditionDraft({this.field = '', this.op = 'eq', this.value = ''});

  String field;
  String op;
  String value;

  factory RoutingConditionDraft.from(RoutingCondition condition) =>
      RoutingConditionDraft(
        field: condition.field,
        op: condition.op,
        value: routingConditionValue(condition),
      );

  bool get isBlank => field.trim().isEmpty;
}

/// Clean the form's condition rows into what the serializer validates.
///
/// A row left blank is dropped rather than rejected: an empty row is how the
/// editor says "I am about to type here", and failing the save over it would be
/// hostile.
///
/// **`in` gets a list, every other operator a string, and this is not
/// cosmetic.** `cases/routing.py` evaluates `in` with
/// `if not isinstance(value, (list, tuple)): return False`, and does it
/// silently: the unknown-field and unknown-op branches beside it both log,
/// this one does not. `validate_conditions` never checks the value's type, only
/// that the key is present, so a string here saves cleanly and then matches
/// nothing, forever, with nothing anywhere pointing at why.
///
/// `value` is always sent, empty list included, because the serializer rejects
/// a condition whose `value` key is missing.
List<Map<String, dynamic>> cleanRoutingConditions(
  List<RoutingConditionDraft> rows,
) {
  final cleaned = <Map<String, dynamic>>[];
  for (final row in rows) {
    final field = row.field.trim();
    if (field.isEmpty) continue;
    final op = row.op.trim().isEmpty ? 'eq' : row.op.trim();
    final dynamic value = op == 'in'
        ? row.value
              .split(',')
              .map((v) => v.trim())
              .where((v) => v.isNotEmpty)
              .toList()
        : row.value;
    cleaned.add({'field': field, 'op': op, 'value': value});
  }
  return cleaned;
}

/// The body for `POST /cases/routing-rules/` and its `PUT`.
///
/// Two omissions carry the weight:
///
/// **Only the half of the target in play is sent.** `by_team` routes to a team
/// and the other three route to people. The backend does not reject the half
/// that does not apply, it simply stores it, so a later strategy switch would
/// resurrect a stale target nobody chose.
///
/// **An empty assignee list omits the key rather than sending `[]`.** `[]`
/// disarms the backend's own guard: `RoutingRuleSerializer.validate` reads
/// `attrs.get("target_assignees")` and only raises when it is `None`, so a
/// create with nobody selected returns 201. With `stop_processing` on, routing
/// then hits `empty_pool` and returns, leaving every matching ticket unassigned
/// AND blocking every lower rule. Omitting the key lets the serializer answer
/// in its own words. On an edit that omission is only half the answer: see
/// [routingWriteProblem].
///
/// `target_team_id` clears with `null`. An empty string is a 400.
Map<String, dynamic> routingRulePayload({
  required String name,
  required int priorityOrder,
  required String strategy,
  required bool stopProcessing,
  required List<RoutingConditionDraft> conditions,
  required List<String> assigneeIds,
  required String? teamId,
  bool? isActive,
}) {
  final body = <String, dynamic>{
    'name': name.trim(),
    'priority_order': priorityOrder,
    'strategy': strategy,
    'stop_processing': stopProcessing,
    'conditions': cleanRoutingConditions(conditions),
  };
  if (isActive != null) body['is_active'] = isActive;

  if (strategy == RoutingRule.strategyByTeam) {
    final team = teamId?.trim() ?? '';
    body['target_team_id'] = team.isEmpty ? null : team;
  } else {
    final ids = assigneeIds.where((id) => id.trim().isNotEmpty).toList();
    if (ids.isNotEmpty) body['target_assignee_ids'] = ids;
  }
  return body;
}

/// What a routing write has to fix before it is worth sending, or `null`.
///
/// The empty-pool rule is asymmetric on purpose, because the backend's is.
/// `RoutingRuleSerializer.validate` guards a people strategy with no assignees
/// behind `self.instance is None`, so it never fires on a `PUT`, and
/// [routingRulePayload] has just dropped the empty list, which `partial=True`
/// reads as "leave the stored assignees alone". An admin who deselected
/// everyone would get a 200, a closed form, and their old list back, with
/// nothing saying the change was dropped. So on an edit this refuses locally;
/// on a create it stays quiet and lets the serializer's own message through.
String? routingWriteProblem({
  required bool isCreate,
  required String name,
  required String strategy,
  required List<String> assigneeIds,
  required String? teamId,
  required List<RoutingConditionDraft> conditions,
}) {
  if (name.trim().isEmpty) return 'A rule needs a name.';
  for (final row in conditions) {
    final field = row.field.trim();
    if (field.isEmpty) continue;
    if (!isSupportedConditionField(field)) {
      return '"$field" is not a field a rule can match on.';
    }
    if (!routingConditionOps.containsKey(row.op)) {
      return '"${row.op}" is not an operator a rule can use.';
    }
  }
  if (strategy == RoutingRule.strategyByTeam) {
    if ((teamId ?? '').trim().isEmpty) {
      return 'A by team rule needs a team to route to.';
    }
    return null;
  }
  final ids = assigneeIds.where((id) => id.trim().isNotEmpty);
  if (ids.isEmpty && !isCreate) {
    return 'A ${routingStrategyLabel(strategy).toLowerCase()} rule needs at '
        'least one assignee.';
  }
  return null;
}

/// The body for turning a rule back on.
///
/// Only `is_active`. Rebuilding the full payload from a row control that has no
/// name field would send `name: ''` and blank the rule's name, which is exactly
/// what the web's reactivate action had to be split out of `update` to avoid.
/// `put` is `partial=True`, so one key is a legal body.
Map<String, dynamic> routingActivatePayload() => {'is_active': true};

/// Deleting a routing rule is permanent.
///
/// `RoutingRuleDetailView.delete` calls `obj.delete()`. There is no soft delete
/// behind this verb, unlike custom fields and tags, so the control that calls
/// it has to say so and has to offer turning the rule off as the reversible
/// alternative.
const String routingRemovalExplanation =
    'The rule is gone for good, along with its place in the order. Tickets it '
    'already routed keep their assignee. If you only want it to stop running, '
    'turn it off instead: that is reversible.';
