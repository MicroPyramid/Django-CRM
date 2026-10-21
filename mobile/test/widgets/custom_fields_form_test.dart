import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/custom_field_definition.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/widgets/forms/custom_fields_form.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// The ticket, task and deal forms save the map this widget hands back, and
/// the server keeps every key a save leaves out. So a cleared field has to be
/// sent as null: dropping the key from the map left the old value in place.
/// Keys the form does not render, such as a field an admin turned off, pass
/// through as they are.
void main() {
  const definitions = [
    CustomFieldDefinition(
      id: '1',
      targetModel: 'Case',
      key: 'note',
      label: 'Note',
      fieldType: CustomFieldType.text,
    ),
    CustomFieldDefinition(
      id: '2',
      targetModel: 'Case',
      key: 'hours',
      label: 'Hours',
      fieldType: CustomFieldType.number,
    ),
    CustomFieldDefinition(
      id: '3',
      targetModel: 'Case',
      key: 'severity',
      label: 'Severity',
      fieldType: CustomFieldType.dropdown,
      options: [CustomFieldOption(value: 'S1', label: 'Sev 1')],
    ),
  ];

  Future<List<Map<String, dynamic>>> pump(WidgetTester tester) async {
    final changes = <Map<String, dynamic>>[];
    var values = <String, dynamic>{
      'note': 'hello',
      'hours': 3.0,
      'severity': 'S1',
      'legacy': 'kept',
    };
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          customFieldDefinitionsProvider(
            'Case',
          ).overrideWith((ref) async => definitions),
        ],
        child: MaterialApp(
          theme: AppTheme.light,
          home: Scaffold(
            body: StatefulBuilder(
              builder: (context, setState) => SingleChildScrollView(
                child: CustomFieldsForm(
                  targetModel: 'Case',
                  values: values,
                  onChanged: (next) {
                    changes.add(next);
                    setState(() => values = next);
                  },
                ),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    return changes;
  }

  void expectSentAsNull(Map<String, dynamic> sent, String key) {
    expect(sent.containsKey(key), isTrue, reason: '$key must be sent');
    expect(sent[key], isNull);
    expect(sent['legacy'], 'kept');
  }

  testWidgets('clearing a text field sends it as null', (tester) async {
    final changes = await pump(tester);
    await tester.enterText(find.byType(TextFormField).at(0), '');
    await tester.pump();

    expectSentAsNull(changes.last, 'note');
  });

  testWidgets('clearing a number field sends it as null', (tester) async {
    final changes = await pump(tester);
    await tester.enterText(find.byType(TextFormField).at(1), '');
    await tester.pump();

    expectSentAsNull(changes.last, 'hours');
  });

  testWidgets('Clear on a dropdown sends it as null', (tester) async {
    final changes = await pump(tester);
    await tester.tap(find.text('Sev 1'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Clear'));
    await tester.pumpAndSettle();

    expectSentAsNull(changes.last, 'severity');
    expect(find.text('Select…'), findsOneWidget);
  });
}
