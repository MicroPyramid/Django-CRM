import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/data/models/custom_field_definition.dart';
import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:flutter_test/flutter_test.dart';

const uuid = '3f2b8c1e-5a4d-4e2f-9b7a-1c2d3e4f5a6b';

final recordDetailFixture = <String, dynamic>{
  'id': uuid,
  'name': '12 High Street',
  'custom_fields': {'status': 'available', 'beds': 3},
  'assigned_to': [
    {'id': 'p1', 'name': 'Asha', 'email': 'asha@example.com'},
  ],
  'created_at': '2026-10-01T10:00:00Z',
  'updated_at': '2026-10-02T10:00:00Z',
  'object': {'key': 'property', 'label': 'Property', 'name_label': 'Address'},
  'links': {
    'owner': {'many': false, 'records': [], 'hidden': 1},
    'enquiries': {
      'many': true,
      'records': [
        {'id': 'c1', 'object': 'contact', 'name': 'Sam'},
      ],
      'hidden': 2,
    },
  },
  'created_by': {'id': 'p2', 'name': 'Bo', 'email': 'bo@example.com'},
  'can_edit': true,
  'can_delete': false,
  'attachments': [
    {
      'id': uuid,
      'file_name': 'house.jpg',
      'is_image': true,
      'created_by': null,
      'created_at': '2026-10-01T11:00:00Z',
      'download_url': '/api/attachments/$uuid/download/',
      'can_delete': true,
    },
  ],
};

RecordAttachment att(String name, {required bool isImage}) =>
    RecordAttachment(id: uuid, fileName: name, isImage: isImage);

CustomObjectsAnswer answer({required bool writes, required bool objects}) =>
    CustomObjectsAnswer.fromJson({
      'has_custom_objects': writes,
      'objects': objects
          ? [
              {
                'key': 'property',
                'label': 'Property',
                'label_plural': 'Properties',
                'name_label': 'Address',
                'description': '',
                'record_access': 'everyone',
                'is_active': true,
              },
            ]
          : [],
      'link_targets': [
        {'key': 'lead', 'label': 'Lead', 'label_plural': 'Leads'},
      ],
    });

