import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/automation.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:flutter_riverpod/misc.dart' show Override;

/// Awkward automation data for the width checks: a 120-character rule name,
/// a person no longer active, grouped stages, a failed run, long step texts.

const autoRuleId = '3f2b8c1e-7a4d-4e2b-9c1a-5d6e7f8a9b0c';
const autoDealId = '9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d';

/// Exactly 120 characters, the name field's limit.
const longRuleName =
    'Deal won in the enterprise renewals pipeline: onboarding kickoff task, '
    'a note to the account team, and new owner in turn';

const longRecordName =
    'Harbour Lane Logistics: the northern region fleet renewal and the depot '
    'expansion for the next three financial years';

/// In the rule, missing from the catalogue's people: someone deactivated.
const gonePerson = 'p-gone';

Map<String, dynamic> _field(
  String key,
  String label,
  String type, {
  bool settable = true,
  List<Map<String, dynamic>> choices = const [],
}) => {
  'key': key,
  'label': label,
  'type': type,
  'settable': settable,
  'choices': choices,
};

final autoCatalogue = AutomationCatalogue.fromJson({
  'objects': [
    {
      'key': 'deal',
      'label': 'Deal',
      'label_plural': 'Deals',
      'fields': [
        _field('name', 'Name', 'text'),
        _field('amount', 'Amount', 'number'),
        _field(
          'stage',
          'Stage',
          'choice',
          choices: [
            {'value': 's-prop', 'label': 'Proposal', 'group': 'Sales'},
            {'value': 's-won', 'label': 'Won', 'group': 'Sales'},
            {
              'value': 's-ent-won',
              'label': 'Signed and handed over to onboarding',
              'group': 'Enterprise renewals and expansion pipeline',
            },
          ],
        ),
        _field(
          'stage_kind',
          'Outcome',
          'choice',
          settable: false,
          choices: [
            {'value': 'won', 'label': 'Won (any pipeline)', 'settable': false},
            {
              'value': 'lost',
              'label': 'Lost (any pipeline)',
              'settable': false,
            },
          ],
        ),
        _field('close_date', 'Expected close date', 'date'),
        _field('is_priority', 'Priority account', 'boolean'),
        _field('assigned_to', 'Assigned to', 'people'),
      ],
      'parent': {'key': 'account', 'label': 'Account'},
      'links': [
        {
          'id': 'out:sites',
          'label': 'Sites linked through the deal and every regional office',
          'object_key': 'obj:site',
        },
      ],
    },
    {
      'key': 'account',
      'label': 'Account',
      'label_plural': 'Accounts',
      'fields': [_field('website', 'Website', 'text')],
    },
  ],
  'operators': {
    'text': ['eq', 'neq', 'contains', 'not_contains', 'empty', 'not_empty'],
    'number': ['eq', 'neq', 'gt', 'lt', 'empty', 'not_empty'],
    'choice': ['eq', 'neq', 'in', 'not_in', 'empty', 'not_empty'],
    'date': ['eq', 'neq', 'gt', 'lt', 'empty', 'not_empty'],
    'boolean': ['true', 'false'],
    'people': ['eq', 'includes', 'excludes', 'empty', 'not_empty'],
  },
  'update_only_operators': ['was', 'was_not'],
  'actions': ['set_field', 'assign', 'create_task', 'notify', 'webhook'],
  'people': [
    {'id': 'p-asha', 'name': 'Asha Rao'},
    {'id': 'p-ben', 'name': 'Benedict Okonkwo-Fairweather'},
  ],
  'endpoints': [
    {
      'id': 'e-1',
      'description': 'Billing system: renewals and onboarding events (JSON)',
    },
  ],
  'limits': {'conditions': 20, 'actions': 10},
});

final autoTrigger = TriggerDraft(
  event: 'updated',
  field: 'stage',
  to: 's-ent-won',
);

final autoConditions = [
  ConditionDraft(field: 'amount', op: 'gt', value: 25000),
  ConditionDraft(field: 'stage', op: 'in', value: ['s-won', 's-ent-won']),
  ConditionDraft(field: 'assigned_to', op: 'includes', value: gonePerson),
];

