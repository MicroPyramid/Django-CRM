import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/data/models/automation.dart';
import 'package:flutter_test/flutter_test.dart';

const ruleId = '3f2b8c1e-5a4d-4e2f-9b7a-1c2d3e4f5a6b';

Map<String, dynamic> catalogueJson({List<Map<String, dynamic>>? links}) => {
  'objects': [
    {
      'key': 'deal',
      'label': 'Deal',
      'label_plural': 'Deals',
      'fields': [
        {
          'key': 'stage',
          'label': 'Stage',
          'type': 'choice',
          'settable': true,
          'choices': [
            {
              'value': 's1',
              'label': 'Proposal',
              'group': 'Sales',
              'settable': true,
            },
          ],
        },
        {
          'key': 'stage_kind',
          'label': 'Outcome',
          'type': 'choice',
          'settable': false,
          'choices': [
            {
              'value': 'won',
              'label': 'Won (any pipeline)',
              'group': '',
              'settable': false,
            },
          ],
        },
        {
          'key': 'amount',
          'label': 'Amount',
          'type': 'number',
          'choices': [],
          'settable': true,
        },
      ],
      'parent': {'key': 'account', 'label': 'Account'},
      'links': links ?? [],
    },
    {
      'key': 'lead',
      'label': 'Lead',
      'label_plural': 'Leads',
      'fields': [],
      'parent': null,
      'links': [],
    },
  ],
  'operators': {
    'text': ['eq', 'neq', 'contains', 'not_contains', 'empty', 'not_empty'],
    'boolean': ['true', 'false'],
  },
  'update_only_operators': ['was', 'was_not'],
  'actions': ['set_field', 'assign', 'create_task', 'notify', 'webhook'],
  'people': [
    {'id': 'p1', 'name': 'Asha'},
  ],
  'endpoints': [
    {'id': 'e1', 'description': 'hooks.example.com'},
  ],
  'limits': {'conditions': 20, 'actions': 10},
};

Map<String, dynamic> ruleJson({String? status}) => {
  'id': ruleId,
  'name': 'Close it',
  'object_key': 'deal',
  'trigger': {'event': 'updated', 'field': 'stage_kind', 'to': 'won'},
  'match': 'any',
  'conditions': [
    {'field': 'amount', 'op': 'gt', 'value': 100},
  ],
  'actions': [
    {
      'type': 'assign',
      'mode': 'rotate',
      'people': ['p1', 'p2'],
    },
  ],
  'is_active': true,
  'position': 0,
  'owner': {'id': 'p1', 'name': 'Asha'},
  'switched_on_at': '2026-10-22T09:00:00Z',
  'paused_reason': '',
  if (status != null) ...{
    'status': status,
    'status_text': 'text for $status',
    'runs_7d': 4,
    'failures_7d': 1,
  },
};

