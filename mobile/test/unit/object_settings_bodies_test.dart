import 'package:bottle_crm/data/models/custom_field_definition.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('a field edit never sends key, type, target or many', () {
    final text = fieldWriteBody(
      creating: false,
      label: 'City',
      key: 'city',
      fieldType: 'text',
      target: 'contact',
      many: true,
      isRequired: true,
      displayOrder: 2,
    );
    expect(text, {'label': 'City', 'is_required': true, 'display_order': 2});

    final link = fieldWriteBody(
      creating: false,
      label: 'Owner',
      key: 'owner',
      fieldType: 'link',
      target: 'contact',
      many: true,
      isRequired: true,
    );
    expect(link, {'label': 'Owner'});

    final object = objectWriteBody(
      creating: false,
      label: 'Property',
      labelPlural: 'Properties',
      key: 'property',
    );
    expect(object.containsKey('key'), isFalse);
    expect(object['record_access'], 'own');
  });

  test('a new link field sends target and many and no options', () {
    final body = fieldWriteBody(
      creating: true,
      label: 'Owner',
      key: 'owner',
      fieldType: 'link',
      target: 'contact',
      many: false,
      isRequired: true,
      options: const [CustomFieldOption(value: '', label: 'x')],
    );
    expect(body, {
      'label': 'Owner',
      'key': 'owner',
      'field_type': 'link',
      'target': 'contact',
      'many': false,
    });
  });

  test('a dropdown keeps stored values and slugs only new rows', () {
    final body = fieldWriteBody(
      creating: true,
      label: 'Stage',
      key: 'stage',
      fieldType: 'dropdown',
      options: const [
        CustomFieldOption(value: 'hot', label: 'Very Hot'),
        CustomFieldOption(value: '', label: 'Very Hot'),
        CustomFieldOption(value: '', label: '   '),
        CustomFieldOption(value: '', label: '!!!'),
      ],
    );
    expect(body['is_required'], false);
    expect(body['options'], [
      {'value': 'hot', 'label': 'Very Hot'},
      {'value': 'very-hot', 'label': 'Very Hot'},
      {'value': 'option_1', 'label': '!!!'},
    ]);
  });

  test('an object body trims, defaults access and names the key on create', () {
    final body = objectWriteBody(
      creating: true,
      label: ' Property ',
      labelPlural: 'Properties',
      key: 'property',
      nameLabel: ' ',
      description: ' Homes ',
      recordAccess: 'everyone',
    );
    expect(body, {
      'label': 'Property',
      'label_plural': 'Properties',
      'description': 'Homes',
      'record_access': 'everyone',
      'key': 'property',
    });
  });
}
