import 'dart:async';
import 'dart:convert';

import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/org_module.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/org_modules_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class _FakeClient extends http.BaseClient {
  int status = 200;
  String body = '{}';
  final List<http.BaseRequest> sent = [];
  final List<String> bodies = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    bodies.add(utf8.decode(await request.finalize().toBytes()));
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

const _groups = {
  'deals': 'sell',
  'leads': 'sell',
  'goals': 'sell',
  'tasks': 'serve',
  'tickets': 'serve',
  'knowledge_base': 'serve',
  'documents': 'serve',
  'invoices': 'bill',
  'timesheet': 'bill',
};

Map<String, dynamic> _row(
  String key, {
  bool enabled = true,
  bool? available,
  String? needs,
  String? label,
}) => {
  'key': key,
  'label': label ?? defaultModuleLabels[key],
  'group': _groups[key],
  'covers': 'Covers $key.',
  'stops': 'Stops $key.',
  'enabled': enabled,
  'available': available ?? enabled,
  'needs': needs,
};

Map<String, dynamic> _json({
  Set<String> off = const {},
  List<String>? order,
  bool canEdit = true,
}) => {
  'modules': [
    for (final k in order ?? _groups.keys)
      _row(
        k,
        enabled: !off.contains(k),
        needs: k == 'goals' ? 'deals' : (k == 'timesheet' ? 'tickets' : null),
      ),
  ],
  'can_edit': canEdit,
};

OrgModulesAnswer _answer({Set<String> off = const {}, List<String>? order}) =>
    OrgModulesAnswer.fromJson(
      _json(off: off, order: order),
      orgId: 'a',
    );

class _GateClient extends _FakeClient {
  final Completer<void> gate;
  _GateClient(this.gate);

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    await gate.future;
    return super.send(request);
  }
}

class _OrgSwitch extends Notifier<Organization?> {
  @override
  Organization? build() => null;
  void set(Organization? next) => state = next;
}

