import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/custom_field_definition.dart';
import 'package:bottle_crm/widgets/common/custom_fields_display.dart';
import 'package:bottle_crm/widgets/forms/custom_fields_form.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

CustomFieldDefinition _def(
  String key,
  CustomFieldType type, {
  bool required = false,
  List<CustomFieldOption> options = const [],
}) => CustomFieldDefinition(
  id: key,
  targetModel: 'Contact',
  key: key,
  label: key[0].toUpperCase() + key.substring(1),
  fieldType: type,
  isRequired: required,
  options: options,
);

void main() {
  group('customFieldDisplayValue', () {
    test('formats each type the way the web does', () {
      expect(
        customFieldDisplayValue(_def('n', CustomFieldType.number), 1500000.0),
        '1,500,000',
      );
      expect(
        customFieldDisplayValue(_def('n', CustomFieldType.number), 2.5),
        '2.5',
      );
      expect(
        customFieldDisplayValue(_def('c', CustomFieldType.checkbox), true),
        'Yes',
      );
      expect(
        customFieldDisplayValue(_def('c', CustomFieldType.checkbox), false),
        'No',
      );
      expect(
        customFieldDisplayValue(_def('d', CustomFieldType.date), '2026-03-05'),
        'Mar 5, 2026',
      );
      expect(
        customFieldDisplayValue(_def('t', CustomFieldType.text), ' hi '),
        'hi',
      );
    });

    test('a dropdown shows its label, and a stale value as itself', () {
      final tier = _def(
        'tier',
        CustomFieldType.dropdown,
        options: const [CustomFieldOption(value: 'gold', label: 'Gold')],
      );
      expect(customFieldDisplayValue(tier, 'gold'), 'Gold');
      expect(customFieldDisplayValue(tier, 'platinum'), 'platinum');
    });

    test('nothing stored reads as empty', () {
      final text = _def('t', CustomFieldType.text);
      expect(customFieldDisplayValue(text, null), '');
      expect(customFieldDisplayValue(text, '  '), '');
    });
  });

  test('the block follows the definitions', () {
    expect(CustomFieldsDisplay.shows(const []), isFalse);
    expect(
      CustomFieldsDisplay.shows([_def('t', CustomFieldType.text)]),
      isTrue,
    );
  });

  testWidgets('lists every definition, and Not set for an empty one', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        home: Scaffold(
          body: CustomFieldsDisplay(
            definitions: [
              _def('budget', CustomFieldType.number),
              _def('notes', CustomFieldType.text),
            ],
            values: const {'budget': 10, 'legacy': 'not shown'},
          ),
        ),
      ),
    );
    expect(find.text('BUDGET'), findsOneWidget);
    expect(find.text('10'), findsOneWidget);
    expect(find.text('NOTES'), findsOneWidget);
    expect(find.text('Not set'), findsOneWidget);
    expect(find.text('not shown'), findsNothing);
  });

  group('missingRequiredCustomFields', () {
    final defs = [
      _def('licence', CustomFieldType.text, required: true),
      _def('agreed', CustomFieldType.checkbox, required: true),
      _def('notes', CustomFieldType.text),
    ];

    test('names each empty required field by its key', () {
      expect(missingRequiredCustomFields(defs, const {}), {
        'licence': 'Licence is required',
      });
      expect(
        missingRequiredCustomFields(defs, const {'licence': '  '}),
        contains('licence'),
      );
    });

    test(
      'a required checkbox the user never touched is false, not missing',
      () {
        expect(missingRequiredCustomFields([defs[1]], const {}), isEmpty);
        expect(
          missingRequiredCustomFields([defs[1]], const {'agreed': null}),
          isEmpty,
        );
        expect(sendableCustomFields(defs, const {'licence': 'RE-1'}), {
          'licence': 'RE-1',
          'agreed': false,
        });
        expect(
          sendableCustomFields(defs, const {'agreed': true})['agreed'],
          isTrue,
        );
      },
    );

    test('an unparseable number is flagged before saving', () {
      final number = [_def('budget', CustomFieldType.number)];
      expect(customFieldProblems(number, const {'budget': '1.2.3'}), {
        'budget': 'Budget must be a number',
      });
      expect(customFieldProblems(number, const {'budget': '12.5'}), isEmpty);
      expect(customFieldProblems(number, const {'budget': 12.5}), isEmpty);
      expect(customFieldProblems(number, const {}), isEmpty);
    });

    test('an unticked checkbox counts as set, as on the server', () {
      expect(
        missingRequiredCustomFields(defs, const {
          'licence': 'RE-1',
          'agreed': false,
        }),
        isEmpty,
      );
    });
  });

  test('customFieldDefinitionsIn reads the detail key and skips junk', () {
    final defs = customFieldDefinitionsIn({
      'custom_field_definitions': [
        {'id': '1', 'key': 'a', 'label': 'A', 'field_type': 'text'},
        'junk',
      ],
    });
    expect(defs.single.key, 'a');
    expect(customFieldDefinitionsIn(null), isEmpty);
    expect(
      customFieldDefinitionsIn({'custom_field_definitions': 'x'}),
      isEmpty,
    );
  });

  group('CustomFieldsForm', () {
    Future<void> pump(
      WidgetTester tester, {
      required ValueNotifier<Map<String, dynamic>> values,
      Map<String, String> errors = const {},
    }) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            theme: AppTheme.light,
            home: Scaffold(
              body: ValueListenableBuilder(
                valueListenable: values,
                builder: (_, current, _) => CustomFieldsForm(
                  definitions: [
                    _def('licence', CustomFieldType.text, required: true),
                    _def('hours', CustomFieldType.number),
                  ],
                  values: current,
                  errors: errors,
                  onChanged: (next) => values.value = next,
                ),
              ),
            ),
          ),
        ),
      );
    }

    testWidgets('shows an error under its field', (tester) async {
      await pump(
        tester,
        values: ValueNotifier({}),
        errors: const {'licence': 'Licence is required'},
      );
      expect(find.text('Licence is required'), findsOneWidget);
    });

    testWidgets('flags a number that is not one beside its field', (
      tester,
    ) async {
      final values = ValueNotifier<Map<String, dynamic>>({});
      await pump(tester, values: values);
      await tester.enterText(find.byType(TextField).at(1), '1.2.3');
      await tester.pump();
      expect(find.text('Hours must be a number'), findsOneWidget);
      await tester.enterText(find.byType(TextField).at(1), '12');
      await tester.pump();
      expect(find.text('Hours must be a number'), findsNothing);
    });

    testWidgets('keeps one controller while the parent rebuilds on every '
        'keystroke, and takes an outside reset', (tester) async {
      final values = ValueNotifier<Map<String, dynamic>>({});
      await pump(tester, values: values);
      TextEditingController controller() =>
          tester.widget<TextField>(find.byType(TextField).first).controller!;
      final first = controller();

      await tester.enterText(find.byType(TextField).first, 'RE');
      await tester.pump();
      await tester.enterText(find.byType(TextField).first, 'RE-1');
      await tester.pump();
      expect(values.value['licence'], 'RE-1');
      expect(identical(controller(), first), isTrue);

      await tester.enterText(find.byType(TextField).at(1), '2.');
      await tester.pump();
      // "2." parses as 2, and the box keeps what was typed.
      expect(values.value['hours'], 2);
      expect(controller().text, 'RE-1');
      expect(
        tester.widget<TextField>(find.byType(TextField).at(1)).controller!.text,
        '2.',
      );

      values.value = {};
      await tester.pump();
      expect(controller().text, isEmpty);
    });
  });
}
