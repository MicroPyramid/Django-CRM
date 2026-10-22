import 'dart:convert';

import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:bottle_crm/widgets/objects/related_objects_section.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;

const _leadId = '3f2b8c1e-5a4d-4e8b-9c3a-1d2e3f4a5b6c';
const _homeId = '11111111-1111-1111-1111-111111111111';
const _otherId = '22222222-2222-2222-2222-222222222222';
const _pickId = '33333333-3333-3333-3333-333333333333';

const _objects =
    '{"has_custom_objects": true, "objects": ['
    '{"key": "property", "label": "Property", "label_plural": "Properties"}],'
    ' "link_targets": []}';

String _related({required bool canEdit}) => jsonEncode({
  'groups': [
    {
      'object': {
        'key': 'property',
        'label': 'Property',
        'label_plural': 'Properties',
      },
      'field': {'key': 'enquiries', 'label': 'Enquiries'},
      'records': [
        {'id': _homeId, 'name': '12 Park Lane'},
      ],
    },
    {
      'object': {
        'key': 'property',
        'label': 'Property',
        'label_plural': 'Properties',
      },
      'field': {'key': 'seller', 'label': 'Seller'},
      'records': [
        {'id': _otherId, 'name': '4 Mill Road'},
      ],
    },
  ],
  'can_edit': canEdit,
  'link_fields': canEdit
      ? [
          {
            'object': {'key': 'property', 'label': 'Property'},
            'field': {'key': 'enquiries', 'label': 'Enquiries'},
          },
        ]
      : [],
});

class _Client extends http.BaseClient {
  int objectsStatus = 200;
  int writeStatus = 200;
  String writeBody = '{"added": true}';
  String related = '{}';
  final List<http.BaseRequest> sent = [];
  final List<String> bodies = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    final bytes = await request.finalize().toBytes();
    bodies.add(utf8.decode(bytes));
    final path = request.url.path;
    var status = 200;
    var body = '{}';
    if (path == '/api/objects/') {
      status = objectsStatus;
      body = _objects;
    } else if (path == '/api/objects/related/') {
      if (request.method == 'GET') {
        body = related;
      } else {
        status = writeStatus;
        body = writeBody;
      }
    } else if (path == '/api/objects/property/records/') {
      body =
          '{"count": 1, "results": [{"id": "$_pickId", "name": "9 Quay Street"}]}';
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }

  Iterable<http.BaseRequest> get related_ =>
      sent.where((r) => r.url.path == '/api/objects/related/');
}

late _Client _client;

Future<void> _pump(WidgetTester tester) async {
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  addTearDown(tester.view.reset);
  final router = GoRouter(
    routes: [
      GoRoute(
        path: '/',
        builder: (_, _) => const Scaffold(
          body: SingleChildScrollView(
            child: RelatedObjectsSection(to: 'lead', recordId: _leadId),
          ),
        ),
      ),
      GoRoute(
        path: AppRoutes.objectRecord('property', _homeId),
        builder: (_, _) => const Scaffold(body: Text('property screen')),
      ),
    ],
  );
  await tester.pumpWidget(
    ProviderScope(child: MaterialApp.router(routerConfig: router)),
  );
  await tester.pumpAndSettle();
}

void main() {
  setUp(() {
    _client = _Client();
    ApiService().setClientForTesting(_client);
  });

  testWidgets('renders nothing and asks nothing when custom objects are not '
      'offered', (tester) async {
    _client.objectsStatus = 404;
    await _pump(tester);

    expect(find.text('Related'), findsNothing);
    expect(_client.related_, isEmpty);
  });

  testWidgets('lists linked records under object and field', (tester) async {
    _client.related = _related(canEdit: false);
    await _pump(tester);

    expect(find.text('Related'), findsOneWidget);
    expect(find.text('Property: Enquiries'), findsOneWidget);
    expect(find.text('Property: Seller'), findsOneWidget);
    expect(find.text('12 Park Lane'), findsOneWidget);

    await tester.tap(find.text('12 Park Lane'));
    await tester.pumpAndSettle();
    expect(find.text('property screen'), findsOneWidget);
  });

  testWidgets('offers removal only on fields this person may edit', (
    tester,
  ) async {
    _client.related = _related(canEdit: true);
    await _pump(tester);

    expect(find.byTooltip('Remove 12 Park Lane'), findsOneWidget);
    expect(find.byTooltip('Remove 4 Mill Road'), findsNothing);

    await tester.tap(find.byTooltip('Remove 12 Park Lane'));
    await tester.pumpAndSettle();
    expect(find.text('Remove from Property: Enquiries?'), findsOneWidget);
    await tester.tap(find.text('Remove'));
    await tester.pumpAndSettle();

    final delete = _client.sent.firstWhere((r) => r.method == 'DELETE');
    expect(delete.url.queryParameters, {
      'to': 'lead',
      'id': _leadId,
      'record': _homeId,
      'field': 'enquiries',
    });
  });

  testWidgets('adds the record through the API', (tester) async {
    _client.related = _related(canEdit: true);
    await _pump(tester);

    await tester.tap(find.text('Add to'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Property: Enquiries').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('9 Quay Street'));
    await tester.pumpAndSettle();

    final post = _client.related_.firstWhere((r) => r.method == 'POST');
    final body = _client.bodies[_client.sent.indexOf(post)];
    expect(jsonDecode(body), {
      'to': 'lead',
      'id': _leadId,
      'record': _pickId,
      'field': 'enquiries',
    });
    expect(find.text('Search'), findsNothing);
  });

  testWidgets('a refusal shows the server message', (tester) async {
    _client.related = _related(canEdit: true);
    _client.writeStatus = 403;
    _client.writeBody = '{"detail": "You cannot change this record."}';
    await _pump(tester);

    await tester.tap(find.text('Add to'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Property: Enquiries').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('9 Quay Street'));
    await tester.pumpAndSettle();

    expect(find.text('You cannot change this record.'), findsOneWidget);
  });

  testWidgets('a reader sees no add or remove', (tester) async {
    _client.related = _related(canEdit: false);
    await _pump(tester);

    expect(find.text('12 Park Lane'), findsOneWidget);
    expect(find.text('Add to'), findsNothing);
    expect(find.byTooltip('Remove 12 Park Lane'), findsNothing);
  });
}
