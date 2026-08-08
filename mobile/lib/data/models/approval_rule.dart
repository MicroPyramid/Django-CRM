/// Approval rules: what gates a ticket close, and who can clear it.
///
/// Three things the list reads as, and is not:
///
/// 1. **The rules are not cumulative.** `find_matching_rule` collects every
///    active rule matching the case, sorts by specificity (how many of
///    priority / type / team are set), and returns exactly one. A broad rule
///    beside a narrow one is one gate and a fallback, not two gates.
/// 2. **Identical rules are not equals.** Among rules whose conditions match,
///    the sort is stable over `-created_at`, so the newest takes every case and
///    an older twin never runs. [shadowedRuleIds] reports exactly that case; a
///    partial overlap between different conditions is a real fallback rather
///    than a dead rule, so nothing here guesses at those.
/// 3. **Named approvers widen a rule, they do not narrow it.**
///    `Approval.can_be_acted_on_by` returns true for a named approver OR for
///    anyone holding `approver_role`, so naming two people on an admin rule
///    still leaves every admin able to clear it.
///
/// None of this is a security control. `ApprovalApproveView` decides who may
/// act, and separately refuses an approval whose requester is its approver.
///
/// `frontend/src/routes/(app)/settings/ticket-approvals/matching.js` carries
/// the same rules.
library;

import 'lookup_models.dart';

/// The `approver_role` values a profile can actually hold.
///
/// `APPROVER_ROLE_CHOICES` offers ADMIN and MANAGER; `Profile.role` is only
/// ADMIN or USER. MANAGER is reserved for a role model that does not exist yet,
/// so today it matches nobody, which is why a MANAGER rule with no named
/// approvers gates closes that no one can clear.
const List<String> rolesThatExist = ['ADMIN'];

/// What the approver-role picker offers, which is the model's list, not the
/// list that works. MANAGER is offered because the column accepts it and
/// hiding it would rewrite a rule already set to it.
const List<({String value, String label})> approverRoleChoices = [
  (value: 'ADMIN', label: 'Admin'),
  (value: 'MANAGER', label: 'Manager (matches nobody yet)'),
];

const List<String> approvalPriorities = ['Low', 'Normal', 'High', 'Urgent'];
const List<String> approvalCaseTypes = ['Question', 'Incident', 'Problem'];

class ApprovalRule {
  const ApprovalRule({
    required this.id,
    this.name = '',
    this.isActive = true,
    this.approverRole = 'ADMIN',
    this.approvers = const [],
    this.matchPriority,
    this.matchCaseType,
    this.matchTeam,
    this.pendingCount = 0,
    this.createdAt,
  });

  final String id;
  final String name;
  final bool isActive;
  final String approverRole;

  /// The API sends `[{id, email}]`. Kept as people rather than flattened to
  /// emails, because the edit form needs the ids to preselect them.
  final List<UserLookup> approvers;

  final String? matchPriority;
  final String? matchCaseType;
  final TeamLookup? matchTeam;

  /// Approvals in state "pending" bound to this rule, server-computed.
  final int pendingCount;

  /// Not displayed. It is the tie-break `find_matching_rule` uses between rules
  /// with identical conditions, so it is what tells an older duplicate from a
  /// fallback.
  final DateTime? createdAt;

  factory ApprovalRule.fromJson(Map<String, dynamic> json) {
    final team = json['match_team'];
    return ApprovalRule(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      isActive: json['is_active'] as bool? ?? true,
      approverRole: json['approver_role']?.toString() ?? 'ADMIN',
      approvers: [
        for (final approver in (json['approvers'] as List?) ?? const [])
          if (approver is Map && approver['id'] != null)
            UserLookup.fromJson(approver.cast<String, dynamic>()),
      ],
      matchPriority: _blankToNull(json['match_priority']),
      matchCaseType: _blankToNull(json['match_case_type']),
      matchTeam: team is Map
          ? TeamLookup.fromJson(team.cast<String, dynamic>())
          : null,
      pendingCount: (json['pending_count'] as num?)?.round() ?? 0,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.tryParse(json['created_at'].toString()),
    );
  }

  bool get roleClears => rolesThatExist.contains(approverRole);

  /// The named approvers' labels, blanks dropped.
  List<String> get approverNames => approvers
      .map((a) => a.email.trim().isNotEmpty ? a.email.trim() : a.displayName)
      .where((label) => label.isNotEmpty)
      .toList(growable: false);

  /// Everyone who can clear this rule, as the sentence a person would say.
  String get approverSentence {
    final named = approverNames;
    if (roleClears) {
      return named.isEmpty
          ? 'any admin'
          : 'any admin, or ${named.join(' or ')}';
    }
    return named.isEmpty ? 'nobody' : named.join(' or ');
  }

  /// True when this rule gates closes that nobody in the org can clear.
  ///
  /// Only meaningful for an active rule: an inactive one gates nothing, so it
  /// cannot strand anything.
  bool get clearableByNobody =>
      isActive && !roleClears && approverNames.isEmpty;

  /// What the rule matches, as the sentence a person would say.
  String get matchSentence {
    final parts = [
      if (matchPriority != null) '$matchPriority priority',
      if (matchCaseType != null) matchCaseType!.toLowerCase(),
      if (matchTeam != null) '${matchTeam!.name} team',
    ];
    return parts.isEmpty ? 'Every ticket' : parts.join(' · ');
  }

  /// How many filters are set. Mirrors `ApprovalRule.specificity`, the sort key
  /// that decides which of several matching rules runs.
  int get specificity => [
    matchPriority,
    matchCaseType,
    matchTeam?.id,
  ].where((v) => v != null).length;