void main() {
  test('reads a catalogue with grouped stages, Outcome and link specs', () {
    final c = AutomationCatalogue.fromJson(
      catalogueJson(
        links: [
          {
            'id': 'in:property.owner',
            'label': 'Properties',
            'object_key': 'obj:property',
          },
        ],
      ),
    );
    expect(c.maxConditions, 20);
    expect(c.maxActions, 10);
    expect(c.updateOnlyOperators, ['was', 'was_not']);
    expect(c.operators['boolean'], ['true', 'false']);
    expect(c.people.single.name, 'Asha');
    expect(c.endpoints.single.description, 'hooks.example.com');
    final deal = c.objects.first;
    expect(deal.labelPlural, 'Deals');
    expect(deal.parent?.key, 'account');
    expect(c.objects.last.parent, isNull);
    final stage = deal.fields.first;
    expect(stage.settable, isTrue);
    expect(stage.choices.single.group, 'Sales');
    final outcome = deal.fields[1];
    expect(outcome.label, 'Outcome');
    expect(outcome.settable, isFalse);
    expect(outcome.choices.single.settable, isFalse);
    final link = deal.links.single;
    expect(
      (link.id, link.label, link.objectKey),
      ('in:property.owner', 'Properties', 'obj:property'),
    );
  });

  test('reads a self-hosted catalogue with no links and no custom objects', () {
    final c = AutomationCatalogue.fromJson(catalogueJson());
    expect(c.objects.map((o) => o.key), ['deal', 'lead']);
    expect(c.objects.every((o) => o.links.isEmpty), isTrue);
    expect(c.objects.any((o) => o.key.startsWith('obj:')), isFalse);
  });

  test('reads a rule row with each of the five statuses', () {
    for (final s in ['on', 'off', 'paused', 'over_limit', 'needs_attention']) {
      final row = AutomationRuleRow.fromJson(ruleJson(status: s));
      expect(row.status, s);
      expect(row.statusText, 'text for $s');
      expect((row.runs7d, row.failures7d), (4, 1));
      expect(row.name, 'Close it');
      expect(row.objectKey, 'deal');
      expect(row.match, 'any');
      expect(row.isActive, isTrue);
      expect(row.owner?.name, 'Asha');
      expect(row.switchedOnAt, DateTime.utc(2026, 10, 22, 9));
      expect(row.trigger.event, 'updated');
      expect((row.trigger.field, row.trigger.to), ('stage_kind', 'won'));
      expect(row.conditions.single.op, 'gt');
      expect(row.actions.single.values['people'], ['p1', 'p2']);
    }
    final answer = AutomationRulesAnswer.fromJson({
      'summary': '5 of 2 active rules',
      'results': [ruleJson(status: 'on')],
    });
    expect(answer.summary, '5 of 2 active rules');
    expect(answer.rules.single.status, 'on');
    expect(
      AutomationRulesAnswer.fromJson({'summary': null, 'results': []}).summary,
      isNull,
    );
  });

  test('reads a run with undone and failed steps and triggered_by', () {
    final page = RunPage.fromJson({
      'count': 31,
      'results': [
        {
          'id': 'r1',
          'created_at': '2026-10-22T10:00:00Z',
          'record_id': 'rec',
          'record_name': 'Acme renewal',
          'object_key': 'deal',
          'status': 'failed',
          'reason': 'That is not a stage of this deal\'s pipeline.',
          'steps': [
            {
              'action': 0,
              'type': 'assign',
              'status': 'undone',
              'text': 'Assigned Acme renewal to Asha',
            },
            {
              'action': 1,
              'type': 'set_field',
              'status': 'failed',
              'text': 'That is not a stage of this deal\'s pipeline.',
            },
          ],
          'skipped_count': 0,
          'depth': 2,
          'triggered_by': {'id': 'r0', 'rule_name': 'Other rule'},
        },
        {
          'id': 'r2',
          'created_at': '2026-10-22T11:00:00Z',
          'record_id': 'rec',
          'record_name': 'Acme renewal',
          'object_key': 'deal',
          'status': 'done',
          'reason': '',
          'steps': [],
          'skipped_count': 0,
          'depth': 1,
          'triggered_by': null,
        },
      ],
    }, offset: 20);
    expect((page.count, page.offset, page.runs.length), (31, 20, 2));
    final run = page.runs.first;
    expect(run.triggeredByRuleName, 'Other rule');
    expect(run.recordName, 'Acme renewal');
    expect(run.steps.map((s) => s.status), ['undone', 'failed']);
    expect(run.steps.first.type, 'assign');
    expect(run.steps.last.action, 1);
    expect(page.runs.last.triggeredByRuleName, isNull);
  });

  test('survives missing and wrongly typed keys without throwing', () {
    expect(AutomationCatalogue.fromJson({}).objects, isEmpty);
    expect(AutomationCatalogue.fromJson({}).maxActions, 10);
    final odd = AutomationCatalogue.fromJson({
      'objects': 'x',
      'operators': [],
      'people': [
        1,
        null,
        {'id': 3},
      ],
      'endpoints': {'a': 1},
      'limits': 'no',
    });
    expect(odd.objects, isEmpty);
    expect(odd.operators, isEmpty);
    expect(odd.maxConditions, 20);
    final rule = AutomationRule.fromJson({
      'id': 5,
      'name': null,
      'trigger': 'created',
      'conditions': [
        1,
        'x',
        {'field': 7},
      ],
      'actions': {'type': 'notify'},
      'is_active': 'yes',
      'owner': 'me',
      'switched_on_at': 12,
    });
    expect(rule.id, '5');
    expect(rule.trigger.event, 'created');
    expect(rule.match, 'all');
    expect(rule.actions, isEmpty);
    expect(rule.isActive, isFalse);
    expect(rule.owner, isNull);
    expect(rule.switchedOnAt, isNull);
    final row = AutomationRuleRow.fromJson({'runs_7d': 'many'});
    expect((row.status, row.runs7d), ('off', 0));
    final run = AutomationRun.fromJson({
      'steps': [null, 4],
      'triggered_by': 'x',
      'created_at': 9,
    });
    expect(run.steps, isEmpty);
    expect(run.triggeredByRuleName, isNull);
    expect(RunPage.fromJson({'results': 3}).runs, isEmpty);
  });

  test('a missing or empty triggered_by name is null, not blank', () {
    for (final by in [
      null,
      <String, dynamic>{'id': 'x'},
      {'id': 'x', 'rule_name': ''},
    ]) {
      expect(
        AutomationRun.fromJson({'triggered_by': by}).triggeredByRuleName,
        isNull,
      );
    }
  });

  test('falls back to the key when a label is empty or missing', () {
    final c = AutomationCatalogue.fromJson({
      'objects': [
        {
          'key': 'deal',
          'label': '',
          'fields': [
            {'key': 'amount', 'label': ''},
            {
              'key': 'stage',
              'type': 'choice',
              'choices': [
                {'value': 's1', 'label': ''},
              ],
            },
          ],
        },
      ],
    });
    final o = c.objects.single;
    expect((o.label, o.labelPlural), ('deal', 'deal'));
    expect(o.fields.map((f) => f.label), ['amount', 'stage']);
    expect(o.fields.last.choices.single.label, 's1');
  });

  test('copies a draft deeply, so editing the copy leaves the original', () {
    final rule = AutomationRule.fromJson(ruleJson());
    final draft = RuleDraft.from(rule);
    final copy = draft.copy();
    copy.name = 'Changed';
    copy.trigger.to = 'lost';
    copy.conditions.first.op = 'lt';
    copy.actions.first.values['people'].add('p3');
    copy.actions.first.values['mode'] = 'replace';
    copy.conditions.add(ConditionDraft(field: 'amount', op: 'empty'));
    expect(draft.name, 'Close it');
    expect(draft.trigger.to, 'won');
    expect(draft.conditions.single.op, 'gt');
    expect(draft.actions.first.values['people'], ['p1', 'p2']);
    expect(draft.actions.first.values['mode'], 'rotate');
    draft.actions.first.values['people'].clear();
    expect(rule.actions.first.values['people'], ['p1', 'p2']);

    final blank = RuleDraft.blank('lead');
    expect(blank.objectKey, 'lead');
    expect(blank.trigger.event, 'created');
    expect(blank.match, 'all');
    expect(blank.conditions, isEmpty);
    expect(blank.actions, isEmpty);
  });

  test('refuses a non-UUID rule id in every URL builder', () {
    expect(ApiConfig.automationCatalogue, endsWith('/automation/catalogue/'));
    expect(ApiConfig.automationRules, endsWith('/automation/rules/'));
    expect(ApiConfig.automationReorder, endsWith('/automation/rules/reorder/'));
    expect(
      ApiConfig.automationRule(ruleId),
      endsWith('/automation/rules/$ruleId/'),
    );
    expect(
      ApiConfig.automationRuleTry(ruleId),
      endsWith('/automation/rules/$ruleId/try/'),
    );
    expect(
      ApiConfig.automationRuleRuns(ruleId),
      endsWith('/automation/rules/$ruleId/runs/?limit=20&offset=0'),
    );
    expect(
      ApiConfig.automationRuleRuns(ruleId, offset: 40),
      endsWith('?limit=20&offset=40'),
    );
    for (final bad in ['', 'reorder', '../x', '$ruleId/try', 'nope']) {
      expect(() => ApiConfig.automationRule(bad), throwsArgumentError);
      expect(() => ApiConfig.automationRuleTry(bad), throwsArgumentError);
      expect(() => ApiConfig.automationRuleRuns(bad), throwsArgumentError);
    }
  });
}
