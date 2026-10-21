import 'package:bottle_crm/data/models/custom_field_definition.dart';
import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/screens/objects/object_record_detail_screen.dart';
import 'package:bottle_crm/screens/objects/object_record_form_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// The record detail and form screens on a tablet, at 1.3x text.
///
/// Rendered at 834x1112, where a layout tuned for 390px can stretch badly or
/// overflow once the text is scaled. Flutter reports an overflow as an
/// exception, so a null `takeException()` is the assertion.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const tablet = Size(834, 1112);
  const key = 'property';
  const id = '11111111-1111-1111-1111-111111111111';

  void useTablet(WidgetTester tester) {
    tester.view.devicePixelRatio = 2.0;
    tester.view.physicalSize = Size(tablet.width * 2, tablet.height * 2);
    tester.platformDispatcher.textScaleFactorTestValue = 1.3;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  }

  const definition = ObjectDefinition(
    summary: ObjectSummary(
      key: key,
      label: 'Property',
      labelPlural: 'Properties',
      nameLabel: 'Address',
    ),
    fields: [
      ObjectField(
        key: 'beds',
        label: 'Beds',
        fieldType: 'number',
        displayOrder: 1,
      ),
      ObjectField(
        key: 'kind',
        label: 'Kind',
        fieldType: 'dropdown',
        displayOrder: 2,
        options: [CustomFieldOption(value: 'flat', label: 'Flat')],
      ),
      ObjectField(
        key: 'notes',
        label: 'Notes',
        fieldType: 'textarea',
        displayOrder: 3,
      ),
      ObjectField(
        key: 'agent',
        label: 'Agent',
        fieldType: 'link',
        displayOrder: 4,
        target: 'lead',
        many: true,
      ),
    ],
  );

  final record = {
    'id': id,
    'name':
        '12 Harbour Road, Old Town Quarter, Northern District, Greater '
        'Metropolitan Area',
    'custom_fields': {'beds': 3, 'kind': 'flat', 'notes': 'Quiet street.'},
    'assigned_to': [
      {'id': 'p1', 'name': 'Ravi', 'email': 'ravi@example.com'},
    ],
    'links': {
      'agent': {
        'many': true,
        'records': [
          {'id': 'l1', 'object': 'lead', 'name': 'Asha'},
        ],
        'hidden': 1,
      },
    },
    'can_edit': true,
    'can_delete': true,
    'attachments': [
      {'id': 'a1', 'file_name': 'front.jpg', 'is_image': true},
      {'id': 'a2', 'file_name': 'survey.pdf', 'is_image': false},
    ],
  };

  Future<void> pump(WidgetTester tester, Widget screen) async {
    useTablet(tester);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          objectDefinitionProvider.overrideWith((ref, k) async => definition),
          customObjectsProvider.overrideWith(_FakeObjects.new),
          customObjectsApiProvider.overrideWithValue(_FakeApi(record)),
          attachmentBytesProvider.overrideWith((ref, i) async => null),
          usersProvider.overrideWithValue(const []),
        ],
        child: MaterialApp.router(
          routerConfig: GoRouter(
            routes: [GoRoute(path: '/', builder: (_, _) => screen)],
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('the record detail holds up on a tablet', (tester) async {
    await pump(
      tester,
      const ObjectRecordDetailScreen(objectKey: key, recordId: id),
    );
    expect(tester.takeException(), isNull);
    expect(find.textContaining('12 Harbour Road'), findsWidgets);
  });

  testWidgets('the record form holds up on a tablet, editing', (tester) async {
    await pump(
      tester,
      const ObjectRecordFormScreen(objectKey: key, recordId: id),
    );
    expect(tester.takeException(), isNull);
    expect(find.text('Address *'), findsWidgets);
  });

  testWidgets('the record form holds up on a tablet, creating', (tester) async {
    await pump(tester, const ObjectRecordFormScreen(objectKey: key));
    expect(tester.takeException(), isNull);
  });
}

class _FakeObjects extends CustomObjectsNotifier {
  @override
  Future<CustomObjectsAnswer?> build() async => const CustomObjectsAnswer(
    hasCustomObjects: true,
    objects: [
      ObjectSummary(
        key: 'property',
        label: 'Property',
        labelPlural: 'Properties',
      ),
    ],
    linkTargets: [LinkTarget(key: 'lead', label: 'Lead', labelPlural: 'Leads')],
  );
}

class _FakeApi extends CustomObjectsApi {
  _FakeApi(this.record);

  final Map<String, dynamic> record;

  @override
  Future<ApiResponse<Map<String, dynamic>>> fetchRecord(
    String key,
    String id,
  ) async => ApiResponse(success: true, data: record, statusCode: 200);
}