final autoActions = [
  ActionDraft(
    type: 'create_task',
    values: {
      'title':
          'Book the onboarding kickoff with {name} and send the welcome '
          'pack before the first invoice goes out',
      'due_in_days': 3,
      'priority': 'High',
      'assign_to': 'person',
      'person': gonePerson,
    },
  ),
  ActionDraft(
    type: 'notify',
    values: {
      'to': ['record_assignees', 'parent_assignees', 'linked:out:sites'],
      'people': ['p-asha', gonePerson],
      'message':
          '{name} is won. Please review the handover notes and confirm the '
          'kickoff date with the customer today.',
    },
  ),
  ActionDraft(
    type: 'assign',
    values: {
      'mode': 'rotate',
      'people': ['p-asha', 'p-ben', gonePerson],
    },
  ),
];

AutomationRule autoRule() => AutomationRule(
  id: autoRuleId,
  name: longRuleName,
  objectKey: 'deal',
  trigger: autoTrigger.copy(),
  conditions: [for (final c in autoConditions) c.copy()],
  actions: [for (final a in autoActions) a.copy()],
  isActive: true,
  owner: const RulePerson(id: 'p-asha', name: 'Asha Rao'),
);

AutomationRuleRow _row(
  String id,
  String name,
  String status, {
  String text = '',
  int runs = 0,
  int failures = 0,
}) => AutomationRuleRow(
  id: id,
  name: name,
  objectKey: 'deal',
  trigger: autoTrigger.copy(),
  status: status,
  statusText: text,
  runs7d: runs,
  failures7d: failures,
);

final autoRows = AutomationRulesAnswer(
  rules: [
    _row(autoRuleId, longRuleName, 'on', runs: 1240, failures: 37),
    _row(
      '11111111-1111-4111-8111-111111111111',
      'New lead: rotate owners',
      'paused',
      text:
          'Paused because the admin who switched it on left the '
          'organization.',
    ),
    _row(
      '22222222-2222-4222-8222-222222222222',
      'Ticket reopened: tell the team lead and the account owner',
      'needs_attention',
      text:
          'Needs attention: Each person must be an active member of this '
          'org.',
      runs: 4,
      failures: 4,
    ),
    _row('33333333-3333-4333-8333-333333333333', 'Old cleanup', 'off'),
    _row('44444444-4444-4444-8444-444444444444', 'Site visits', 'over_limit'),
  ],
);

AutomationRun _run(
  String id,
  String status, {
  String reason = '',
  List<RunStep> steps = const [],
  String? by,
  String name = longRecordName,
}) => AutomationRun.fromJson({
  'id': id,
  'created_at': '2025-10-21T18:03:00Z',
  'record_id': autoDealId,
  'record_name': name,
  'object_key': 'deal',
  'status': status,
  'reason': reason,
  'steps': [
    for (final s in steps)
      {'action': s.action, 'type': s.type, 'status': s.status, 'text': s.text},
  ],
  if (by != null) 'triggered_by': {'id': 'run-0', 'rule_name': by},
});

final autoRuns = RunPage(
  count: 45,
  runs: [
    _run(
      'run-1',
      'done',
      steps: const [
        RunStep(
          action: 0,
          type: 'create_task',
          status: 'done',
          text:
              'Created the task "Book the onboarding kickoff with Harbour '
              'Lane Logistics and send the welcome pack" for Asha Rao',
        ),
        RunStep(
          action: 1,
          type: 'notify',
          status: 'done',
          text: 'Notified Asha Rao and Benedict Okonkwo-Fairweather',
        ),
        RunStep(
          action: 2,
          type: 'assign',
          status: 'undone',
          text: 'Assigned to Benedict Okonkwo-Fairweather by rotation',
        ),
      ],
    ),
    _run(
      'run-2',
      'failed',
      reason:
          "That is not a stage of this deal's pipeline, so the rule stopped "
          'and nothing it wrote was kept.',
      steps: const [
        RunStep(
          action: 0,
          type: 'set_field',
          status: 'failed',
          text: "That is not a stage of this deal's pipeline",
        ),
        RunStep(
          action: 1,
          type: 'notify',
          status: 'skipped',
          text: 'Nobody to notify',
        ),
      ],
    ),
    _run(
      'run-3',
      'skipped',
      reason: '2 runs skipped: the org reached its hourly limit',
      by: 'Ticket reopened: tell the team lead and the account owner',
      name: '<b>Bold</b> [open](javascript:x)',
    ),
  ],
);