void main() {
  late _FakeClient client;
  late ProviderContainer container;

  setUp(() {
    client = _FakeClient();
    ApiService().setClientForTesting(client);
    container = ProviderContainer();
  });

  tearDown(() => container.dispose());

  group('OrgModulesAnswer', () {
    test(
      'reads the nine rows in order with label, group, covers, stops and needs',
      () {
        final a = _answer();
        expect(a.modules.map((m) => m.key), _groups.keys.toList());
        final goals = a.modules[2];
        expect(goals.label, 'Goals');
        expect(goals.group, 'sell');
        expect(goals.covers, 'Covers goals.');
        expect(goals.stops, 'Stops goals.');
        expect(goals.needs, 'deals');
        expect(a.modules.first.needs, isNull);
        expect(a.canEdit, isTrue);
        expect(a.orgId, 'a');
      },
    );

    test('survives missing and wrongly typed keys without throwing', () {
      expect(OrgModulesAnswer.fromJson({}).modules, isEmpty);
      expect(OrgModulesAnswer.fromJson({'modules': 'x'}).modules, isEmpty);
      final a = OrgModulesAnswer.fromJson({
        'modules': [
          'junk',
          {'label': 'no key'},
          {'key': 7},
          {'key': 'leads', 'label': 3, 'enabled': 'yes', 'needs': 4},
        ],
        'can_edit': 'true',
      });
      expect(a.modules.single.key, 'leads');
      expect(a.modules.single.label, 'Leads');
      expect(a.modules.single.enabled, isTrue);
      expect(a.modules.single.needs, isNull);
      expect(a.canEdit, isFalse);
    });

    test(
      'reads a module as on when available, when it has no row, and when the answer is for another org',
      () {
        final a = OrgModulesAnswer.fromJson({
          'modules': [
            _row('deals', enabled: false),
            _row('goals', available: false, needs: 'deals'),
            _row('leads'),
          ],
        }, orgId: 'a');
        expect(a.isOn('deals'), isFalse);
        expect(a.isOn('goals'), isFalse);
        expect(a.isOn('leads'), isTrue);
        expect(a.isOn('tickets'), isTrue);
        expect(a.productsOn, isTrue);
        expect(a.labelOf('deals'), 'Pipeline');
        expect(a.labelOf('tickets'), 'Tickets');

        final value = AsyncData<OrgModulesAnswer?>(a);
        expect(moduleIsOn(value, 'a', 'deals'), isFalse);
        expect(moduleIsOn(value, 'b', 'deals'), isTrue);
        expect(moduleIsOn(const AsyncData(null), 'a', 'deals'), isTrue);
        expect(moduleIsOn(const AsyncLoading(), 'a', 'deals'), isTrue);
        expect(
          moduleIsOn(
            AsyncError(Exception('x'), StackTrace.empty),
            'a',
            'deals',
          ),
          isTrue,
        );
      },
    );

    test('productsOn is true while either deals or invoices is on', () {
      expect(_answer(off: {'deals'}).productsOn, isTrue);
      expect(_answer(off: {'deals', 'invoices'}).productsOn, isFalse);
    });

    test('switches one module and keeps the served order', () {
      final a = _answer(
        off: {'tickets'},
        order: [
          'goals',
          'leads',
          'deals',
          'documents',
          'tasks',
          'tickets',
          'knowledge_base',
          'timesheet',
          'invoices',
        ],
      );
      final order = [for (final m in a.modules) m.key];
      final off = a.switchBody('leads', false)!;
      expect(off.off, ['leads', 'tickets']);
      expect(off.order, order);
      final on = a.switchBody('tickets', true)!;
      expect(on.off, isEmpty);
      expect(on.order, order);
      expect(a.switchBody('crm', true), isNull);
    });

    test('moves within a group and stops at the ends', () {
      final a = _answer(off: {'goals'});
      final up = a.moveBody('leads', 'up')!;
      expect(up.order.take(3), ['leads', 'deals', 'goals']);
      expect(up.order.skip(3), a.modules.skip(3).map((m) => m.key));
      expect(up.off, ['goals']);
      expect(a.moveBody('leads', 'down')!.order.take(3), [
        'deals',
        'goals',
        'leads',
      ]);
      expect(a.moveBody('deals', 'up'), isNull);
      expect(a.moveBody('goals', 'down'), isNull);
      expect(a.moveBody('tasks', 'up'), isNull);
      expect(a.moveBody('documents', 'down'), isNull);
      expect(a.moveBody('invoices', 'up'), isNull);
      expect(a.moveBody('timesheet', 'up')!.order.skip(7), [
        'timesheet',
        'invoices',
      ]);
      expect(a.moveBody('crm', 'up'), isNull);
      expect(a.moveBody('leads', 'sideways'), isNull);
    });
  });

  group('orgModulesProvider', () {
    Future<OrgModulesAnswer?> read() {
      container.listen(orgModulesProvider, (_, _) {});
      return container.read(orgModulesProvider.future);
    }

    test(
      'loads for the selected org, reads 404 as null and 500 as an error',
      () async {
        final org = NotifierProvider<_OrgSwitch, Organization?>(_OrgSwitch.new);
        final scoped = ProviderContainer(
          overrides: [
            selectedOrgProvider.overrideWith((ref) => ref.watch(org)),
          ],
        );
        addTearDown(scoped.dispose);
        scoped
            .read(org.notifier)
            .set(Organization.fromJson({'id': 'a', 'name': 'A'}));
        client.body = jsonEncode(_json(off: {'deals'}));
        scoped.listen(orgModulesProvider, (_, _) {});
        final answer = await scoped.read(orgModulesProvider.future);
        expect(answer!.orgId, 'a');
        expect(client.sent.single.url.path, '/api/org/modules/');
        expect(scoped.read(moduleOnProvider('deals')), isFalse);
        expect(scoped.read(moduleOnProvider('leads')), isTrue);
        expect(scoped.read(productsOnProvider), isTrue);
        expect(scoped.read(shownModulesProvider), isNotNull);

        client.status = 404;
        scoped.invalidate(orgModulesProvider);
        expect(await scoped.read(orgModulesProvider.future), isNull);
        expect(scoped.read(shownModulesProvider), isNull);
        expect(scoped.read(moduleOnProvider('deals')), isTrue);

        client.status = 500;
        client.body = '{}';
        scoped.invalidate(orgModulesProvider);
        await expectLater(
          scoped.read(orgModulesProvider.future),
          throwsA(isA<Exception>()),
        );
        expect(scoped.read(shownModulesProvider), isNull);
        expect(scoped.read(moduleOnProvider('deals')), isTrue);
      },
    );

    test(
      'a reload for the same org keeps the off module off while loading',
      () async {
        client.body = jsonEncode(_json(off: {'deals'}));
        container.read(selectedOrgProvider);
        await read();
        final orgId = container.read(orgModulesProvider).value!.orgId;
        final gate = Completer<void>();
        final slow = _GateClient(gate)..body = client.body;
        ApiService().setClientForTesting(slow);
        container.invalidate(orgModulesProvider);
        container.read(orgModulesProvider);
        expect(container.read(orgModulesProvider).isLoading, isTrue);
        expect(
          moduleIsOn(container.read(orgModulesProvider), orgId, 'deals'),
          isFalse,
        );
        gate.complete();
        await container.read(orgModulesProvider.future);
      },
    );

    test('an error after a successful load keeps the last answer', () async {
      client.body = jsonEncode(_json(off: {'deals'}));
      await read();
      final orgId = container.read(orgModulesProvider).value!.orgId;
      client.status = 500;
      client.body = '{}';
      container.invalidate(orgModulesProvider);
      await expectLater(
        container.read(orgModulesProvider.future),
        throwsA(isA<Exception>()),
      );
      final value = container.read(orgModulesProvider);
      expect(value.hasError, isTrue);
      expect(moduleIsOn(value, orgId, 'deals'), isFalse);
    });

    test(
      'an org switch during a reload reads as all on until the new org answers',
      () async {
        final org = NotifierProvider<_OrgSwitch, Organization?>(_OrgSwitch.new);
        final scoped = ProviderContainer(
          overrides: [
            selectedOrgProvider.overrideWith((ref) => ref.watch(org)),
          ],
        );
        addTearDown(scoped.dispose);
        scoped
            .read(org.notifier)
            .set(Organization.fromJson({'id': 'a', 'name': 'A'}));
        client.body = jsonEncode(_json(off: {'deals'}));
        scoped.listen(orgModulesProvider, (_, _) {});
        await scoped.read(orgModulesProvider.future);
        expect(scoped.read(moduleOnProvider('deals')), isFalse);

        final gate = Completer<void>();
        ApiService().setClientForTesting(_GateClient(gate)..body = client.body);
        scoped
            .read(org.notifier)
            .set(Organization.fromJson({'id': 'b', 'name': 'B'}));
        scoped.read(orgModulesProvider);
        expect(scoped.read(orgModulesProvider).isLoading, isTrue);
        expect(scoped.read(moduleOnProvider('deals')), isTrue);
        expect(scoped.read(shownModulesProvider), isNull);
        gate.complete();
        await scoped.read(orgModulesProvider.future);
        expect(scoped.read(moduleOnProvider('deals')), isFalse);
      },
    );

    test(
      'save returns every refusal, off first, and keeps the state',
      () async {
        client.body = jsonEncode(_json());
        final before = await read();
        client.status = 400;
        client.body = jsonEncode({
          'order': ['Name each module once.'],
          'off': ['Goals needs Pipeline.', 'Tickets still receives email.'],
        });
        final notifier = container.read(orgModulesProvider.notifier);
        final errors = await notifier.save(off: ['deals'], order: ['leads']);
        expect(errors, [
          'Goals needs Pipeline.',
          'Tickets still receives email.',
          'Name each module once.',
        ]);
        expect(jsonDecode(client.bodies.last), {
          'off': ['deals'],
          'order': ['leads'],
        });
        expect(client.sent.last.method, 'PUT');
        expect(container.read(orgModulesProvider).value, same(before));

        client.status = 500;
        client.body = '{}';
        final other = await notifier.save(off: [], order: []);
        expect(other, hasLength(1));
        expect(other.single, isNotEmpty);
        expect(container.read(orgModulesProvider).value, same(before));
      },
    );

    test('save takes the new answer as its state', () async {
      client.body = jsonEncode(_json());
      await read();
      client.body = jsonEncode(_json(off: {'tickets'}));
      final errors = await container
          .read(orgModulesProvider.notifier)
          .save(off: ['tickets'], order: []);
      expect(errors, isEmpty);
      final now = container.read(orgModulesProvider).value!;
      expect(now.isOn('tickets'), isFalse);
      expect(now.isOn('leads'), isTrue);
    });
  });
}
