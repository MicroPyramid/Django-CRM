import 'dart:async';
import 'dart:convert';

import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class _Req {
  _Req(this.method, this.url, this.body);
  final String method;
  final Uri url;
  final String body;
}

class _FakeClient extends http.BaseClient {
  final List<_Req> sent = [];
  // Keyed by "METHOD path".
  final Map<String, (int, String)> routes = {};
  // A route listed here answers only once its completer does.
  final Map<String, Completer<void>> holds = {};

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final body = utf8.decode(await request.finalize().toBytes());
    sent.add(_Req(request.method, request.url, body));
    await holds['${request.method} ${request.url.path}']?.future;
    final (status, text) =
        routes['${request.method} ${request.url.path}'] ?? (200, '{}');
    return http.StreamedResponse(
      Stream.value(utf8.encode(text)),
      status,
      request: request,
    );
  }
}

class _OrgNotifier extends Notifier<Organization?> {
  @override
  Organization? build() => const Organization(id: 'org-1', name: 'One');

  void set(Organization? o) => state = o;
}

const _a = '11111111-1111-4111-8111-111111111111';
const _b = '22222222-2222-4222-8222-222222222222';
const _c = '33333333-3333-4333-8333-333333333333';

String _row(String id, String name) =>
    '{"id":"$id","name":"$name","object_key":"lead","is_active":false}';

String _list(String org) =>
    '{"summary":"$org","results":[${_row(_a, 'A')},${_row(_b, 'B')},${_row(_c, 'C')}]}';

