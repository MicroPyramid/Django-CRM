import 'dart:async';
import 'dart:convert';

import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/screens/objects/object_record_form_screen.dart';
import 'package:bottle_crm/screens/objects/object_records_screen.dart';
import 'package:bottle_crm/screens/settings/more_screen.dart';
import 'package:bottle_crm/screens/settings/object_settings_screen.dart';
import 'package:bottle_crm/screens/settings/settings_hub_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

/// After an org switch or a sign-out, Riverpod keeps the previous org's
/// objects answer as the value of both the reload and a failed load. None of
/// it may reach the screen.

const _orgABody = '''
{"has_custom_objects": true,
 "objects": [{"key": "property", "label": "Property", "label_plural": "Properties"}],
 "link_targets": [{"key": "contact", "label": "Contact", "label_plural": "Contacts"}]}
''';

class _FakeClient extends http.BaseClient {
  int status = 200;
  String body = _orgABody;
  Completer<void>? gate;
  final List<http.BaseRequest> sent = [];

  int get objectsAsked =>
      sent.where((r) => r.url.path == '/api/objects/').length;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    final wait = gate?.future;
    if (wait != null) await wait;
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

class _OrgSwitch extends Notifier<Organization?> {
  @override
  Organization? build() => Organization.fromJson({'id': 'a', 'name': 'A'});

  void set(Organization? next) => state = next;
}

final _org = NotifierProvider<_OrgSwitch, Organization?>(_OrgSwitch.new);

const _summary = ObjectSummary(
  key: 'property',
  label: 'Property',
  labelPlural: 'Properties',
);

const _definition = ObjectDefinition(summary: _summary);

class _NoRecords extends ObjectRecordsNotifier {
  _NoRecords(super.key);

  @override
  Future<ObjectRecordsData> build() async => const ObjectRecordsData();
}

/// Each screen, and what it shows only because of org A's answer.
final _screens = <String, ({Widget home, List<String> orgA})>{
  'More': (home: const MoreScreen(), orgA: ['OBJECTS', 'Properties']),
  'the settings hub': (home: const SettingsHubScreen(), orgA: ['Objects']),
  'the records list': (
    home: const ObjectRecordsScreen(objectKey: 'property'),
    orgA: ['New Property'],
  ),
  'the record form': (
    home: const ObjectRecordFormScreen(objectKey: 'property'),
    orgA: ['Save'],
  ),
  'the object settings screen': (
    home: const ObjectSettingsScreen(objectKey: 'property'),
    orgA: ['Add field'],
  ),
};

void _expectShown(List<String> texts, Matcher matcher) {
  for (final text in texts) {
    expect(find.text(text), matcher, reason: text);
  }
}

void main() {
  late _FakeClient client;

  setUp(() {
    client = _FakeClient();
    ApiService().setClientForTesting(client);
  });

  tearDown(() => ApiService().setClientForTesting(http.Client()));

  Future<ProviderContainer> showOrgA(WidgetTester tester, Widget home) async {
    tester.view.physicalSize = const Size(800, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final container = ProviderContainer(
      overrides: [
        selectedOrgProvider.overrideWith((ref) => ref.watch(_org)),
        isOrgAdminProvider.overrideWithValue(true),
        objectDefinitionProvider.overrideWith((ref, key) async => _definition),
        objectSettingsProvider('property').overrideWith(
          (ref) async => const ObjectSettingsData(summary: _summary),
        ),
        objectRecordsProvider(
          'property',
        ).overrideWith(() => _NoRecords('property')),
        usersProvider.overrideWithValue(const []),
      ],
    );
    addTearDown(container.dispose);
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(home: home),
      ),
    );
    await tester.pumpAndSettle();
    return container;
  }

  void switchTo(ProviderContainer container, String? id) => container
      .read(_org.notifier)
      .set(id == null ? null : Organization.fromJson({'id': id, 'name': id}));

  for (final screen in _screens.entries) {
    testWidgets('${screen.key} shows nothing of org A after org B fails', (
      tester,
    ) async {
      final container = await showOrgA(tester, screen.value.home);
      _expectShown(screen.value.orgA, findsOneWidget);

      client.status = 502;
      switchTo(container, 'b');
      await tester.pumpAndSettle();

      expect(client.objectsAsked, 2);
      _expectShown(screen.value.orgA, findsNothing);
    });

    testWidgets('${screen.key} shows nothing of org A while org B loads', (
      tester,
    ) async {
      final container = await showOrgA(tester, screen.value.home);
      _expectShown(screen.value.orgA, findsOneWidget);

      client.gate = Completer<void>();
      switchTo(container, 'b');
      await tester.pump();
      // Long enough for a removed button's exit animation, still mid-load.
      await tester.pump(const Duration(milliseconds: 500));

      expect(client.objectsAsked, 2, reason: 'org B was never asked');
      _expectShown(screen.value.orgA, findsNothing);

      client.status = 502;
      client.gate!.complete();
      await tester.pumpAndSettle();
      _expectShown(screen.value.orgA, findsNothing);
    });

    testWidgets('${screen.key} shows nothing after sign-out', (tester) async {
      final container = await showOrgA(tester, screen.value.home);
      _expectShown(screen.value.orgA, findsOneWidget);

      client.status = 401;
      switchTo(container, null);
      await tester.pumpAndSettle();

      expect(client.objectsAsked, 2);
      _expectShown(screen.value.orgA, findsNothing);
    });
  }

  testWidgets('the record form says the answer could not be loaded', (
    tester,
  ) async {
    final container = await showOrgA(
      tester,
      const ObjectRecordFormScreen(objectKey: 'property'),
    );

    client.status = 502;
    switchTo(container, 'b');
    await tester.pumpAndSettle();

    expect(find.text(objectsLoadFailedNotice), findsOneWidget);
    expect(find.text(objectsTurnedOffNotice), findsNothing);
  });
}
