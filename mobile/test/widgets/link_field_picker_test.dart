import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/widgets/objects/link_field_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _one = ObjectField(
  key: 'owner',
  label: 'Owner',
  fieldType: 'link',
  target: 'lead',
  many: false,
);
const _many = ObjectField(
  key: 'agents',
  label: 'Agents',
  fieldType: 'link',
  target: 'lead',
  many: true,
);
const _asha = LinkedRecord(id: 'a', object: 'lead', name: 'Asha');
const _ravi = LinkedRecord(id: 'r', object: 'lead', name: 'Ravi');
const _meera = LinkedRecord(id: 'm', object: 'lead', name: 'Meera');

Widget _host({
  required ObjectField field,
  required LinkValue value,
  required List<LinkedRecord> selected,
  required ValueChanged<List<LinkedRecord>> onChanged,
}) => ProviderScope(
  overrides: [
    linkTargetSearchProvider.overrideWith((ref, arg) async => [_ravi, _meera]),
  ],
  child: MaterialApp(
    home: Scaffold(
      body: LinkFieldPicker(
        field: field,
        value: value,
        selected: selected,
        onChanged: onChanged,
      ),
    ),
  ),
);

Widget _searchHost(Future<List<LinkedRecord>> Function() search) =>
    ProviderScope(
      overrides: [
        linkTargetSearchProvider.overrideWith((ref, arg) => search()),
      ],
      child: MaterialApp(
        home: Scaffold(
          body: LinkSearchSheet(
            title: 'Property: Agents',
            target: 'lead',
            taken: const {},
            controller: ScrollController(),
          ),
        ),
      ),
    );

void main() {
  testWidgets('a failed search says so and offers a retry', (tester) async {
    var calls = 0;
    await tester.pumpWidget(
      _searchHost(() async {
        calls++;
        if (calls == 1) throw Exception('502');
        return [_ravi];
      }),
    );
    await tester.pumpAndSettle();

    expect(find.text('Could not search. Try again.'), findsOneWidget);
    expect(find.text('No matches'), findsNothing);

    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(find.text('Ravi'), findsOneWidget);
    expect(find.text('Could not search. Try again.'), findsNothing);
  });

  testWidgets('an empty search says no matches', (tester) async {
    await tester.pumpWidget(_searchHost(() async => const []));
    await tester.pumpAndSettle();

    expect(find.text('No matches'), findsOneWidget);
    expect(find.text('Could not search. Try again.'), findsNothing);
  });

  testWidgets('a read-only link field has no add or remove', (tester) async {
    await tester.pumpWidget(
      _host(
        field: _one,
        value: const LinkValue(many: false, records: [], hidden: 1),
        selected: const [],
        onChanged: (_) {},
      ),
    );

    expect(find.text("Linked to a record you can't open"), findsOneWidget);
    expect(find.text('Add'), findsNothing);
    expect(find.byTooltip('Remove Asha'), findsNothing);
    expect(find.byType(InputChip), findsNothing);
  });

  testWidgets('a one-record field replaces its pick', (tester) async {
    List<LinkedRecord>? changed;
    await tester.pumpWidget(
      _host(
        field: _one,
        value: const LinkValue(many: false, records: [_asha]),
        selected: const [_asha],
        onChanged: (next) => changed = next,
      ),
    );

    await tester.tap(find.text('Add'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ravi'));
    await tester.pumpAndSettle();

    expect(changed?.map((r) => r.id), ['r']);
  });

  testWidgets('a many-record field adds to its picks and removes one', (
    tester,
  ) async {
    List<LinkedRecord>? changed;
    await tester.pumpWidget(
      _host(
        field: _many,
        value: const LinkValue(records: [_asha], hidden: 3),
        selected: const [_asha],
        onChanged: (next) => changed = next,
      ),
    );

    expect(find.text("and 3 you can't open"), findsOneWidget);

    await tester.tap(find.text('Add'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Meera'));
    await tester.pumpAndSettle();
    expect(changed?.map((r) => r.id), ['a', 'm']);

    await tester.tap(find.byTooltip('Remove Asha'));
    await tester.pumpAndSettle();
    expect(changed, isEmpty);
  });
}
