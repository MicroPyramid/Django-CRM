import 'dart:convert';

import 'package:bottle_crm/data/models/custom_field_definition.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/providers/settings_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

/// Custom fields, the first page of the settings cluster on the phone.
///
/// What is worth pinning here is mostly about what does NOT go on the wire:
///
/// - The edit body must not carry `key`, `target_model` or `field_type`. The
///   server freezes all three because values live in each record's
///   `custom_fields` JSON keyed by `key`, so a change orphans, relocates or
///   reinterprets every value already stored.
/// - The reactivate body must carry `is_active` and nothing else. Reusing the
///   edit body would send a `label` the reactivate control does not have, and
///   the field would come back with its name blanked.
/// - The record-form fetch must send `include_counts=false`. Without it every
///   lead, deal and task form open pays for a full scan of the org's records
///   per definition, to compute a number no form displays.
class _FakeClient extends http.BaseClient {
  int status = 200;
  String body = '{}';
  final List<http.BaseRequest> sent = [];
  final List<String> bodies = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    final bytes = await request.finalize().toBytes();
    bodies.add(utf8.decode(bytes));
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

CustomFieldDefinition _field({
  String id = 'f1',
  String targetModel = 'Case',
  String key = 'severity',
  String label = 'Severity',
  CustomFieldType type = CustomFieldType.text,
  int order = 0,
}) {
  return CustomFieldDefinition(
    id: id,
    targetModel: targetModel,
    key: key,
    label: label,
    fieldType: type,
    displayOrder: order,
  );
}

void main() {
  group('key rules', () {
    test('accepts what the serializer accepts', () {
      // `validate_key` requires [a-z][a-z0-9_]*.
      expect(isValidCustomFieldKey('severity'), isTrue);
      expect(isValidCustomFieldKey('region_2'), isTrue);
      expect(isValidCustomFieldKey('a'), isTrue);
    });

    test('rejects the four shapes the server rejects', () {
      expect(isValidCustomFieldKey('Severity'), isFalse, reason: 'uppercase');
      expect(
        isValidCustomFieldKey('2region'),
        isFalse,
        reason: 'leading digit',
      );
      expect(isValidCustomFieldKey('re-gion'), isFalse, reason: 'hyphen');
      expect(isValidCustomFieldKey('re gion'), isFalse, reason: 'space');
      expect(isValidCustomFieldKey(''), isFalse);
    });
  });

  group('suggested key', () {
    test('slugs a label into a valid key', () {
      expect(suggestCustomFieldKey('Deal source'), 'deal_source');
      expect(suggestCustomFieldKey('Region / Zone'), 'region_zone');
      expect(suggestCustomFieldKey('  Severity  '), 'severity');
    });

    test('gives up rather than suggest a key the server would refuse', () {
      // A leading digit fails the server's leading-letter rule, so suggesting
      // it would hand the admin a key that cannot be saved.
      expect(suggestCustomFieldKey('2nd contact'), '');
      expect(suggestCustomFieldKey('???'), '');
      expect(suggestCustomFieldKey(''), '');
    });

    test('every non-empty suggestion is a key the server accepts', () {
      const labels = [
        'Deal source',
        'Region / Zone',
        'Renewal date!',
        'ARR (USD)',
        'Tier-1 account',
      ];
      for (final label in labels) {
        final suggestion = suggestCustomFieldKey(label);
        if (suggestion.isEmpty) continue;
        expect(isValidCustomFieldKey(suggestion), isTrue, reason: label);
      }
    });
  });

  group('draft validation', () {
    String? validate({
      bool isCreate = true,
      String label = 'Severity',
      String key = 'severity',
      String targetModel = 'Case',
      CustomFieldType type = CustomFieldType.text,
      List<CustomFieldOption> options = const [],
    }) {
      return validateCustomFieldDraft(
        isCreate: isCreate,
        label: label,
        key: key,
        targetModel: targetModel,
        fieldType: type,
        options: options,
      );
    }

    test('a complete create passes', () {
      expect(validate(), isNull);
    });

    test('a blank label is refused on both paths', () {
      expect(validate(label: '  '), contains('label'));
      expect(validate(isCreate: false, label: '  '), contains('label'));
    });

    test('a blank key is refused on create', () {
      expect(validate(key: ''), contains('key'));
    });

    test('a hyphenated key names the hyphen', () {
      // The trap worth a specific message: a hyphen reads as natural in a slug
      // and is the one character the server refuses without saying why.
      expect(validate(key: 'deal-source'), contains('hyphen'));
    });

    test('a target the server does not support is refused', () {
      expect(validate(targetModel: 'Widget'), contains('record type'));
    });

    test('the edit path does not check key or target', () {
      // Both are frozen after creation, so the edit form does not offer them
      // and has nothing to validate. Checking them anyway would block an edit
      // over values the form never collected.
      expect(validate(isCreate: false, key: '', targetModel: ''), isNull);
    });

    test('a dropdown needs at least one option', () {
      expect(
        validate(type: CustomFieldType.dropdown),
        contains('at least one option'),
      );
      expect(
        validate(
          type: CustomFieldType.dropdown,
          options: const [CustomFieldOption(value: '', label: '   ')],
        ),
        contains('at least one option'),
        reason: 'a blank row is not an option',
      );
    });

    test(
      'two options that would collide are refused before the round trip',
      () {
        final problem = validate(
          type: CustomFieldType.dropdown,
          options: const [
            CustomFieldOption(value: '', label: 'Very High'),
            CustomFieldOption(value: '', label: 'very high'),
          ],
        );
        expect(problem, contains('very-high'));
      },
    );

    test('an option of only punctuation is refused', () {
      expect(
        validate(
          type: CustomFieldType.dropdown,
          options: const [CustomFieldOption(value: '', label: '???')],
        ),
        contains('letter or number'),
      );
    });

    test('options are ignored on a non-dropdown', () {
      // The server refuses a non-empty options list on any other type, but
      // that is about the payload, not the draft: leaving stale rows behind
      // after switching the type back must not block the save.
      expect(
        validate(
          type: CustomFieldType.text,
          options: const [CustomFieldOption(value: '', label: 'Stale')],
        ),
        isNull,
      );
    });
  });

  group('create payload', () {
    Map<String, dynamic> build({
      CustomFieldType type = CustomFieldType.text,
      List<CustomFieldOption> options = const [],
    }) {
      return customFieldCreatePayload(
        targetModel: 'Case',
        key: '  severity ',
        label: '  Severity ',
        fieldType: type,
        isRequired: true,
        isFilterable: false,
        displayOrder: 3,
        options: options,
      );
    }

    test('carries the three fields that are only settable at creation', () {
      final body = build();
      expect(body['target_model'], 'Case');
      expect(body['key'], 'severity');
      expect(body['field_type'], 'text');
    });

    test('trims the key and label', () {
      expect(build()['key'], 'severity');
      expect(build()['label'], 'Severity');
    });

    test('sends no options on a non-dropdown', () {
      // `validate_definition_options` answers 400 for a non-empty options list
      // on any type but dropdown, so sending one turns a valid text field into
      // a rejection.
      expect(
        build(
          options: const [CustomFieldOption(value: 'a', label: 'A')],
        ),
        isNot(contains('options')),
      );
    });

    test('sends no org and no computed count', () {
      // `org` comes from the JWT server-side and `records_missing_value` is
      // computed. A payload carrying either would imply the client decided it.
      final body = build();
      expect(body.containsKey('org'), isFalse);
      expect(body.containsKey('records_missing_value'), isFalse);
      expect(body.containsKey('id'), isFalse);
    });

    test('a new dropdown option gets a slugified value', () {
      final body = build(
        type: CustomFieldType.dropdown,
        options: const [CustomFieldOption(value: '', label: 'Very High')],
      );
      expect(body['options'], [
        {'value': 'very-high', 'label': 'Very High'},
      ]);
    });

    test('a blank option row is dropped rather than sent', () {
      final body = build(
        type: CustomFieldType.dropdown,
        options: const [
          CustomFieldOption(value: '', label: 'Real'),
          CustomFieldOption(value: '', label: '   '),
        ],
      );
      expect((body['options'] as List), hasLength(1));
    });
  });

  group('update payload', () {
    Map<String, dynamic> build({
      CustomFieldType type = CustomFieldType.text,
      List<CustomFieldOption> options = const [],
    }) {
      return customFieldUpdatePayload(
        label: 'Renamed',
        fieldType: type,
        isRequired: false,
        isFilterable: true,
        displayOrder: 1,
        options: options,
      );
    }

    test('carries none of the three frozen fields', () {
      // This is the assertion the whole edit path rests on. The server answers
      // 400 for a change to any of them, and sending the unchanged value would
      // pass only by luck: `validate` compares against the instance, so a
      // stale value from a list fetched before someone else edited the row
      // would be a rejection the admin could not explain.
      final body = build();
      expect(body.containsKey('key'), isFalse);
      expect(body.containsKey('target_model'), isFalse);
      expect(body.containsKey('field_type'), isFalse);
    });

    test('carries what an edit may change', () {
      final body = build();
      expect(body['label'], 'Renamed');
      expect(body['is_required'], false);
      expect(body['is_filterable'], true);
      expect(body['display_order'], 1);
    });

    test('an existing option keeps its stored value when relabelled', () {
      // Every record holding this option refers to it by value. Re-slugifying
      // on a relabel would leave all of them pointing at an option that no
      // longer exists.
      final body = build(
        type: CustomFieldType.dropdown,
        options: const [
          CustomFieldOption(value: 'very-high', label: 'Critical'),
        ],
      );
      expect(body['options'], [
        {'value': 'very-high', 'label': 'Critical'},
      ]);
    });
  });

  group('activate payload', () {
    test('is is_active and nothing else', () {
      // There is no reactivate endpoint, so this rides the edit PUT. If it
      // carried the edit body's `label`, a reactivate would blank the field's
      // name, because the control that sends it has no label to send.
      expect(customFieldActivatePayload(), {'is_active': true});
    });
  });

  group('parsing', () {
    test('reads the counts the settings screen shows', () {
      final field = CustomFieldDefinition.fromJson({
        'id': 'f1',
        'target_model': 'Lead',
        'key': 'source',
        'label': 'Source',
        'field_type': 'dropdown',
        'is_required': true,
        'is_filterable': true,
        'display_order': 2,
        'is_active': false,
        'records_missing_value': 23,
        'options': [
          {'value': 'web', 'label': 'Web'},
        ],
      });
      expect(field.recordsMissingValue, 23);
      expect(field.isFilterable, isTrue);
      expect(field.isRequired, isTrue);
      expect(field.isActive, isFalse);
      expect(field.fieldType, CustomFieldType.dropdown);
      expect(field.options.single.value, 'web');
    });

    test('defaults the count to zero when the server omitted it', () {
      // The form path asks for `include_counts=false`, and the response then
      // carries no `records_missing_value` at all.
      final field = CustomFieldDefinition.fromJson({
        'id': 'f1',
        'key': 'source',
        'label': 'Source',
      });
      expect(field.recordsMissingValue, 0);
      expect(field.isFilterable, isFalse);
    });

    test('an unknown field type falls back to text rather than throwing', () {
      final field = CustomFieldDefinition.fromJson({
        'id': 'f1',
        'field_type': 'colour_picker',
      });
      expect(field.fieldType, CustomFieldType.text);
    });
  });

  group('grouping', () {
    test('groups by record type, ordered by the name shown', () {
      // "Deals" before "Tickets" is the label order, not the target_model
      // order: `Opportunity` sorts after `Case` and would put Tickets first.
      const state = CustomFieldsState(
        fields: [
          CustomFieldDefinition(
            id: 'a',
            targetModel: 'Case',
            key: 'a',
            label: 'A',
            fieldType: CustomFieldType.text,
          ),
          CustomFieldDefinition(
            id: 'b',
            targetModel: 'Opportunity',
            key: 'b',
            label: 'B',
            fieldType: CustomFieldType.text,
          ),
        ],
      );
      expect(state.grouped.map((e) => e.key), ['Opportunity', 'Case']);
    });

    test('orders fields by display_order, then label', () {
      final state = CustomFieldsState(
        fields: [
          _field(id: '1', label: 'Zulu', order: 0),
          _field(id: '2', label: 'Alpha', order: 5),
          _field(id: '3', label: 'Bravo', order: 0),
        ],
      );
      expect(state.grouped.single.value.map((f) => f.label), [
        'Bravo',
        'Zulu',
        'Alpha',
      ]);
    });
  });

  group('the provider', () {
    late ProviderContainer container;
    late _FakeClient client;

    setUp(() {
      client = _FakeClient();
      ApiService().setClientForTesting(client);
      container = ProviderContainer();
    });

    tearDown(() => container.dispose());

    // Riverpod 3 providers are auto-dispose, so a bare `read(p.future)` holds
    // no subscription and can be torn down mid-request. Listen first.
    Future<CustomFieldsState> readFields() {
      container.listen(customFieldsProvider, (_, _) {});
      return container.read(customFieldsProvider.future);
    }

    test('reads the definitions and the server totals', () async {
      client.body = '''
      {"definitions": [
        {"id": "f1", "target_model": "Case", "key": "severity",
         "label": "Severity", "field_type": "text", "is_required": true,
         "is_active": true, "records_missing_value": 4}
      ],
       "totals": {"count": 9, "active": 7, "models_extended": 3,
                  "required_with_gaps": 2}}
      ''';
      final state = await readFields();
      expect(state.fields.single.label, 'Severity');
      // Taken from `totals`, not recounted from the rows. The server computes
      // them over the org's whole definition set.
      expect(state.count, 9);
      expect(state.active, 7);
      expect(state.modelsExtended, 3);
      expect(state.requiredWithGaps, 2);
    });

    test('falls back to counting the rows when totals are absent', () async {
      client.body = '''
      {"definitions": [
        {"id": "f1", "target_model": "Case", "key": "a", "label": "A",
         "is_active": true, "is_required": true, "records_missing_value": 1},
        {"id": "f2", "target_model": "Lead", "key": "b", "label": "B",
         "is_active": false}
      ]}
      ''';
      final state = await readFields();
      expect(state.count, 2);
      expect(state.active, 1);
      expect(state.modelsExtended, 1, reason: 'only the active row counts');
      expect(state.requiredWithGaps, 1);
    });

    test('asks for the inactive rows too', () async {
      // This screen is the one that turns a field back on, and it cannot offer
      // that for a row it never fetched.
      client.body = '{"definitions": []}';
      await readFields();
      expect(client.sent.single.url.queryParameters, isEmpty);
    });

    test('a create POSTs the payload it was given', () async {
      client.body = '{"definitions": []}';
      await readFields();
      await container.read(customFieldsProvider.notifier).createField({
        'key': 'severity',
        'label': 'Severity',
      });
      final post = client.sent.firstWhere((r) => r.method == 'POST');
      expect(post.url.path, endsWith('/custom-fields/'));
      expect(jsonDecode(client.bodies[client.sent.indexOf(post)]), {
        'key': 'severity',
        'label': 'Severity',
      });
    });

    test('turning a field off is a DELETE on the row', () async {
      client.body = '{"definitions": []}';
      await readFields();
      await container.read(customFieldsProvider.notifier).deactivateField('f1');
      final sent = client.sent.firstWhere((r) => r.method == 'DELETE');
      expect(sent.url.path, endsWith('/custom-fields/f1/'));
    });

    test('turning a field on is a PUT carrying only is_active', () async {
      client.body = '{"definitions": []}';
      await readFields();
      await container.read(customFieldsProvider.notifier).activateField('f1');
      final put = client.sent.firstWhere((r) => r.method == 'PUT');
      expect(put.url.path, endsWith('/custom-fields/f1/'));
      expect(jsonDecode(client.bodies[client.sent.indexOf(put)]), {
        'is_active': true,
      });
    });

    test('a refusal is reported in the server own words', () async {
      client.body = '{"definitions": []}';
      await readFields();
      client.status = 403;
      client.body = '{"error": true, "errors": "Admin access required"}';
      final message = await container
          .read(customFieldsProvider.notifier)
          .createField({'key': 'x'});
      expect(message, 'Admin access required');
    });

    test('a field-level 400 reports the field message', () async {
      client.body = '{"definitions": []}';
      await readFields();
      client.status = 400;
      client.body =
          '{"error": true, "errors": {"key": ["key must be a lowercase slug '
          'starting with a letter (a-z, 0-9, _)"]}}';
      final message = await container
          .read(customFieldsProvider.notifier)
          .createField({'key': 'Bad-Key'});
      expect(message, contains('lowercase slug'));
    });
  });

  group('the record-form fetch', () {
    late ProviderContainer container;
    late _FakeClient client;

    setUp(() {
      client = _FakeClient();
      ApiService().setClientForTesting(client);
      container = ProviderContainer();
    });

    tearDown(() => container.dispose());

    test('opts out of the counts the settings screen needs', () async {
      // Without `include_counts=false` the endpoint runs one COUNT over the
      // org's records per target model plus a `custom_fields ? key` scan per
      // definition, on every lead, deal and task form open, to compute a
      // number no form displays. The web opts out on this same path.
      client.body = '{"definitions": []}';
      container.listen(customFieldDefinitionsProvider('Lead'), (_, _) {});
      await container.read(customFieldDefinitionsProvider('Lead').future);

      final params = client.sent.single.url.queryParameters;
      expect(params['include_counts'], 'false');
      expect(params['target_model'], 'Lead');
      expect(params['active_only'], 'true');
    });
  });
}