  /// A key identical for two rules that match exactly the same tickets.
  ///
  /// `trigger_event` is deliberately not in it: `pre_close` is the only value
  /// the backend accepts, so including a constant would only look like a
  /// comparison.
  String get signature =>
      '${matchPriority ?? ''}|${matchCaseType ?? ''}|${matchTeam?.id ?? ''}';
}

String? _blankToNull(dynamic value) {
  final text = value?.toString().trim() ?? '';
  return text.isEmpty ? null : text;
}

/// Whether [a] was created after [b].
///
/// A missing timestamp counts as neither, so a row the API did not date never
/// claims to beat one it did, and no rule is called dead on the strength of a
/// blank.
bool _isNewer(DateTime? a, DateTime? b) {
  if (a == null || b == null) return false;
  return a.isAfter(b);
}

/// The active rules that can never be the one that runs.
///
/// A rule is here when another ACTIVE rule matches exactly the same tickets and
/// was created later. Inactive rules are neither reported nor counted as
/// shadowers: one gates nothing, so it can neither be beaten nor beat anything.
Set<String> shadowedRuleIds(List<ApprovalRule> rules) {
  final active = rules.where((r) => r.isActive).toList(growable: false);
  return {
    for (final rule in active)
      if (active.any(
        (other) =>
            other.id != rule.id &&
            other.signature == rule.signature &&
            _isNewer(other.createdAt, rule.createdAt),
      ))
        rule.id,
  };
}

/// The rule that actually takes a shadowed rule's tickets, or null.
ApprovalRule? shadowedBy(ApprovalRule rule, List<ApprovalRule> rules) {
  final winners =
      rules
          .where(
            (other) =>
                other.isActive &&
                other.id != rule.id &&
                other.signature == rule.signature &&
                _isNewer(other.createdAt, rule.createdAt),
          )
          .toList()
        ..sort((a, b) => _isNewer(a.createdAt, b.createdAt) ? -1 : 1);
  return winners.isEmpty ? null : winners.first;
}

/// The body for creating or editing a rule.
///
/// `trigger_event` is set here rather than asked for: `pre_close` is the only
/// value the backend accepts, and a picker with one option is a control that
/// cannot be wrong, so it should not be a control.
///
/// `isActive` is optional because the edit form does not own it: the row's own
/// Turn off / Turn on control does, and sending it from an edit would let a
/// stale form flip a rule back on.
Map<String, dynamic> approvalRulePayload({
  required String name,
  required String approverRole,
  required List<String> approverIds,
  String? matchPriority,
  String? matchCaseType,
  String? matchTeamId,
  bool? isActive,
}) {
  final body = <String, dynamic>{
    'name': name.trim(),
    'approver_role': approverRole,
    'approver_ids': approverIds.where((id) => id.trim().isNotEmpty).toList(),
    'trigger_event': 'pre_close',
    // All three are `allow_null=True`, and the empty string fails the
    // ChoiceField and the PK lookup alike, so "any" has to travel as null.
    'match_priority': (matchPriority?.trim().isEmpty ?? true)
        ? null
        : matchPriority,
    'match_case_type': (matchCaseType?.trim().isEmpty ?? true)
        ? null
        : matchCaseType,
    'match_team_id': (matchTeamId?.trim().isEmpty ?? true) ? null : matchTeamId,
  };
  if (isActive != null) body['is_active'] = isActive;
  return body;
}

/// Turn a rule on or off without rewriting it.
///
/// Its own body rather than a reuse of [approvalRulePayload]: that builds a
/// whole rule, and a form that is not open has nothing to say about the name.
/// `ApprovalRuleDetailView.put` is `partial=True`, so a single key leaves
/// everything else alone.
Map<String, dynamic> approvalRuleActivePayload(bool isActive) => {
  'is_active': isActive,
};

/// What a create or edit has to fix before it is worth sending, or null.
String? approvalRuleNameProblem(String name) {
  final trimmed = name.trim();
  if (trimmed.isEmpty) return 'Give the rule a name.';
  if (trimmed.length > 128) {
    return 'That name is too long (128 characters max).';
  }
  return null;
}

/// What Delete does, which is two different things behind one verb.
///
/// `ApprovalRuleDetailView.delete` destroys a rule that has never gated a
/// close and turns off one that has, because `Approval.rule` is
/// `on_delete=PROTECT` and the history has to keep pointing at it. Both answer
/// 2xx, and `pendingCount` cannot predict which: it counts only the pending
/// state, and the backend's check counts every state. So the line names both.
const String approvalRuleDeleteExplanation =
    'A rule that has never gated a close is deleted for good. One with any '
    'approval history is turned off instead, because the record has to be '
    'kept. Which happens is decided when you confirm, and you will be told.';

/// Which of the two outcomes the response describes.
///
/// The hard delete answers 204 with no body; the soft one answers 200 carrying
/// `is_active: false`. Read rather than assumed, and read here rather than in
/// the notifier so it can be pinned: `pendingCount` cannot predict it, since it
/// counts only the pending state while the backend's check counts every state.
bool approvalRuleWasTurnedOff(Map<String, dynamic>? body) =>
    body?['is_active'] == false;

/// What actually happened, once the server has decided.
String approvalRuleDeleteResult({required bool turnedOff}) => turnedOff
    ? 'That rule had approval history, so it was turned off instead of '
          'deleted. It is still in the list, off, and gates nothing.'
    : 'Rule deleted';
