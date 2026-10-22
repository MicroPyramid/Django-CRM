import 'dart:async';

import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/data/models/lookup_models.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/objects/object_record_form_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:bottle_crm/widgets/common/common.dart';
import 'package:bottle_crm/widgets/objects/link_field_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

const _key = 'property';
const _id = '11111111-1111-1111-1111-111111111111';

const _definition = ObjectDefinition(
  summary: ObjectSummary(
    key: _key,
    label: 'Property',
    labelPlural: 'Properties',
    nameLabel: 'Address',
  ),
  fields: [
    ObjectField(
      key: 'price',
      label: 'Price',
      fieldType: 'number',
      displayOrder: 1,
    ),
    ObjectField(
      key: 'agent',
      label: 'Agent',
      fieldType: 'link',
      displayOrder: 2,
      target: 'lead',
      many: false,
    ),
    ObjectField(
      key: 'friends',
      label: 'Friends',
      fieldType: 'link',
      displayOrder: 3,
      target: 'lead',
      many: true,
    ),
  ],
);

class _FakeObjects extends CustomObjectsNotifier {
  _FakeObjects(this.answer);

  final CustomObjectsAnswer answer;

  @override
  Future<CustomObjectsAnswer?> build() async => answer;
}

class _FailingObjects extends CustomObjectsNotifier {
  _FailingObjects([this.onBuild]);

  final void Function()? onBuild;

  @override
  Future<CustomObjectsAnswer?> build() async {
    onBuild?.call();
    throw Exception('timeout');
  }
}

class _FakeApi extends CustomObjectsApi {
  _FakeApi({
    required this.record,
    this.updateAnswer,
    this.updateGate,
    List<ApiResponse<Map<String, dynamic>>>? updateAnswers,
  }) : updateAnswers = updateAnswers ?? [];

  final Completer<ApiResponse<Map<String, dynamic>>>? updateGate;

  final Map<String, dynamic> record;
  final ApiResponse<Map<String, dynamic>>? updateAnswer;
  final List<ApiResponse<Map<String, dynamic>>> updateAnswers;
  final List<Map<String, dynamic>> updates = [];
  final List<Map<String, dynamic>> creates = [];

  @override
  Future<ApiResponse<Map<String, dynamic>>> fetchRecord(
    String key,
    String id,
  ) async => ApiResponse(success: true, data: record, statusCode: 200);

  @override
  Future<ApiResponse<Map<String, dynamic>>> updateRecord(
    String key,
    String id,
    Map<String, dynamic> body,
  ) async {
    updates.add(body);
    if (updateGate != null) return updateGate!.future;
    if (updateAnswers.isNotEmpty) return updateAnswers.removeAt(0);
    return updateAnswer ??
        ApiResponse(success: true, data: record, statusCode: 200);
  }

  @override
  Future<ApiResponse<Map<String, dynamic>>> createRecord(
    String key,
    Map<String, dynamic> body,
  ) async {
    creates.add(body);
    return ApiResponse(success: true, data: record, statusCode: 201);
  }
}

Map<String, dynamic> _record({
  bool canEdit = true,
  Map<String, dynamic>? agent,
  Map<String, dynamic>? friends,
}) => {
  'id': _id,
  'name': '12 Park Lane',
  'custom_fields': {'price': 100},
  'assigned_to': [
    {'id': 'gone', 'name': 'Old Hand', 'email': 'old@example.com'},
  ],
  'links': {
    'agent':
        agent ??
        {
          'many': false,
          'records': [
            {'id': 'l1', 'object': 'lead', 'name': 'Asha'},
          ],
          'hidden': 0,
        },
    'friends': friends ?? {'many': true, 'records': const [], 'hidden': 0},
  },
  'can_edit': canEdit,
  'can_delete': false,
  'attachments': const [],
};

