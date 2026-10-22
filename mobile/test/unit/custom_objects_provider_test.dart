import 'dart:async';
import 'dart:convert';

import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/custom_field_definition.dart';
import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show ProviderListenable;
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class _FakeClient extends http.BaseClient {
  int status = 200;
  String body = '{}';
  bool offline = false;
  Future<void>? gate;
  final Map<String, String> routes = {};
  final List<http.BaseRequest> sent = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    await request.finalize().toBytes();
    final wait = gate;
    final text0 = routes[request.url.path] ?? body;
    if (wait != null) await wait;
    if (offline) throw http.ClientException('no route');
    final text = text0;
    return http.StreamedResponse(
      Stream.value(utf8.encode(text)),
      status,
      request: request,
    );
  }
}

const uuid = '3f2b8c1e-5a4d-4e8b-9c3a-1d2e3f4a5b6c';

const _objectsBody = '''
{"has_custom_objects": true,
 "objects": [{"key": "property", "label": "Property", "label_plural": "Properties"}],
 "link_targets": []}
''';

ObjectField _field(String key, String type, {String? target, bool? many}) =>
    ObjectField(
      key: key,
      label: key[0].toUpperCase() + key.substring(1),
      fieldType: type,
      target: target,
      many: many,
    );

final _definition = ObjectDefinition(
  summary: const ObjectSummary(
    key: 'property',
    label: 'Property',
    labelPlural: 'Properties',
    nameLabel: 'Address',
  ),
  fields: [
    _field('price', 'number'),
    _field('notes', 'text'),
    _field('enquiries', 'link', target: 'lead', many: true),
    _field('owner', 'link', target: 'contact', many: false),
  ],
);

ObjectRecord _record() => const ObjectRecord(
  id: uuid,
  name: '12 Park Lane',
  customFields: {'price': 100, 'notes': 'quiet'},
  assignedTo: [
    PersonRef(id: 'p1', name: 'Ann'),
    PersonRef(id: 'p2', name: 'Bo'),
  ],
  links: {
    'enquiries': LinkValue(
      records: [LinkedRecord(id: 'l1', object: 'lead', name: 'Lee')],
      hidden: 2,
    ),
    'owner': LinkValue(many: false, hidden: 1),
  },
);

List<String> _visibleIds(ObjectRecord r, String key) =>
    r.links[key]!.records.map((l) => l.id).toList();

class _OrgSwitch extends Notifier<Organization?> {
  @override
  Organization? build() => Organization.fromJson({'id': 'a', 'name': 'A'});

  void set(Organization? next) => state = next;
}

Future<void> _settle() async {
  for (var i = 0; i < 30; i++) {
    await Future<void>.delayed(Duration.zero);
  }
}

