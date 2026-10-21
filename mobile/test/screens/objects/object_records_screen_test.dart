import 'package:bottle_crm/data/models/custom_field_definition.dart';
import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/screens/objects/object_records_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

class _FakeObjects extends CustomObjectsNotifier {
  _FakeObjects(this.answer);

  final CustomObjectsAnswer? answer;

  @override
  Future<CustomObjectsAnswer?> build() async => answer;
}

class _FakeRecords extends ObjectRecordsNotifier {
  _FakeRecords(super.key, this.data, this.queries);

  final ObjectRecordsData data;
  final List<String> queries;

  @override
  Future<ObjectRecordsData> build() async => data;

  @override
  Future<void> setQuery(String query) async => queries.add(query);
}

const _summary = ObjectSummary(
  key: 'property',
  label: 'Property',
  labelPlural: 'Properties',
);

const _definition = ObjectDefinition(
  summary: _summary,
  fields: [
    ObjectField(key: 'city', label: 'City', fieldType: 'text', displayOrder: 2),
    ObjectField(
      key: 'beds',
      label: 'Beds',
      fieldType: 'number',
      displayOrder: 1,
    ),
    ObjectField(
      key: 'stage',
      label: 'Stage',
      fieldType: 'dropdown',
      displayOrder: 0,
      options: [CustomFieldOption(value: 'hot', label: 'Hot lead')],
    ),
    ObjectField(
      key: 'notes',
      label: 'Notes',
      fieldType: 'text',
      displayOrder: 3,
    ),
  ],
);

const _records = ObjectRecordsData(
  records: [
    ObjectRecord(
      id: '11111111-1111-1111-1111-111111111111',
      name: 'Harbour View',
      customFields: {'city': 'Oslo', 'beds': 3, 'notes': 'quiet'},
      assignedTo: [
        PersonRef(id: 'p1'),
        PersonRef(id: 'p2'),
      ],
    ),
  ],
  count: 1,
);

Widget _app({
  String objectKey = 'property',
  required bool writes,
  ObjectDefinition? definition = _definition,
  ObjectRecordsData records = _records,
  List<String>? queries,
  List<String>? pushed,
}) {
  final router = GoRouter(
    routes: [
      GoRoute(
        path: '/',
        builder: (_, _) => ObjectRecordsScreen(objectKey: objectKey),
      ),
      GoRoute(
        path: '/more/objects/:key/new',
        builder: (_, _) {
          pushed?.add('new');
          return const Scaffold(body: Text('create screen'));
        },
      ),
      GoRoute(
        path: '/more/objects/:key/:id',
        builder: (_, state) {
          pushed?.add(state.pathParameters['id']!);
          return const Scaffold(body: Text('detail screen'));
        },
      ),
    ],
  );
  return ProviderScope(
    key: UniqueKey(),
    overrides: [
      customObjectsProvider.overrideWith(
        () => _FakeObjects(
          CustomObjectsAnswer(
            hasCustomObjects: writes,
            objects: const [_summary],
          ),
        ),
      ),
      objectDefinitionProvider.overrideWith((ref, key) async => definition),
      objectRecordsProvider(
        'property',
      ).overrideWith(() => _FakeRecords('property', records, queries ?? [])),
    ],
    child: MaterialApp.router(routerConfig: router),
  );
}

void main() {
  malformedKeys();
  testWidgets('the list offers New only with writes on', (tester) async {
    await tester.pumpWidget(_app(writes: true));
    await tester.pumpAndSettle();
    expect(find.text('Properties'), findsOneWidget);
    expect(find.text('Harbour View'), findsOneWidget);
    expect(find.text('New Property'), findsOneWidget);

    await tester.pumpWidget(_app(writes: false));
    await tester.pumpAndSettle();
    expect(find.text('Harbour View'), findsOneWidget);
    expect(find.text('New Property'), findsNothing);
  });

  testWidgets('a row shows the first two filled fields by display order', (
    tester,
  ) async {
    await tester.pumpWidget(_app(writes: true));
    await tester.pumpAndSettle();
    expect(find.textContaining('Beds: 3'), findsOneWidget);
    expect(find.textContaining('City: Oslo'), findsOneWidget);
    expect(find.textContaining('Notes'), findsNothing);
    expect(find.text('2'), findsOneWidget);
  });

  testWidgets('a dropdown shows its label, and a stale value shows itself', (
    tester,
  ) async {
    ObjectRecordsData withStage(String value) => ObjectRecordsData(
      records: [
        ObjectRecord(
          id: '11111111-1111-1111-1111-111111111111',
          name: 'Harbour View',
          customFields: {'stage': value},
        ),
      ],
      count: 1,
    );

    await tester.pumpWidget(_app(writes: true, records: withStage('hot')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Stage: Hot lead'), findsOneWidget);

    await tester.pumpWidget(_app(writes: true, records: withStage('retired')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Stage: retired'), findsOneWidget);
  });

  testWidgets('a missing object says so', (tester) async {
    await tester.pumpWidget(_app(writes: true, definition: null));
    await tester.pumpAndSettle();
    expect(
      find.text('This object does not exist, or you do not have access to it.'),
      findsOneWidget,
    );
    expect(find.text('New Property'), findsNothing);
  });

  testWidgets('an empty list shows an empty state', (tester) async {
    await tester.pumpWidget(
      _app(writes: true, records: const ObjectRecordsData()),
    );
    await tester.pumpAndSettle();
    expect(find.text('No properties yet'), findsOneWidget);
  });

  testWidgets('search waits 300 ms before asking the server', (tester) async {
    final queries = <String>[];
    await tester.pumpWidget(_app(writes: true, queries: queries));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), 'harb');
    await tester.pump(const Duration(milliseconds: 200));
    expect(queries, isEmpty);
    await tester.pump(const Duration(milliseconds: 150));
    expect(queries, ['harb']);
  });

  testWidgets('rows and New open their routes', (tester) async {
    final pushed = <String>[];
    await tester.pumpWidget(_app(writes: true, pushed: pushed));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Harbour View'));
    await tester.pumpAndSettle();
    expect(pushed, ['11111111-1111-1111-1111-111111111111']);

    final router = GoRouter.of(tester.element(find.text('detail screen')));
    router.pop();
    await tester.pumpAndSettle();
    await tester.tap(find.text('New Property'));
    await tester.pumpAndSettle();
    expect(pushed.last, 'new');
  });
}

void malformedKeys() {
  for (final key in ['../leads', 'Bad Key']) {
    testWidgets('a malformed key ($key) says the object does not exist', (
      tester,
    ) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            customObjectsProvider.overrideWith(
              () => _FakeObjects(const CustomObjectsAnswer()),
            ),
          ],
          child: MaterialApp(home: ObjectRecordsScreen(objectKey: key)),
        ),
      );
      await tester.pumpAndSettle();
      expect(
        find.text(
          'This object does not exist, or you do not have access to it.',
        ),
        findsOneWidget,
      );
      expect(find.text('Retry'), findsNothing);
    });
  }
}