Widget _app(
  _FakeApi api, {
  bool writes = true,
  bool objectsFail = false,
  void Function()? onObjectsBuild,
  String? recordId = _id,
}) {
  final router = GoRouter(
    routes: [
      GoRoute(
        path: '/',
        builder: (context, _) => Scaffold(
          body: TextButton(
            onPressed: () => context.push('/form'),
            child: const Text('open'),
          ),
        ),
      ),
      GoRoute(
        path: AppRoutes.objectRecord(_key, _id),
        builder: (_, _) => const Scaffold(body: Text('detail screen')),
      ),
      GoRoute(
        path: '/form',
        builder: (_, _) =>
            ObjectRecordFormScreen(objectKey: _key, recordId: recordId),
      ),
    ],
  );
  return ProviderScope(
    key: UniqueKey(),
    overrides: [
      customObjectsProvider.overrideWith(
        objectsFail
            ? () => _FailingObjects(onObjectsBuild)
            : () => _FakeObjects(CustomObjectsAnswer(hasCustomObjects: writes)),
      ),
      objectDefinitionProvider.overrideWith((ref, key) async => _definition),
      customObjectsApiProvider.overrideWithValue(api),
      linkTargetSearchProvider.overrideWith(
        (ref, arg) async => const [
          LinkedRecord(id: 'r', object: 'lead', name: 'Ravi Link'),
        ],
      ),
      usersProvider.overrideWithValue(const [
        UserLookup(
          id: 'p1',
          email: 'ravi@example.com',
          name: 'Ravi',
          role: 'USER',
          isActive: true,
        ),
      ]),
    ],
    child: MaterialApp.router(routerConfig: router),
  );
}