void main() {
  late ProviderContainer container;
  late _FakeClient client;

  setUp(() {
    client = _FakeClient();
    ApiService().setClientForTesting(client);
    container = ProviderContainer();
  });

  tearDown(() => container.dispose());

  Future<CustomObjectsAnswer?> readObjects() {
    container.listen(customObjectsProvider, (_, _) {});
    return container.read(customObjectsProvider.future);
  }

  group('customObjectsProvider', () {
    test('reads the answer', () async {
      client.body = _objectsBody;
      final answer = await readObjects();
      expect(answer!.offered, isTrue);
      expect(answer.objects.single.key, 'property');
    });

    test('a server without custom objects answers null', () async {
      client.status = 404;
      expect(await readObjects(), isNull);
    });

    test('a 500 is an error, not null', () async {
      client.status = 500;
      await expectLater(readObjects(), throwsException);
      expect(container.read(customObjectsProvider).hasError, isTrue);
    });

    test('a request that never arrived is an error, not null', () async {
      client.offline = true;
      await expectLater(readObjects(), throwsException);
      expect(container.read(customObjectsProvider).hasError, isTrue);
    });
  });

  group('reading the answer for display', () {
    const answer = CustomObjectsAnswer(hasCustomObjects: true);

    test('shows a loaded answer and nothing else', () {
      expect(shownCustomObjects(const AsyncData(answer)), same(answer));
      expect(shownCustomObjects(const AsyncData(null)), isNull);
      expect(shownCustomObjects(const AsyncLoading()), isNull);
      expect(
        shownCustomObjects(AsyncError(Exception('502'), StackTrace.empty)),
        isNull,
      );
    });

    test('a failure counts as failed until it is asked again', () {
      expect(customObjectsFailed(const AsyncData(answer)), isFalse);
      expect(customObjectsFailed(const AsyncLoading()), isFalse);
      expect(
        customObjectsFailed(AsyncError(Exception('502'), StackTrace.empty)),
        isTrue,
      );
    });
  });

  group('after an org switch', () {
    final org = NotifierProvider<_OrgSwitch, Organization?>(_OrgSwitch.new);
    late ProviderContainer scoped;
    const related = (to: 'lead', id: uuid);

    int relatedAsked() =>
        client.sent.where((r) => r.url.path == '/api/objects/related/').length;

    void switchTo(String? id) => scoped
        .read(org.notifier)
        .set(id == null ? null : Organization.fromJson({'id': id, 'name': id}));

    setUp(() async {
      scoped = ProviderContainer(
        overrides: [selectedOrgProvider.overrideWith((ref) => ref.watch(org))],
      );
      client.body = _objectsBody;
      client.routes['/api/objects/related/'] =
          '{"groups": [], "can_edit": true, "link_fields": []}';
      scoped.listen(customObjectsProvider, (_, _) {});
      scoped.listen(relatedProvider(related), (_, _) {});
      await _settle();
      expect(shownCustomObjects(scoped.read(customObjectsProvider)), isNotNull);
      expect(relatedAsked(), 1);
    });

    tearDown(() => scoped.dispose());

    test('a failed load shows nothing, though Riverpod keeps org A', () async {
      client.status = 502;
      switchTo('b');
      await _settle();

      final state = scoped.read(customObjectsProvider);
      expect(state.value, isNotNull, reason: 'the value this rule hides');
      expect(shownCustomObjects(state), isNull);
      expect(customObjectsFailed(state), isTrue);
      expect(await scoped.read(relatedProvider(related).future), isNull);
      expect(relatedAsked(), 1);
    });

    test('a load in flight shows nothing and asks no Related', () async {
      final gate = Completer<void>();
      client.gate = gate.future;
      switchTo('b');
      await _settle();

      final state = scoped.read(customObjectsProvider);
      expect(state.isLoading, isTrue);
      expect(state.value, isNotNull, reason: 'the value this rule hides');
      expect(shownCustomObjects(state), isNull);
      expect(customObjectsFailed(state), isFalse);
      expect(relatedAsked(), 1);

      client.status = 502;
      gate.complete();
      await _settle();
      expect(shownCustomObjects(scoped.read(customObjectsProvider)), isNull);
      expect(await scoped.read(relatedProvider(related).future), isNull);
      expect(relatedAsked(), 1);
    });

    test('sign-out shows nothing', () async {
      client.status = 401;
      switchTo(null);
      await _settle();

      expect(shownCustomObjects(scoped.read(customObjectsProvider)), isNull);
      expect(await scoped.read(relatedProvider(related).future), isNull);
      expect(relatedAsked(), 1);
    });
  });

  group('objectRecordsProvider paging', () {
    String page(int from, int n) => jsonEncode({
      'count': 60,
      'results': [
        for (var i = from; i < from + n; i++) {'id': 'r$i', 'name': 'N$i'},
      ],
    });

    test('two loadMore calls in a row fetch one page', () async {
      client.body = page(0, 20);
      final p = objectRecordsProvider('property');
      container.listen(p, (_, _) {});
      await container.read(p.future);
      client.sent.clear();

      final gate = Completer<void>();
      client.gate = gate.future;
      client.body = page(20, 20);
      final n = container.read(p.notifier);
      final a = n.loadMore();
      final b = n.loadMore();
      gate.complete();
      await Future.wait([a, b]);

      expect(client.sent, hasLength(1));
      final ids = container.read(p).value!.records.map((r) => r.id).toList();
      expect(ids, hasLength(40));
      expect(ids.toSet(), hasLength(40));
    });

    test(
      'a loadMore overtaken by setQuery does not change the new list',
      () async {
        client.body = page(0, 20);
        final p = objectRecordsProvider('property');
        container.listen(p, (_, _) {});
        await container.read(p.future);

        final gate = Completer<void>();
        client.gate = gate.future;
        client.body = page(20, 20);
        final more = container.read(p.notifier).loadMore();
        await Future<void>.delayed(Duration.zero);
        client.gate = null;
        client.body = jsonEncode({
          'count': 1,
          'results': [
            {'id': 'q1', 'name': 'Match'},
          ],
        });
        await container.read(p.notifier).setQuery('match');
        gate.complete();
        await more;

        final data = container.read(p).value!;
        expect(data.records.map((r) => r.id), ['q1']);
        expect(data.query, 'match');
      },
    );

    String one(String id) => jsonEncode({
      'count': 1,
      'results': [
        {'id': id, 'name': id},
      ],
    });

    test('an older search answering last leaves the newer results', () async {
      client.body = page(0, 20);
      final p = objectRecordsProvider('property');
      container.listen(p, (_, _) {});
      await container.read(p.future);
      final n = container.read(p.notifier);

      final first = Completer<void>();
      client.gate = first.future;
      client.body = one('older');
      final a = n.setQuery('par');
      await Future<void>.delayed(Duration.zero);

      final second = Completer<void>();
      client.gate = second.future;
      client.body = one('newer');
      final b = n.setQuery('park');
      await Future<void>.delayed(Duration.zero);

      second.complete();
      await b;
      first.complete();
      await a;

      final data = container.read(p).value!;
      expect(data.records.map((r) => r.id), ['newer']);
      expect(data.query, 'park');
    });

    test('a refresh answering after a newer search is dropped', () async {
      client.body = page(0, 20);
      final p = objectRecordsProvider('property');
      container.listen(p, (_, _) {});
      await container.read(p.future);
      final n = container.read(p.notifier);

      final first = Completer<void>();
      client.gate = first.future;
      client.body = one('refreshed');
      final a = n.refresh();
      await Future<void>.delayed(Duration.zero);

      client.gate = null;
      client.body = one('searched');
      await n.setQuery('park');
      first.complete();
      await a;

      final data = container.read(p).value!;
      expect(data.records.map((r) => r.id), ['searched']);
      expect(data.query, 'park');
    });
  });

  group('objectRecordsProvider after the screen closed', () {
    final page = jsonEncode({
      'count': 60,
      'results': [
        for (var i = 0; i < 20; i++) {'id': 'r$i', 'name': 'N$i'},
      ],
    });

    Future<void> closedDuring(
      Future<void> Function(ObjectRecordsNotifier n) act,
    ) async {
      client.body = page;
      final p = objectRecordsProvider('property');
      final sub = container.listen(p, (_, _) {});
      await container.read(p.future);
      final n = container.read(p.notifier);

      final gate = Completer<void>();
      client.gate = gate.future;
      final pending = act(n);
      await Future<void>.delayed(Duration.zero);
      sub.close();
      container.dispose();
      gate.complete();
      await pending;
    }

    test('loadMore finishes quietly', () async {
      await closedDuring((n) => n.loadMore());
    });

    test('setQuery finishes quietly', () async {
      await closedDuring((n) => n.setQuery('park'));
    });

    test('refresh finishes quietly', () async {
      await closedDuring((n) => n.refresh());
    });
  });

  group('a failed load shows its error at once, with no automatic retry', () {
    Future<void> failsOnce(ProviderListenable<AsyncValue<Object?>> p) async {
      client.status = 502;
      container.listen(p, (_, _) {});
      await _settle();
      final state = container.read(p);
      final asked = client.sent.length;
      expect(asked, isPositive);
      expect(state.hasError, isTrue);
      expect(state.isLoading, isFalse, reason: 'a retry is pending');
      await Future<void>.delayed(const Duration(milliseconds: 300));
      expect(client.sent, hasLength(asked));
    }

    test('objectDefinitionProvider', () async {
      await failsOnce(objectDefinitionProvider('property'));
    });

    test('objectSettingsProvider', () async {
      await failsOnce(objectSettingsProvider('property'));
    });

    test('objectRecordsProvider', () async {
      await failsOnce(objectRecordsProvider('property'));
    });
  });

  group('objectDefinitionProvider', () {
    test('a malformed key is not found and asks nothing', () async {
      final p = objectDefinitionProvider('../leads');
      container.listen(p, (_, _) {});
      expect(await container.read(p.future), isNull);
      expect(client.sent, isEmpty);
    });
  });

  group('relatedProvider', () {
    bool askedRelated() =>
        client.sent.any((r) => r.url.path.contains('/objects/related/'));

    test('sends no request when nothing is offered', () async {
      client.status = 404;
      await container.read(customObjectsProvider.future);
      expect(
        await container.read(relatedProvider((to: 'lead', id: uuid)).future),
        isNull,
      );
      expect(askedRelated(), isFalse);
    });

    test('sends no request while the answer is an error', () async {
      client.status = 500;
      await expectLater(readObjects(), throwsException);
      expect(
        await container.read(relatedProvider((to: 'lead', id: uuid)).future),
        isNull,
      );
      expect(askedRelated(), isFalse);
    });

    test('sends no request when the org has no objects', () async {
      client.body =
          '{"has_custom_objects": true, "objects": [], "link_targets": []}';
      await container.read(customObjectsProvider.future);
      expect(
        await container.read(relatedProvider((to: 'lead', id: uuid)).future),
        isNull,
      );
      expect(askedRelated(), isFalse);
    });

    test('reads the groups when the org has objects', () async {
      client.body = _objectsBody;
      client.routes['/api/objects/related/'] =
          '{"groups": [], "can_edit": true, "link_fields": []}';
      final p = relatedProvider((to: 'lead', id: uuid));
      container.listen(p, (_, _) {});
      await _settle();
      final answer = container.read(p).value;
      expect(answer!.canEdit, isTrue);
      final request = client.sent.last;
      expect(request.url.queryParameters, {'to': 'lead', 'id': uuid});
    });
  });

  group('recordWriteBody', () {
    final r = _record();
    List<String> assignees() => r.assignedTo.map((p) => p.id).toList();

    test('an unchanged edit sends only the name', () {
      final body = recordWriteBody(
        definition: _definition,
        name: r.name,
        customFields: r.customFields,
        links: {'enquiries': _visibleIds(r, 'enquiries')},
        assignees: assignees(),
        original: r,
      );
      expect(body, {'name': r.name});
    });

    test('a read-only one-record field is never sent', () {
      final body = recordWriteBody(
        definition: _definition,
        name: r.name,
        customFields: r.customFields,
        links: {'owner': []},
        assignees: assignees(),
        original: r,
      );
      expect(body.containsKey('links'), isFalse);
    });

    test('a cleared custom field is sent as null', () {
      final body = recordWriteBody(
        definition: _definition,
        name: r.name,
        customFields: {'price': 100, 'notes': ''},
        links: const {},
        assignees: assignees(),
        original: r,
      );
      expect(body['custom_fields'], {'notes': null});
    });

    test('removing an assignee sends the remaining ones', () {
      final body = recordWriteBody(
        definition: _definition,
        name: r.name,
        customFields: r.customFields,
        links: const {},
        assignees: ['p2'],
        original: r,
      );
      expect(body['assigned_to'], ['p2']);
    });

    test('a changed link set is sent for that field only', () {
      final body = recordWriteBody(
        definition: _definition,
        name: r.name,
        customFields: r.customFields,
        links: {
          'enquiries': ['l1', 'l9'],
        },
        assignees: assignees(),
        original: r,
      );
      expect(body['links'], {
        'enquiries': ['l1', 'l9'],
      });
    });

    test('a new record sends what it has and leaves empties out', () {
      final body = recordWriteBody(
        definition: _definition,
        name: 'New',
        customFields: {'price': 5, 'notes': ' '},
        links: {
          'enquiries': [],
          'owner': ['c1'],
        },
        assignees: const [],
      );
      expect(body, {
        'name': 'New',
        'custom_fields': {'price': 5},
        'links': {
          'owner': ['c1'],
        },
      });
    });
  });

  group('recordWriteError', () {
    ApiResponse<dynamic> refused(Map<String, dynamic> data) =>
        ApiResponse(success: false, data: data, message: 'x', statusCode: 400);

    test('names the refused field in a record error', () {
      final text = recordWriteError(
        refused({
          'name': ['This field may not be blank.'],
          'custom_fields': {'price': 'Enter a number.'},
          'links': {
            'owner': ['This field links to one record at most.'],
          },
        }),
        _definition,
      );
      expect(text.split('\n'), [
        'Address: This field may not be blank.',
        'Price: Enter a number.',
        'Owner: This field links to one record at most.',
      ]);
    });

    test('gives the size message alone, and detail as it is', () {
      expect(
        recordWriteError(
          refused({
            'custom_fields': {'_size': 'Too much data.'},
          }),
          _definition,
        ),
        'Too much data.',
      );
      expect(
        recordWriteError(refused({'detail': 'Not allowed.'}), _definition),
        'Not allowed.',
      );
    });

    test('falls back to the response message', () {
      expect(
        recordWriteError(
          const ApiResponse(success: false, message: 'Offline', statusCode: 0),
          _definition,
        ),
        'Offline',
      );
    });
  });

  group('settingsWriteError', () {
    ApiResponse<dynamic> refused(Map<String, dynamic> data) =>
        ApiResponse(success: false, statusCode: 400, data: data);

    test('names an object error by the label the form shows', () {
      final text = settingsWriteError(
        refused({
          'label_plural': ['Too long.'],
          'record_access': 'Not a choice.',
        }),
        'fallback',
        labels: objectFormLabels,
      );
      expect(
        text,
        'Name (plural): Too long.\nWho can see its records: Not a choice.',
      );
    });

    test('names a field error by the label the form shows', () {
      final text = settingsWriteError(
        refused({
          'is_required': ['Bad.'],
          'target': ['Unknown.'],
          'surprise': ['Odd.'],
        }),
        'fallback',
        labels: fieldFormLabels,
      );
      expect(text, 'Required: Bad.\nLinks to: Unknown.\nsurprise: Odd.');
    });
  });

  group('displayValue', () {
    const dropdown = ObjectField(
      key: 'stage',
      label: 'Stage',
      fieldType: 'dropdown',
      options: [CustomFieldOption(value: 'hot', label: 'Hot lead')],
    );
    const text = ObjectField(key: 'n', label: 'N', fieldType: 'text');

    test('a dropdown shows its label, or itself when the option is gone', () {
      expect(displayValue(dropdown, 'hot'), 'Hot lead');
      expect(displayValue(dropdown, 'retired'), 'retired');
    });

    test('checkbox, empty and plain values', () {
      const box = ObjectField(key: 'b', label: 'B', fieldType: 'checkbox');
      expect(displayValue(box, true), 'Yes');
      expect(displayValue(box, false), 'No');
      expect(displayValue(text, null), 'None');
      expect(displayValue(text, '  '), 'None');
      expect(displayValue(text, 'quiet'), 'quiet');
      expect(displayValue(text, 12), '12');
    });
  });

  group('RelatedGroup', () {
    test('names its object by the singular label', () {
      final group = RelatedGroup.fromJson({
        'object': {
          'key': 'property',
          'label': 'Property',
          'label_plural': 'Properties',
        },
        'field': {'key': 'agent', 'label': 'Agent'},
        'records': const [],
      });
      expect(group.objectLabel, 'Property');
    });
  });

  group('CustomObjectsApi', () {
    test('saves a record with PATCH', () async {
      await container.read(customObjectsApiProvider).updateRecord(
        'property',
        uuid,
        {'name': 'x'},
      );
      expect(client.sent.single.method, 'PATCH');
      expect(
        client.sent.single.url.path,
        '/api/objects/property/records/$uuid/',
      );
    });

    test('searches each kind through its list endpoint', () async {
      const cases = {
        'lead': (
          '/api/leads/',
          '{"open_leads": {"open_leads": [{"id": "1", "first_name": "Lee", "last_name": "Fox"}]}}',
          'Lee Fox',
        ),
        'contact': (
          '/api/contacts/',
          '{"results": [{"id": "1", "first_name": "Cy", "last_name": "Dunn"}]}',
          'Cy Dunn',
        ),
        'account': (
          '/api/accounts/',
          '{"active_accounts": {"open_accounts": [{"id": "1", "name": "Acme"}]}}',
          'Acme',
        ),
        'deal': (
          '/api/opportunities/',
          '{"opportunities": [{"id": "1", "name": "Big deal"}]}',
          'Big deal',
        ),
        'ticket': (
          '/api/cases/',
          '{"cases": [{"id": "1", "name": "Broken tap"}]}',
          'Broken tap',
        ),
        'task': (
          '/api/tasks/',
          '{"tasks": [{"id": "1", "title": "Call back"}]}',
          'Call back',
        ),
        'obj:property': (
          '/api/objects/property/records/',
          '{"count": 1, "results": [{"id": "1", "name": "12 Park Lane"}]}',
          '12 Park Lane',
        ),
      };
      for (final e in cases.entries) {
        client.sent.clear();
        client.body = e.value.$2;
        final found = await container
            .read(customObjectsApiProvider)
            .searchTargets(e.key, '12 Park');
        final request = client.sent.single;
        expect(request.url.path, e.value.$1, reason: e.key);
        final param = e.key.startsWith('obj:') ? 'q' : 'search';
        expect(request.url.queryParameters[param], '12 Park', reason: e.key);
        expect(request.url.queryParameters['limit'], '20', reason: e.key);
        expect(found.single.name, e.value.$3, reason: e.key);
        expect(found.single.object, e.key);
      }
    });

    test('a failed search throws instead of finding nothing', () async {
      client.status = 500;
      await expectLater(
        container.read(customObjectsApiProvider).searchTargets('lead', 'x'),
        throwsException,
      );
      client.status = 200;
      client.offline = true;
      await expectLater(
        container.read(customObjectsApiProvider).searchTargets('lead', 'x'),
        throwsException,
      );
    });

    test('finds nothing for an unknown kind without a request', () async {
      final found = await container
          .read(customObjectsApiProvider)
          .searchTargets('invoice', 'x');
      expect(found, isEmpty);
      expect(client.sent, isEmpty);
    });

    test(
      'finds nothing for a malformed object key without a request',
      () async {
        final found = await container
            .read(customObjectsApiProvider)
            .searchTargets('obj:Bad Key', 'x');
        expect(found, isEmpty);
        expect(client.sent, isEmpty);
      },
    );
  });

  group('objectRecordsProvider', () {
    test('pages by 20 and appends on loadMore', () async {
      client.routes['/api/objects/property/records/'] =
          '{"count": 21, "results": [{"id": "$uuid", "name": "A"}]}';
      final provider = objectRecordsProvider('property');
      container.listen(provider, (_, _) {});
      final first = await container.read(provider.future);
      expect(first.hasMore, isTrue);
      expect(client.sent.last.url.queryParameters['limit'], '20');
      await container.read(provider.notifier).loadMore();
      expect(client.sent.last.url.queryParameters['offset'], '1');
      expect(container.read(provider).value!.records, hasLength(2));
    });

    test('a search sends q', () async {
      client.body = '{"count": 0, "results": []}';
      final provider = objectRecordsProvider('property');
      container.listen(provider, (_, _) {});
      await container.read(provider.future);
      await container.read(provider.notifier).setQuery('park');
      expect(client.sent.last.url.queryParameters['q'], 'park');
    });
  });
}