void main() {
  late _FakeClient client;
  late ProviderContainer container;
  late NotifierProvider<_OrgNotifier, Organization?> orgState;

  setUp(() {
    client = _FakeClient();
    ApiService().setClientForTesting(client);
    orgState = NotifierProvider<_OrgNotifier, Organization?>(_OrgNotifier.new);
    container = ProviderContainer(
      overrides: [
        selectedOrgProvider.overrideWith((ref) => ref.watch(orgState)),
      ],
    );
    client.routes['GET /api/automation/rules/'] = (200, _list('one'));
  });

  tearDown(() => container.dispose());

  List<_Req> posts() => client.sent.where((r) => r.method == 'POST').toList();

  test('loads the catalogue, the rules and one rule from their urls', () async {
    client.routes['GET /api/automation/catalogue/'] = (
      200,
      '{"objects":[],"actions":["notify"],"limits":{"conditions":5,"actions":2}}',
    );
    client.routes['GET /api/automation/rules/$_a/'] = (200, _row(_a, 'Solo'));

    final cat = await container.read(automationCatalogueProvider.future);
    expect(cat.maxConditions, 5);
    final rules = await container.read(automationRulesProvider.future);
    expect(rules.summary, 'one');
    expect(rules.rules.map((r) => r.id), [_a, _b, _c]);
    final rule = await container.read(automationRuleProvider(_a).future);
    expect(rule.name, 'Solo');
    expect(
      client.sent.map((r) => r.url.path),
      containsAll([
        '/api/automation/catalogue/',
        '/api/automation/rules/',
        '/api/automation/rules/$_a/',
      ]),
    );
  });

  test('an API without automation answers not offered', () async {
    client.routes['GET /api/automation/rules/'] = (
      404,
      '{"detail":"Not found."}',
    );
    container.listen(automationRulesProvider, (_, _) {});
    await expectLater(
      container.read(automationRulesProvider.future),
      throwsA(isA<AutomationNotOffered>()),
    );
    expect(
      automationNotOffered(container.read(automationRulesProvider)),
      isTrue,
    );
    expect(
      const AutomationNotOffered().toString(),
      'Automation rules are not available here.',
    );
  });

  test('any other failure is not read as not offered', () async {
    client.routes['GET /api/automation/rules/'] = (500, '{"detail":"boom"}');
    container.listen(automationRulesProvider, (_, _) {});
    await expectLater(
      container.read(automationRulesProvider.future),
      throwsA(isNot(isA<AutomationNotOffered>())),
    );
    expect(
      automationNotOffered(container.read(automationRulesProvider)),
      isFalse,
    );
  });

  test('a failed load is an error, not an empty answer', () async {
    client.routes['GET /api/automation/rules/'] = (500, '{"detail":"boom"}');
    await expectLater(
      container.read(automationRulesProvider.future),
      throwsA(isA<Exception>()),
    );
  });

  test('loads runs at an offset of 20', () async {
    client.routes['GET /api/automation/rules/$_a/runs/'] = (
      200,
      '{"count":45,"results":[]}',
    );
    final page = await container.read(
      automationRunsProvider((id: _a, offset: 20)).future,
    );
    expect(page.count, 45);
    expect(page.offset, 20);
    final req = client.sent.last;
    expect(req.url.queryParameters['offset'], '20');
    expect(req.url.queryParameters['limit'], '20');
  });

  test(
    'moves a rule by posting the whole order, and refuses the ends without a request',
    () async {
      client.routes['POST /api/automation/rules/reorder/'] = (200, '{}');
      await container.read(automationRulesProvider.future);
      final n = container.read(automationRulesProvider.notifier);
      final gets = client.sent.length;

      expect(await n.move(_a, 'up'), isNotNull);
      expect(await n.move(_c, 'down'), isNotNull);
      expect(await n.move('nope', 'up'), isNotNull);
      expect(await n.move(_b, 'sideways'), isNotNull);
      expect(client.sent.length, gets);

      expect(await n.move(_b, 'up'), isNull);
      final post = posts().single;
      expect(jsonDecode(post.body), {
        'ids': [_b, _a, _c],
      });
      // The refresh after success is the only extra GET.
      await container.read(automationRulesProvider.future);
      expect(client.sent.where((r) => r.method == 'GET').length, 2);
    },
  );

  test('a refused move answers the response message', () async {
    client.routes['POST /api/automation/rules/reorder/'] = (
      400,
      '{"detail":"Stale order."}',
    );
    await container.read(automationRulesProvider.future);
    final msg = await container
        .read(automationRulesProvider.notifier)
        .move(_a, 'down');
    expect(msg, 'Stale order.');
  });

  test(
    'creates and updates with the body it is given, and reads the errors of a 400',
    () async {
      final api = container.read(automationApiProvider);
      client.routes['POST /api/automation/rules/'] = (201, _row(_a, 'Made'));
      final made = await api.create({'name': 'Made'});
      expect(made.rule?.id, _a);
      expect(made.errors, isNull);
      expect(jsonDecode(posts().single.body), {'name': 'Made'});

      client.routes['PATCH /api/automation/rules/$_a/'] = (
        200,
        _row(_a, 'Renamed'),
      );
      final updated = await api.update(_a, {'name': 'Renamed'});
      expect(updated.rule?.name, 'Renamed');
      expect(jsonDecode(client.sent.last.body), {'name': 'Renamed'});

      client.routes['PATCH /api/automation/rules/$_a/'] = (
        400,
        '{"errors":{"name":["Required."]}}',
      );
      final bad = await api.update(_a, {'name': ''});
      expect(bad.rule, isNull);
      expect(bad.errors?.rows['name'], 'Required.');

      client.routes['POST /api/automation/rules/'] = (
        403,
        '{"code":"plan_limit","detail":"Cap."}',
      );
      final capped = await api.create({'name': 'X'});
      expect(capped.rule, isNull);
      expect(capped.errors?.general, isNotEmpty);
    },
  );

  test('switches off with is_active false only', () async {
    client.routes['PATCH /api/automation/rules/$_a/'] = (200, _row(_a, 'A'));
    final api = container.read(automationApiProvider);
    expect(await api.switchOff(_a), isNull);
    expect(jsonDecode(client.sent.last.body), {'is_active': false});

    client.routes['PATCH /api/automation/rules/$_a/'] = (
      500,
      '{"detail":"No."}',
    );
    expect(await api.switchOff(_a), isNotNull);
  });

  test('deletes on a 204 and reports a failure', () async {
    final api = container.read(automationApiProvider);
    client.routes['DELETE /api/automation/rules/$_a/'] = (204, '');
    expect(await api.delete(_a), isNull);
    client.routes['DELETE /api/automation/rules/$_a/'] = (
      403,
      '{"detail":"Admins only."}',
    );
    expect(await api.delete(_a), 'Admins only.');
  });

  test('tries with record_id and turns a 404 into the record sentence', () async {
    final api = container.read(automationApiProvider);
    client.routes['POST /api/automation/rules/$_a/try/'] = (
      200,
      '{"steps":[{"action":0,"type":"notify","status":"ok","text":"Would notify"}]}',
    );
    final ok = await api.tryRule(_a, 'rec-1');
    expect(ok.error, isNull);
    expect(ok.steps.single.text, 'Would notify');
    expect(jsonDecode(client.sent.last.body), {'record_id': 'rec-1'});

    client.routes['POST /api/automation/rules/$_a/try/'] = (
      404,
      '{"detail":"No such record."}',
    );
    final missing = await api.tryRule(_a, 'rec-2');
    expect(missing.steps, isEmpty);
    expect(missing.error, 'That record does not exist, or you cannot open it.');
  });

  test(
    'tries: a non-404 failure gives the server message or a fallback',
    () async {
      final api = container.read(automationApiProvider);
      client.routes['POST /api/automation/rules/$_a/try/'] = (
        400,
        '{"detail":"Rule is invalid."}',
      );
      final bad = await api.tryRule(_a, 'rec-1');
      expect(bad.steps, isEmpty);
      expect(bad.error, 'Rule is invalid.');

      client.routes['POST /api/automation/rules/$_a/try/'] = (500, '{}');
      final down = await api.tryRule(_a, 'rec-1');
      expect(down.error, isNotEmpty);
    },
  );

  test(
    'drops the old org rules when the org changes, and on sign-out',
    () async {
      expect(
        (await container.read(automationRulesProvider.future)).summary,
        'one',
      );

      client.routes['GET /api/automation/rules/'] = (200, _list('two'));
      client.holds['GET /api/automation/rules/'] = Completer<void>();
      container
          .read(orgState.notifier)
          .set(const Organization(id: 'org-2', name: 'Two'));
      // Mid-load the old value is still held, but nothing shows it.
      final mid = container.read(automationRulesProvider);
      expect(mid.isLoading, isTrue);
      expect(shownAutomationRules(mid), isNull);
      final gets = client.sent.length;
      final n = container.read(automationRulesProvider.notifier);
      expect(await n.move(_a, 'down'), 'The rules are still loading.');
      expect(client.sent.length, gets);

      client.holds.remove('GET /api/automation/rules/')!.complete();
      final after = await container.read(automationRulesProvider.future);
      expect(after.summary, 'two');
      expect(
        shownAutomationRules(container.read(automationRulesProvider)),
        isNotNull,
      );

      client.routes['GET /api/automation/rules/'] = (200, _list('none'));
      container.read(orgState.notifier).set(null);
      expect(
        (await container.read(automationRulesProvider.future)).summary,
        'none',
      );
    },
  );

  test('a failed load shows nothing and move sends nothing', () async {
    client.routes['GET /api/automation/rules/'] = (500, '{}');
    await expectLater(
      container.read(automationRulesProvider.future),
      throwsA(isA<Exception>()),
    );
    final state = container.read(automationRulesProvider);
    expect(shownAutomationRules(state), isNull);
    final n = container.read(automationRulesProvider.notifier);
    final sent = client.sent.length;
    expect(await n.move(_a, 'down'), isNotNull);
    expect(client.sent.length, sent);
  });

  test('refuses a second move while one is in flight', () async {
    client.routes['POST /api/automation/rules/reorder/'] = (200, '{}');
    await container.read(automationRulesProvider.future);
    final n = container.read(automationRulesProvider.notifier);
    client.holds['POST /api/automation/rules/reorder/'] = Completer<void>();

    final first = n.move(_a, 'down');
    await Future<void>.delayed(Duration.zero);
    expect(await n.move(_b, 'down'), 'A move is already in progress.');
    expect(posts().length, 1);

    client.holds.remove('POST /api/automation/rules/reorder/')!.complete();
    expect(await first, isNull);
    // Free again once the first has finished.
    expect(await n.move(_a, 'down'), isNull);
  });

  test('declaring the providers sends nothing', () {
    container.read(automationApiProvider);
    expect(client.sent, isEmpty);
  });
}