const autoTrySteps = [
  RunStep(
    action: 0,
    type: 'create_task',
    status: 'planned',
    text:
        'Would create the task "Book the onboarding kickoff with Harbour Lane '
        'Logistics and send the welcome pack" for Someone no longer active',
  ),
  RunStep(
    action: 1,
    type: 'notify',
    status: 'skipped',
    text: 'None of the chosen people is an active member',
  ),
  RunStep(
    action: 2,
    type: 'assign',
    status: 'failed',
    text: 'Each person must be an active member of this org.',
  ),
];

/// The automation screens over these fixtures, as an admin in one org.
List<Override> automationOverrides({bool admin = true}) => [
  isOrgAdminProvider.overrideWithValue(admin),
  selectedOrgProvider.overrideWithValue(
    const Organization(id: 'org-1', name: 'Acme'),
  ),
  automationCatalogueProvider.overrideWith((ref) async => autoCatalogue),
  automationRulesProvider.overrideWith(_FixtureRules.new),
  automationRuleProvider.overrideWith((ref, id) async => autoRule()),
  automationRunsProvider.overrideWith((ref, key) async => autoRuns),
];

class _FixtureRules extends AutomationRulesNotifier {
  @override
  Future<AutomationRulesAnswer> build() async => autoRows;
}

/// The automation notification verbs, each unread, as the feed sends them.
List<Map<String, dynamic>> automationNotificationsJson() => [
  {
    'id': 'n-message',
    'verb': 'automation.message',
    'actor': {
      'id': 'p-asha',
      'user_details': {'email': 'asha.rao@example.com', 'profile_pic': null},
    },
    'entity_type': 'Opportunity',
    'entity_id': autoDealId,
    'entity_name': longRecordName,
    'data': {
      'message':
          'Harbour Lane Logistics is won. Please review the handover notes '
          'and confirm the kickoff date with the customer today.',
      'rule': longRuleName,
    },
    'link': '/pipeline/$autoDealId',
    'read_at': null,
    'created_at': '2026-10-22T09:00:00Z',
  },
  {
    'id': 'n-markup',
    'verb': 'automation.message',
    'actor': {
      'id': 'p-asha',
      'user_details': {'email': 'asha.rao@example.com', 'profile_pic': null},
    },
    'entity_name': 'Lead 7',
    'data': {
      'message': '<img src=x onerror=alert(1)> [open](javascript:x)',
      'rule': '<b>Rule</b>',
    },
    'link': 'https://evil.example/leads/$autoDealId',
    'read_at': null,
    'created_at': '2026-10-22T08:00:00Z',
  },
  {
    'id': 'n-failed',
    'verb': 'automation.failed',
    'actor': null,
    'entity_name': longRuleName,
    'data': {
      'rule': longRuleName,
      'rule_id': autoRuleId,
      'reason': "That is not a stage of this deal's pipeline.",
    },
    'link': '/settings/automation/$autoRuleId',
    'read_at': null,
    'created_at': '2026-10-22T07:00:00Z',
  },
  {
    'id': 'n-paused',
    'verb': 'automation.paused',
    'actor': null,
    'entity_name': 'New lead: rotate owners',
    'data': {
      'rules': ['New lead: rotate owners', longRuleName],
      'reason':
          'Paused because the admin who switched it on left the organization.',
    },
    'link': '/settings/automation',
    'read_at': null,
    'created_at': '2026-10-22T06:00:00Z',
  },
  {
    'id': 'n-limit',
    'verb': 'automation.limit',
    'actor': null,
    'data': {'window_start': '2025-01-15T14:00:00+00:00'},
    'link': '/settings/automation',
    'read_at': null,
    'created_at': '2026-10-22T05:00:00Z',
  },
  {
    'id': 'n-bad',
    'verb': 'automation.failed',
    'actor': null,
    'data': {'rule': 5, 'reason': 'Broke'},
    'link': '/settings/automation',
    'read_at': null,
    'created_at': '2026-10-22T04:00:00Z',
  },
  {
    'id': 'n-unknown',
    'verb': 'automation.digest',
    'actor': null,
    'data': {'message': 'Weekly digest', 'rule': 'R'},
    'link': null,
    'read_at': null,
    'created_at': '2026-10-22T03:00:00Z',
  },
];