void main() {
  test('a one-record field held by a hidden link is read-only', () {
    final r = ObjectRecord.fromJson(recordDetailFixture);
    expect(r.links['owner']!.readOnly, isTrue);
    expect(r.links['enquiries']!.hidden, 2);
    expect(r.links['enquiries']!.readOnly, isFalse);
    expect(r.canEdit, isTrue);
    expect(r.attachments.single.canDelete, isTrue);
    expect(r.createdBy!.email, 'bo@example.com');
  });

  test('a list row parses with no links, attachments or rights', () {
    final r = ObjectRecord.fromJson({
      'id': uuid,
      'name': 'x',
      'custom_fields': {},
      'assigned_to': [],
      'created_at': '2026-10-01T10:00:00Z',
      'updated_at': '2026-10-01T10:00:00Z',
    });
    expect(r.links, isEmpty);
    expect(r.attachments, isEmpty);
    expect(r.createdBy, isNull);
    expect(r.canEdit, isFalse);
    expect(r.canDelete, isFalse);
  });

  test('only real images are photos', () {
    expect(att('house.JPG', isImage: true).isPhoto, isTrue);
    expect(att('plan.svg', isImage: true).isPhoto, isFalse);
    expect(att('plan.svg', isImage: false).isPhoto, isFalse);
    expect(att('notes.pdf', isImage: false).isPhoto, isFalse);
  });

  test('an attachment keeps a file but never a path to open', () {
    final a = att('house.jpg', isImage: true).toAttachment();
    expect(a.hasFile, isTrue);
    expect(a.id, uuid);
  });

  test('an org with neither objects nor writes on is not offered', () {
    expect(answer(writes: false, objects: false).offered, isFalse);
    expect(answer(writes: true, objects: false).offered, isTrue);
    expect(answer(writes: false, objects: true).offered, isTrue);
    expect(answer(writes: true, objects: true).offered, isTrue);
    expect(answer(writes: true, objects: true).linkTargets.single.key, 'lead');
  });

  test('an object field becomes a custom field definition', () {
    final field = ObjectField.fromJson({
      'key': 'status',
      'label': 'Status',
      'field_type': 'dropdown',
      'options': [
        {'value': 'available', 'label': 'Available'},
        {'value': 'let_agreed', 'label': 'Let agreed'},
      ],
      'is_required': true,
      'display_order': 2,
      'is_active': true,
      'target': null,
      'many': null,
    });
    final def = field.toDefinition('property');
    expect(def.targetModel, 'obj:property');
    expect(def.fieldType, CustomFieldType.dropdown);
    expect(def.options.map((o) => o.value), ['available', 'let_agreed']);
    expect(def.isRequired, isTrue);
    expect(def.key, 'status');
    expect(field.isLink, isFalse);
  });

  test('fields tolerate missing optional keys, and split by kind', () {
    final def = ObjectDefinition.fromJson({
      'key': 'property',
      'label': 'Property',
      'label_plural': 'Properties',
      'fields': [
        {'key': 'b', 'label': 'B', 'field_type': 'text', 'display_order': 2},
        {
          'key': 'owner',
          'label': 'Owner',
          'field_type': 'link',
          'target': 'contact',
          'many': false,
          'display_order': 1,
        },
        {'key': 'a', 'label': 'A', 'field_type': 'text', 'display_order': 1},
        {
          'key': 'off',
          'label': 'Off',
          'field_type': 'text',
          'is_active': false,
        },
      ],
    });
    expect(def.summary.description, '');
    expect(def.customFields.map((f) => f.key), ['a', 'b']);
    expect(def.linkFields.map((f) => f.key), ['owner']);
  });

  test('a related answer says what is removable and when it shows nothing', () {
    final r = RelatedAnswer.fromJson({
      'groups': [
        {
          'object': {
            'key': 'property',
            'label': 'Property',
            'label_plural': 'Properties',
          },
          'field': {'key': 'owners', 'label': 'Owners'},
          'records': [
            {'id': uuid, 'name': '12 High Street'},
          ],
        },
      ],
      'can_edit': true,
      'link_fields': [
        {
          'object': {'key': 'property', 'label': 'Property'},
          'field': {'key': 'owners', 'label': 'Owners'},
        },
      ],
    });
    expect(r.removable(r.groups.single), isTrue);
    expect(r.showsNothing, isFalse);
    expect(RelatedAnswer.fromJson({'groups': []}).showsNothing, isTrue);
  });

  test('object URLs refuse a malformed key or id', () {
    expect(() => ApiConfig.object('../leads'), throwsArgumentError);
    expect(
      () => ApiConfig.objectRecord('property', 'nope'),
      throwsArgumentError,
    );
    expect(() => ApiConfig.objectField('property', 'Bad'), throwsArgumentError);
    expect(
      () => ApiConfig.objectRecordAttachment('property', uuid, 'x'),
      throwsArgumentError,
    );
    expect(
      ApiConfig.objectRecord('property', uuid),
      endsWith('/objects/property/records/$uuid/'),
    );
    expect(
      ApiConfig.objectRecordAttachment('property', uuid.toUpperCase(), uuid),
      endsWith(
        '/objects/property/records/${uuid.toUpperCase()}/attachments/$uuid/',
      ),
    );
    expect(
      ApiConfig.objectField('property', 'status'),
      endsWith('/objects/property/fields/status/'),
    );
    expect(ApiConfig.objectsRelated, endsWith('/objects/related/'));
  });

  test('suggests keys as the web does', () {
    expect(suggestObjectKey('Property', 28), 'property');
    expect(suggestObjectKey('3D Prints!', 28), 'd_prints');
    expect(suggestObjectKey('Ünits', 28), 'units');
    expect(suggestObjectKey('Very Long Object Name Here', 8), 'very_lon');
    expect(suggestObjectKey('Ab cd', 3), 'ab');
  });
}