Future<void> _open(WidgetTester tester, Widget app) async {
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 2000 * 3);
  addTearDown(tester.view.reset);
  await tester.pumpWidget(app);
  await tester.pumpAndSettle();
  await tester.tap(find.text('open'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('saving an untouched record sends only the name', (tester) async {
    final api = _FakeApi(record: _record());
    await _open(tester, _app(api));

    expect(find.text('Address *'), findsOneWidget);
    expect(find.text('Asha'), findsOneWidget);
    expect(find.text('Old Hand (inactive)'), findsOneWidget);
    expect(find.byType(LinkFieldPicker), findsNWidgets(2));

    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(api.updates, [
      {'name': '12 Park Lane'},
    ]);
    expect(find.text('open'), findsOneWidget);
  });

  testWidgets('shows the server refusal by field label', (tester) async {
    final api = _FakeApi(
      record: _record(),
      updateAnswer: const ApiResponse(
        success: false,
        statusCode: 400,
        data: {
          'custom_fields': {'price': 'Enter a number.'},
        },
      ),
    );
    await _open(tester, _app(api));

    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(find.text('Price: Enter a number.'), findsNWidgets(2));
    expect(
      find.descendant(
        of: find.byType(SnackBar),
        matching: find.text('Price: Enter a number.').hitTestable(),
      ),
      findsOneWidget,
    );
    expect(find.text('Address *'), findsOneWidget);
  });

  testWidgets('a blank name is refused before sending', (tester) async {
    final api = _FakeApi(record: _record());
    await _open(tester, _app(api));

    await tester.enterText(find.byType(TextFormField).first, '');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(api.updates, isEmpty);
    expect(find.text('Address is required'), findsOneWidget);
  });

  testWidgets('says writes are off when writes are off', (tester) async {
    await _open(tester, _app(_FakeApi(record: _record()), writes: false));

    expect(
      find.text('Creating and editing is turned off for this organization.'),
      findsOneWidget,
    );
    expect(find.text('Save'), findsNothing);
  });

  testWidgets('says the answer could not be loaded, not that writes are off', (
    tester,
  ) async {
    await _open(tester, _app(_FakeApi(record: _record()), objectsFail: true));

    expect(
      find.text('Custom objects could not be loaded. Try again.'),
      findsOneWidget,
    );
    expect(
      find.text('Creating and editing is turned off for this organization.'),
      findsNothing,
    );
    expect(find.text('Save'), findsNothing);
  });

  testWidgets('the could-not-load sentence has a Retry that asks again', (
    tester,
  ) async {
    var builds = 0;
    await _open(
      tester,
      _app(
        _FakeApi(record: _record()),
        objectsFail: true,
        onObjectsBuild: () => builds++,
      ),
    );
    expect(builds, 1);

    final retry = find.widgetWithText(TextButton, 'Retry');
    expect(tester.getSize(retry).height, greaterThanOrEqualTo(44));
    await tester.tap(retry);
    await tester.pumpAndSettle();

    expect(builds, 2);
    expect(find.text(objectsLoadFailedNotice), findsOneWidget);
  });

  ApiResponse<Map<String, dynamic>> refusal(String message) => ApiResponse(
    success: false,
    statusCode: 400,
    data: {
      'custom_fields': {'price': message},
    },
  );

  Finder inSnackBar(String text) =>
      find.descendant(of: find.byType(SnackBar), matching: find.text(text));

  testWidgets('a second refusal replaces the first SnackBar', (tester) async {
    final api = _FakeApi(
      record: _record(),
      updateAnswers: [refusal('Too low.'), refusal('Too high.')],
    );
    await _open(tester, _app(api));

    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(inSnackBar('Price: Too low.'), findsOneWidget);

    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(inSnackBar('Price: Too low.'), findsNothing);
    expect(inSnackBar('Price: Too high.').hitTestable(), findsOneWidget);
  });

  testWidgets('a successful save clears the refusal SnackBar', (tester) async {
    final api = _FakeApi(
      record: _record(),
      updateAnswers: [refusal('Too low.')],
    );
    await _open(tester, _app(api));

    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(inSnackBar('Price: Too low.'), findsOneWidget);

    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(find.text('open'), findsOneWidget);
    expect(find.byType(SnackBar), findsNothing);
  });

  testWidgets('says so for a record the user cannot edit', (tester) async {
    await _open(tester, _app(_FakeApi(record: _record(canEdit: false))));

    expect(find.text('You cannot edit this record.'), findsOneWidget);
    expect(find.text('Save'), findsNothing);
  });

  testWidgets('a new record sends what was typed and links nothing', (
    tester,
  ) async {
    final api = _FakeApi(record: _record());
    await _open(tester, _app(api, recordId: null));

    await tester.enterText(find.byType(TextFormField).first, '9 Mill Road');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(api.creates, [
      {'name': '9 Mill Road'},
    ]);
    expect(find.text('detail screen'), findsOneWidget);
  });

  Map<String, dynamic> lead(String id, String name) => {
    'id': id,
    'object': 'lead',
    'name': name,
  };

  testWidgets('a read-only one-record link is shown and never sent', (
    tester,
  ) async {
    final api = _FakeApi(
      record: _record(agent: {'many': false, 'records': const [], 'hidden': 1}),
    );
    await _open(tester, _app(api));
    expect(find.text("Linked to a record you can't open"), findsOneWidget);

    await tester.enterText(find.byType(TextFormField).first, 'Renamed');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(api.updates, [
      {'name': 'Renamed'},
    ]);
  });

  testWidgets('removing a visible link sends only the visible ids left', (
    tester,
  ) async {
    final api = _FakeApi(
      record: _record(
        friends: {
          'many': true,
          'records': [lead('b', 'Bo'), lead('c', 'Cy')],
          'hidden': 2,
        },
      ),
    );
    await _open(tester, _app(api));
    expect(find.text("and 2 you can't open"), findsOneWidget);

    await tester.tap(find.byTooltip('Remove Bo'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(api.updates, [
      {
        'name': '12 Park Lane',
        'links': {
          'friends': ['c'],
        },
      },
    ]);
  });

  testWidgets('a changed custom field sends just that key', (tester) async {
    final api = _FakeApi(record: _record());
    await _open(tester, _app(api));

    await tester.enterText(find.byType(TextFormField).at(1), '250');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    final body = api.updates.single;
    expect(body.keys.toSet(), {'name', 'custom_fields'});
    expect((body['custom_fields'] as Map).keys, ['price']);
    expect(num.parse('${(body['custom_fields'] as Map)['price']}'), 250);
  });

  testWidgets('a link change sends just that field', (tester) async {
    final api = _FakeApi(record: _record());
    await _open(tester, _app(api));

    await tester.tap(find.text('Add').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ravi Link'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(api.updates, [
      {
        'name': '12 Park Lane',
        'links': {
          'agent': ['r'],
        },
      },
    ]);
  });

  testWidgets('an assignee change sends assigned_to', (tester) async {
    final api = _FakeApi(record: _record());
    await _open(tester, _app(api));

    await tester.tap(find.text('Choose'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ravi'));
    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    final body = api.updates.single;
    expect(body.keys.toSet(), {'name', 'assigned_to'});
    expect((body['assigned_to'] as List).toSet(), {'gone', 'p1'});
  });

  testWidgets('tapping Save twice makes one request', (tester) async {
    final gate = Completer<ApiResponse<Map<String, dynamic>>>();
    final api = _FakeApi(record: _record(), updateGate: gate);
    await _open(tester, _app(api));

    await tester.tap(find.text('Save'));
    await tester.pump();
    await tester.tap(find.byType(PrimaryButton), warnIfMissed: false);
    await tester.pump();
    expect(api.updates, hasLength(1));

    gate.complete(ApiResponse(success: true, data: _record(), statusCode: 200));
    await tester.pumpAndSettle();
    expect(api.updates, hasLength(1));
  });
}
