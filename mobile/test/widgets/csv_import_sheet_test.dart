import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:bottle_crm/providers/csv_import_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:bottle_crm/widgets/forms/csv_import_sheet.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../helpers/fake_platform_file.dart';

class _QueueClient extends http.BaseClient {
  final List<(int, String, Completer<void>?)> replies = [];
  final List<http.BaseRequest> requests = [];
  int get sent => requests.length;

  void reply(int status, String body, {Completer<void>? gate}) =>
      replies.add((status, body, gate));

  String? mappingOf(int i) =>
      (requests[i] as http.MultipartRequest).fields['mapping'];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requests.add(request);
    await request.finalize().toBytes();
    final (status, body, gate) = replies.removeAt(0);
    if (gate != null) await gate.future;
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

String _previewBody({int valid = 2, int errorCount = 0}) => jsonEncode({
  'header_error': null,
  'valid': [
    for (var i = 1; i <= valid; i++)
      {
        'row': i,
        'name': 'Ticket $i',
        'status': 'New',
        'priority': 'High',
        'account_id': null,
      },
  ],
  'errors': [
    for (var i = 0; i < errorCount; i++)
      {
        'row': i + 3,
        'field': 'name',
        'message':
            'Duplicate name also used by row 1 in this file, so this row '
            'cannot be imported until one of the two is changed',
      },
  ],
  'summary': {
    'total': valid + errorCount,
    'valid': valid,
    'invalid': errorCount,
  },
});

const _fields = [
  {'name': 'first_name', 'label': 'First name', 'required': true},
  {'name': 'last_name', 'label': 'Last name', 'required': true},
  {'name': 'email', 'label': 'Email', 'required': false},
  {'name': 'phone', 'label': 'Phone', 'required': false},
  {
    'name': 'full_name',
    'label': 'Full name (split into first and last)',
    'required': false,
  },
];

List<Map<String, Object?>> _columns({bool matched = true}) => [
  {
    'index': 0,
    'header': 'Name of the person as written on their business card',
    'field': matched ? 'full_name' : null,
    'samples': [
      'Ada Augusta King, Countess of Lovelace',
      'Alan Mathison Turing',
      'Grace Brewster Murray Hopper',
    ],
  },
  {
    'index': 1,
    'header': 'Email ID',
    'field': matched ? 'email' : null,
    'samples': ['ada@x.test'],
  },
  {
    'index': 2,
    'header': 'Mobile',
    'field': null,
    'samples': ['98765 43210'],
  },
  {'index': 3, 'header': 'Fax', 'field': null, 'samples': []},
];

String _mappedBody({
  int valid = 2,
  bool matched = true,
  List<Map<String, Object?>> skipped = const [],
  List<Map<String, Object>> dropped = const [],
}) => jsonEncode({
  'columns': _columns(matched: matched),
  'fields': _fields,
  'valid': [
    for (var i = 1; i <= valid; i++)
      {'row': i, 'first_name': 'Person', 'last_name': '$i'},
  ],
  'skipped': skipped,
  'dropped': dropped,
  'summary': {
    'total': valid + skipped.length,
    'valid': valid,
    'skipped': skipped.length,
  },
});

Map<String, Object?> _skip(
  int row, {
  String kind = 'row',
  String message = 'A contact needs a first and a last name.',
  List<String> cells = const ['Plato', '=1+1', '98765'],
}) => {
  'row': row,
  'field': 'last_name',
  'message': message,
  'cells': cells,
  'kind': kind,
};

/// A successful mapped commit (`commit_mapped`): what it created, and the
/// rows and values it left out.
String _committed({
  int created = 2,
  List<Map<String, Object?>> skipped = const [],
  List<Map<String, Object>> dropped = const [],
}) => jsonEncode({
  'error': false,
  'created': created,
  'ids': [for (var i = 0; i < created; i++) 'id$i'],
  'skipped': skipped,
  'dropped': dropped,
});

void main() {
  late _QueueClient client;
  late int refreshed;

  setUp(() {
    client = _QueueClient();
    ApiService().setClientForTesting(client);
    refreshed = 0;
  });

  /// A 390px phone, as the other layout tests use, at [textScale]; or
  /// another [size].
  void usePhone(
    WidgetTester tester, {
    double textScale = 1.0,
    Size size = const Size(390, 844),
  }) {
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = size * 3;
    tester.platformDispatcher.textScaleFactorTestValue = textScale;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  }

  Future<void> open(
    WidgetTester tester, {
    CsvImportTarget target = CsvImportTarget.contacts,
    double textScale = 1.0,
    String fileName = 'people.csv',
    Size size = const Size(390, 844),
    Future<String?> Function(String fileName, List<int> bytes)? saveFile,
  }) async {
    usePhone(tester, textScale: textScale, size: size);
    final bytes = Uint8List.fromList(utf8.encode('first_name,last_name\n'));
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) => Center(
                child: ElevatedButton(
                  onPressed: () => showCsvImportSheet(
                    context,
                    target,
                    onImported: () => refreshed++,
                    pickFile: () async => FakePlatformFile(
                      name: fileName,
                      size: bytes.length,
                      bytes: bytes,
                    ),
                    saveFile: saveFile,
                  ),
                  child: const Text('open'),
                ),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
  }

  Future<void> choose(WidgetTester tester, CsvImportTarget target) async {
    await tester.tap(
      find.text(
        target.usesMapping ? 'Choose a spreadsheet' : 'Choose CSV file',
      ),
    );
    await tester.pumpAndSettle();
  }

  FilledButton importButton(WidgetTester tester) => tester.widget<FilledButton>(
    find.ancestor(
      of: find.textContaining(RegExp(r'^Import \d')),
      matching: find.byWidgetPredicate((w) => w is FilledButton),
    ),
  );

  Finder pickers() => find.byType(DropdownButtonFormField<String>);

  /// Pick [label] in the field menu of the [n]th column card. Stops once the
  /// menu has closed, inside the debounce, so nothing has been sent yet.
  Future<void> pick(WidgetTester tester, int n, String label) async {
    await tester.ensureVisible(pickers().at(n));
    await tester.tap(pickers().at(n));
    await tester.pumpAndSettle();
    await tester.tap(find.text(label).last);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
  }

  for (final scale in [1.0, 1.3]) {
    testWidgets('the empty sheet fits a phone at ${scale}x text', (
      tester,
    ) async {
      for (final target in CsvImportTarget.values) {
        await open(tester, target: target, textScale: scale);

        expect(tester.takeException(), isNull);
        if (target.usesMapping) {
          expect(find.text('Import ${target.plural}'), findsOneWidget);
          expect(
            find.text(
              'Any column names work. You\'ll check how they match before '
              'anything is imported.',
            ),
            findsOneWidget,
          );
          expect(find.text('.xlsx or .csv, up to 5 MB.'), findsOneWidget);
          expect(find.text('Choose a spreadsheet'), findsOneWidget);
        } else {
          expect(find.text('Import ${target.plural} from CSV'), findsOneWidget);
          expect(find.text('CSV format'), findsOneWidget);
          expect(find.text('Choose CSV file'), findsOneWidget);
        }
        expect(find.text('Save CSV template'), findsOneWidget);
        // The primary action is a full 44px target.
        expect(
          tester.getSize(find.byType(FilledButton)).height,
          greaterThanOrEqualTo(44),
        );

        await tester.tap(find.byTooltip('Close'));
        await tester.pumpAndSettle();
      }
    });

    testWidgets(
      'the column matcher fits and changing a field re-previews at ${scale}x',
      (tester) async {
        client
          ..reply(200, _mappedBody())
          ..reply(200, _mappedBody(valid: 5));
        await open(tester, textScale: scale);
        await choose(tester, CsvImportTarget.contacts);

        expect(tester.takeException(), isNull);
        expect(client.mappingOf(0), 'auto');
        expect(
          find.text('Name of the person as written on their business card'),
          findsOneWidget,
        );
        expect(find.text('Email ID'), findsOneWidget);
        expect(find.text('98765 43210'), findsOneWidget);
        // A column with no values waits behind a toggle, as on the web.
        expect(find.text('Fax'), findsNothing);
        expect(pickers(), findsNWidgets(3));
        expect(find.text('2 contacts will be imported.'), findsOneWidget);
        expect(importButton(tester).onPressed, isNotNull);

        await pick(tester, 2, 'Email');

        // The field moved off the column that held it.
        expect(
          tester
              .widget<DropdownButtonFormField<String>>(pickers().at(1))
              .initialValue,
          isNull,
        );
        // Until the preview catches up, its counts are not of this choice.
        expect(client.sent, 1);
        expect(find.text('Updating the preview'), findsOneWidget);
        expect(importButton(tester).onPressed, isNull);
        // The debounce has passed, so the preview was asked again.
        await tester.pump(const Duration(milliseconds: 400));
        await tester.pumpAndSettle();
        expect(client.sent, 2);
        expect(
          client.mappingOf(1),
          '{"0":"full_name","1":null,"2":"email","3":null}',
        );
        expect(find.text('5 contacts will be imported.'), findsOneWidget);
        expect(find.text('Import 5 contacts'), findsOneWidget);
        expect(tester.takeException(), isNull);

        await tester.ensureVisible(find.text('Show 1 empty column'));
        await tester.tap(find.text('Show 1 empty column'));
        await tester.pumpAndSettle();
        expect(find.text('Fax'), findsOneWidget);
        expect(find.text('No values'), findsOneWidget);
        expect(find.text('Hide the empty columns'), findsOneWidget);
        expect(tester.takeException(), isNull);
        // Every picker is a full-height target.
        for (var i = 0; i < 4; i++) {
          expect(
            tester.getSize(pickers().at(i)).height,
            greaterThanOrEqualTo(44),
          );
        }
      },
    );

    testWidgets('dropped values and skipped counts are shown at ${scale}x', (
      tester,
    ) async {
      client.reply(
        200,
        _mappedBody(
          skipped: [
            _skip(3),
            _skip(4),
            _skip(5, kind: 'duplicate'),
          ],
          dropped: [
            {'field': 'email', 'count': 12},
            {'field': 'phone', 'count': 1},
          ],
        ),
      );
      await open(tester, textScale: scale);
      await choose(tester, CsvImportTarget.contacts);

      expect(tester.takeException(), isNull);
      expect(
        find.text("Email: 12 values we couldn't use were left blank."),
        findsOneWidget,
      );
      expect(
        find.text("Phone: 1 value we couldn't use was left blank."),
        findsOneWidget,
      );
      expect(
        find.text('2 contacts will be imported, and 3 rows will be skipped.'),
        findsOneWidget,
      );
      expect(find.textContaining('Row 3'), findsOneWidget);
      expect(find.text('Save skipped rows'), findsOneWidget);
      // The list sheet offers leads as text only.
      expect(
        find.textContaining('so this file could go in as leads instead'),
        findsOneWidget,
      );
      expect(find.text('Import as leads instead'), findsNothing);
      expect(importButton(tester).onPressed, isNotNull);
    });

    testWidgets('the done step reports what the commit created, dropped and '
        'skipped at ${scale}x', (tester) async {
      client
        ..reply(
          200,
          _mappedBody(
            valid: 4,
            skipped: [_skip(6)],
            dropped: [
              {'field': 'phone', 'count': 1},
            ],
          ),
        )
        // A record arrived since the preview, so the commit skipped one more
        // row and blanked other values: the done step reports this, not the
        // preview.
        ..reply(
          200,
          _committed(
            created: 3,
            skipped: [
              _skip(2, kind: 'duplicate'),
              _skip(6),
            ],
            dropped: [
              {'field': 'email', 'count': 12},
            ],
          ),
        );
      await open(tester, textScale: scale);
      await choose(tester, CsvImportTarget.contacts);
      await tester.tap(find.text('Import 4 contacts'));
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      expect(find.text('Import contacts'), findsOneWidget);
      expect(find.text('Imported 3 contacts.'), findsOneWidget);
      expect(
        find.text("Email: 12 values we couldn't use were left blank."),
        findsOneWidget,
      );
      expect(find.textContaining('Phone:'), findsNothing);
      expect(find.text('2 rows skipped.'), findsOneWidget);
      expect(find.text('Save skipped rows'), findsOneWidget);
      // The rows' own cells go only into the saved file.
      expect(find.textContaining('Plato'), findsNothing);
      // The matching step is gone, and so are its Back and Import.
      expect(pickers(), findsNothing);
      expect(find.text('Back'), findsNothing);
      expect(find.textContaining(RegExp(r'^Import \d')), findsNothing);
      // Nothing closed, so nothing refreshed yet, and no snackbar repeats it.
      expect(refreshed, 0);
      expect(find.byType(SnackBar), findsNothing);
      // Both actions are full tap targets, on the screen.
      for (final label in ['Done', 'Save skipped rows']) {
        final button = find.ancestor(
          of: find.text(label),
          matching: find.byWidgetPredicate((w) => w is ButtonStyleButton),
        );
        final box = tester.getRect(button);
        expect(box.height, greaterThanOrEqualTo(44), reason: label);
        expect(box.right, lessThanOrEqualTo(390), reason: label);
        expect(box.bottom, lessThanOrEqualTo(844), reason: label);
      }
    });

    testWidgets("Save skipped rows saves the commit's skipped rows at "
        '${scale}x', (tester) async {
      final saved = <(String, List<int>)>[];
      client
        ..reply(200, _mappedBody(skipped: [_skip(3)]))
        ..reply(
          200,
          _committed(
            created: 1,
            skipped: [
              _skip(
                7,
                kind: 'duplicate',
                message: 'Already in BottleCRM.',
                cells: ['Hypatia', '@SUM(A1)', '555'],
              ),
            ],
          ),
        );
      await open(
        tester,
        textScale: scale,
        saveFile: (name, bytes) async {
          saved.add((name, bytes));
          return '/tmp/$name';
        },
      );
      await choose(tester, CsvImportTarget.contacts);
      // The preview's rows, saved before importing.
      await tester.ensureVisible(find.text('Save skipped rows'));
      await tester.tap(find.text('Save skipped rows'));
      await tester.pumpAndSettle();
      expect(find.text('Saved contacts-skipped-rows.csv.'), findsOneWidget);

      await tester.tap(find.text('Import 2 contacts'));
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      expect(find.text('Imported 1 contact.'), findsOneWidget);
      expect(find.text('1 row skipped.'), findsOneWidget);
      // That save was of the preview's rows, so it is not reported here.
      expect(find.text('Saved contacts-skipped-rows.csv.'), findsNothing);

      await tester.tap(find.text('Save skipped rows'));
      await tester.pumpAndSettle();

      expect(saved, hasLength(2));
      expect(saved.last.$1, 'contacts-skipped-rows.csv');
      expect(saved.last.$2.take(3), [0xEF, 0xBB, 0xBF]);
      final lines = utf8.decode(saved.last.$2.skip(3).toList()).split('\n');
      expect(lines, [
        'Name of the person as written on their business card,Email ID,Mobile,'
            'Fax,Reason',
        "Hypatia,'@SUM(A1),555,,Already in BottleCRM.",
      ]);
      expect(find.text('Saved contacts-skipped-rows.csv.'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('Done, Close, back and a tap outside all close the done step '
        'and refresh the list at ${scale}x', (tester) async {
      const ways = ['Done', 'Close', 'back', 'outside'];
      for (var i = 0; i < ways.length; i++) {
        client
          ..reply(200, _mappedBody())
          ..reply(200, _committed());
      }
      await open(tester, textScale: scale);

      for (var i = 0; i < ways.length; i++) {
        if (i > 0) {
          await tester.tap(find.text('open'));
          await tester.pumpAndSettle();
        }
        await choose(tester, CsvImportTarget.contacts);
        await tester.tap(find.text('Import 2 contacts'));
        await tester.pumpAndSettle();
        expect(find.text('Imported 2 contacts.'), findsOneWidget);
        expect(refreshed, i, reason: ways[i]);

        switch (ways[i]) {
          case 'Done':
            await tester.tap(find.text('Done'));
          case 'Close':
            await tester.tap(find.byTooltip('Close'));
          case 'back':
            await tester
                .state<NavigatorState>(find.byType(Navigator))
                .maybePop();
          case 'outside':
            await tester.tapAt(const Offset(195, 20));
        }
        await tester.pumpAndSettle();

        expect(find.text('Import contacts'), findsNothing, reason: ways[i]);
        expect(refreshed, i + 1, reason: ways[i]);
        expect(find.byType(SnackBar), findsNothing, reason: ways[i]);
      }
      expect(tester.takeException(), isNull);
    });

    testWidgets('a commit that skipped nothing shows no skipped line and no '
        'save button at ${scale}x', (tester) async {
      client
        ..reply(200, _mappedBody())
        ..reply(200, _committed());
      await open(tester, textScale: scale);
      await choose(tester, CsvImportTarget.contacts);
      await tester.tap(find.text('Import 2 contacts'));
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      expect(find.text('Imported 2 contacts.'), findsOneWidget);
      expect(find.textContaining('skipped'), findsNothing);
      expect(find.text('Save skipped rows'), findsNothing);
      expect(find.textContaining('left blank'), findsNothing);
      expect(find.text('Done'), findsOneWidget);
    });
  }

  testWidgets('the done step still fits a tablet at 1.3x text', (tester) async {
    const tablet = Size(1024, 768);
    client
      ..reply(200, _mappedBody(skipped: [_skip(3)]))
      ..reply(
        200,
        _committed(
          skipped: [_skip(3)],
          dropped: [
            {'field': 'email', 'count': 2},
          ],
        ),
      );
    await open(tester, textScale: 1.3, size: tablet);
    await choose(tester, CsvImportTarget.contacts);
    await tester.tap(find.text('Import 2 contacts'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    for (final label in [
      'Imported 2 contacts.',
      "Email: 2 values we couldn't use were left blank.",
      '1 row skipped.',
      'Save skipped rows',
      'Done',
    ]) {
      final box = tester.getRect(find.text(label));
      expect(box.right, lessThanOrEqualTo(tablet.width), reason: label);
      expect(box.bottom, lessThanOrEqualTo(tablet.height), reason: label);
    }
    expect(
      tester.getSize(find.widgetWithText(FilledButton, 'Done')).height,
      greaterThanOrEqualTo(44),
    );

    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();
    expect(refreshed, 1);
  });

  testWidgets('the skipped rows save with the file\'s own columns and a '
      'reason, formula-safe', (tester) async {
    final saved = <(String, List<int>)>[];
    client.reply(200, _mappedBody(skipped: [_skip(3)]));
    await open(
      tester,
      saveFile: (name, bytes) async {
        saved.add((name, bytes));
        return '/tmp/$name';
      },
    );
    await choose(tester, CsvImportTarget.contacts);

    await tester.ensureVisible(find.text('Save skipped rows'));
    await tester.tap(find.text('Save skipped rows'));
    await tester.pumpAndSettle();

    expect(saved.single.$1, 'contacts-skipped-rows.csv');
    // A byte-order mark, as the web's download carries, so Excel reads
    // accented names as UTF-8.
    expect(saved.single.$2.take(3), [0xEF, 0xBB, 0xBF]);
    final lines = utf8.decode(saved.single.$2.skip(3).toList()).split('\n');
    expect(
      lines.first,
      'Name of the person as written on their business card,Email ID,Mobile,'
      'Fax,Reason',
    );
    expect(
      lines[1],
      "Plato,'=1+1,98765,,A contact needs a first and a last name.",
    );
    expect(find.text('Saved contacts-skipped-rows.csv.'), findsOneWidget);
  });

  testWidgets('a long skipped list shows the first 50 and says how many '
      'more the saved file holds', (tester) async {
    client.reply(
      200,
      _mappedBody(skipped: [for (var i = 1; i <= 52; i++) _skip(i)]),
    );
    await open(tester);
    await choose(tester, CsvImportTarget.contacts);

    expect(find.text('2 rows more are in the download.'), findsOneWidget);
    expect(
      find.text('2 contacts will be imported, and 52 rows will be skipped.'),
      findsOneWidget,
    );
  });

  testWidgets('a re-preview the throttle refused can be tried again', (
    tester,
  ) async {
    client
      ..reply(200, _mappedBody())
      ..reply(429, '{"detail": "Request was throttled."}')
      ..reply(200, _mappedBody(valid: 4));
    await open(tester);
    await choose(tester, CsvImportTarget.contacts);

    await pick(tester, 2, 'Phone');
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();

    expect(
      find.text('Too many tries in a minute. Wait a moment, then try again.'),
      findsOneWidget,
    );
    // Nothing is updating any more, so no spinner says it is.
    expect(find.text('Updating the preview'), findsNothing);
    expect(importButton(tester).onPressed, isNull);

    await tester.ensureVisible(find.text('Try again'));
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();

    expect(
      client.mappingOf(2),
      '{"0":"full_name","1":"email","2":"phone","3":null}',
    );
    expect(find.text('Try again'), findsNothing);
    expect(find.text('4 contacts will be imported.'), findsOneWidget);
    expect(importButton(tester).onPressed, isNotNull);
  });

  testWidgets('a sheet whose first row is a title says nothing matched and '
      'refuses nothing', (tester) async {
    client.reply(
      200,
      _mappedBody(valid: 0, matched: false, skipped: [_skip(1)]),
    );
    await open(tester);
    await choose(tester, CsvImportTarget.contacts);

    expect(
      find.text(
        "We couldn't match any columns. Make sure the first row of your "
        'sheet holds the column names.',
      ),
      findsOneWidget,
    );
    expect(find.text('Nothing in this file can be imported.'), findsOneWidget);
    expect(importButton(tester).onPressed, isNull);
    expect(pickers(), findsNWidgets(3));
  });

  testWidgets('the pickers and Import are locked while the import runs', (
    tester,
  ) async {
    final gate = Completer<void>();
    client
      ..reply(200, _mappedBody())
      ..reply(
        200,
        '{"error": false, "created": 2, "ids": ["a", "b"]}',
        gate: gate,
      );
    await open(tester);
    await choose(tester, CsvImportTarget.contacts);

    await tester.tap(find.text('Import 2 contacts'));
    await tester.pump();

    expect(importButton(tester).onPressed, isNull);
    for (var i = 0; i < 3; i++) {
      expect(
        tester
            .widget<DropdownButtonFormField<String>>(pickers().at(i))
            .onChanged,
        isNull,
      );
    }

    gate.complete();
    await tester.pumpAndSettle();
    // The done step reports the import; the list refreshes when it closes.
    expect(find.text('Imported 2 contacts.'), findsOneWidget);
    expect(refreshed, 0);
  });

  IconButton closeButton(WidgetTester tester) =>
      tester.widget<IconButton>(find.widgetWithIcon(IconButton, LucideIcons.x));

  testWidgets('the sheet cannot be closed while the import runs, so the '
      'result still refreshes the list', (tester) async {
    final gate = Completer<void>();
    client
      ..reply(200, _mappedBody())
      ..reply(
        200,
        '{"error": false, "created": 2, "ids": ["a", "b"]}',
        gate: gate,
      );
    await open(tester);
    await choose(tester, CsvImportTarget.contacts);
    expect(closeButton(tester).onPressed, isNotNull);

    await tester.tap(find.text('Import 2 contacts'));
    await tester.pump();

    expect(closeButton(tester).onPressed, isNull);
    // Back, a tap outside the sheet and a swipe down all leave the sheet's
    // route in place. The progress bar never settles, so these pump for a
    // fixed time.
    final navigator = tester.state<NavigatorState>(find.byType(Navigator));
    await navigator.maybePop();
    await tester.pump(const Duration(milliseconds: 500));
    expect(navigator.canPop(), isTrue);
    await tester.tapAt(const Offset(195, 20));
    await tester.pump(const Duration(milliseconds: 500));
    expect(navigator.canPop(), isTrue);
    await tester.drag(find.text('Import contacts'), const Offset(0, 600));
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pump();
    expect(navigator.canPop(), isTrue);
    expect(find.text('Import contacts'), findsOneWidget);
    expect(refreshed, 0);

    gate.complete();
    await tester.pumpAndSettle();
    // The sheet stays on its done step, and can be closed again.
    expect(find.text('Imported 2 contacts.'), findsOneWidget);
    expect(closeButton(tester).onPressed, isNotNull);
    expect(refreshed, 0);

    await navigator.maybePop();
    await tester.pumpAndSettle();
    expect(find.text('Import contacts'), findsNothing);
    expect(refreshed, 1);
  });

  testWidgets('back and a tap outside still close the sheet between imports', (
    tester,
  ) async {
    client.reply(200, _mappedBody());
    await open(tester);
    await choose(tester, CsvImportTarget.contacts);

    await tester.state<NavigatorState>(find.byType(Navigator)).maybePop();
    await tester.pumpAndSettle();
    expect(find.text('Import contacts'), findsNothing);

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
    await tester.tapAt(const Offset(195, 20));
    await tester.pumpAndSettle();
    expect(find.text('Import contacts'), findsNothing);
    expect(refreshed, 0);
  });

  testWidgets('a clean file imports with the previewed choice and reports the '
      'count on the done step', (tester) async {
    client
      ..reply(200, _mappedBody())
      ..reply(200, '{"error": false, "created": 2, "ids": ["a", "b"]}');
    await open(tester, fileName: 'people.xlsx');
    await choose(tester, CsvImportTarget.contacts);
    expect(find.text('people.xlsx'), findsOneWidget);
    expect(importButton(tester).onPressed, isNotNull);

    await tester.tap(find.text('Import 2 contacts'));
    await tester.pumpAndSettle();

    expect(client.sent, 2);
    expect(
      client.mappingOf(1),
      '{"0":"full_name","1":"email","2":null,"3":null}',
    );
    expect(find.text('Imported 2 contacts.'), findsOneWidget);
    expect(refreshed, 0);

    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();
    expect(find.text('Import contacts'), findsNothing);
    expect(refreshed, 1);
  });

  testWidgets('a 403 shows the access message and leaves the sheet open', (
    tester,
  ) async {
    client.reply(403, '{"error": true, "message": "Permission denied"}');
    await open(tester, target: CsvImportTarget.leads, textScale: 1.3);
    await choose(tester, CsvImportTarget.leads);

    expect(tester.takeException(), isNull);
    expect(find.text(csvImportForbiddenMessage), findsOneWidget);
    expect(find.text('Import leads'), findsOneWidget);
    expect(refreshed, 0);
  });

  testWidgets('closing without importing refreshes nothing', (tester) async {
    await open(tester);

    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    expect(find.text('Import contacts'), findsNothing);
    expect(refreshed, 0);
    expect(client.sent, 0);
  });

  group('tickets keep the template-only sheet', () {
    for (final scale in [1.0, 1.3]) {
      testWidgets('row errors list and block the import at ${scale}x text', (
        tester,
      ) async {
        client.reply(200, _previewBody(valid: 2, errorCount: 30));
        await open(tester, target: CsvImportTarget.tickets, textScale: scale);
        await choose(tester, CsvImportTarget.tickets);

        expect(tester.takeException(), isNull);
        expect(client.mappingOf(0), isNull);
        expect(find.text('Valid: 2'), findsOneWidget);
        expect(find.text('Invalid: 30'), findsOneWidget);
        expect(
          find.text('30 errors, fix the CSV before importing'),
          findsOneWidget,
        );
        expect(find.textContaining('Row 3'), findsOneWidget);
        expect(importButton(tester).onPressed, isNull);
        // The long list scrolls inside its own box rather than pushing the
        // buttons off the sheet.
        expect(find.text('Back'), findsOneWidget);
        expect(tester.getBottomLeft(find.text('Back')).dy, lessThan(844));
      });

      testWidgets('the valid rows are sampled, as on the web, at ${scale}x', (
        tester,
      ) async {
        client.reply(200, _previewBody(valid: 25, errorCount: 1));
        await open(tester, target: CsvImportTarget.tickets, textScale: scale);
        await choose(tester, CsvImportTarget.tickets);

        expect(tester.takeException(), isNull);
        expect(find.textContaining('Ticket 1'), findsWidgets);
        expect(find.textContaining('New · High'), findsWidgets);
        expect(find.text('Showing first 20 of 25 valid rows'), findsOneWidget);
        // The save button is a full-height target.
        expect(
          tester
              .getSize(
                find.ancestor(
                  of: find.text('Save errors as CSV'),
                  matching: find.byWidgetPredicate((w) => w is TextButton),
                ),
              )
              .height,
          greaterThanOrEqualTo(44),
        );
      });

      testWidgets('a clean import still closes with its snackbar, and no done '
          'step, at ${scale}x', (tester) async {
        client
          ..reply(200, _previewBody(valid: 2))
          ..reply(200, '{"error": false, "created": 2, "ids": ["a", "b"]}');
        await open(tester, target: CsvImportTarget.tickets, textScale: scale);
        await choose(tester, CsvImportTarget.tickets);

        await tester.tap(find.text('Import 2 tickets'));
        await tester.pumpAndSettle();

        expect(tester.takeException(), isNull);
        expect(find.text('Import tickets from CSV'), findsNothing);
        expect(find.text('Imported 2 tickets'), findsOneWidget);
        expect(find.text('Imported 2 tickets.'), findsNothing);
        expect(find.text('Done'), findsNothing);
        expect(refreshed, 1);
      });
    }

    testWidgets('the row errors save as the web drawer\'s errors file', (
      tester,
    ) async {
      final saved = <(String, String)>[];
      client.reply(200, _previewBody(valid: 1, errorCount: 2));
      await open(
        tester,
        target: CsvImportTarget.tickets,
        saveFile: (name, bytes) async {
          saved.add((name, utf8.decode(bytes)));
          return '/tmp/$name';
        },
      );

      await choose(tester, CsvImportTarget.tickets);
      await tester.ensureVisible(find.text('Save errors as CSV'));
      await tester.tap(find.text('Save errors as CSV'));
      await tester.pumpAndSettle();

      expect(saved, hasLength(1));
      expect(saved.single.$1, 'tickets-import-errors.csv');
      final lines = saved.single.$2.split('\n');
      expect(lines.first, 'row,field,message');
      expect(lines, hasLength(3));
      // The message holds a comma, so it is one quoted cell.
      expect(lines[1], startsWith('3,name,"Duplicate name also used by row 1'));
      expect(lines[1], endsWith('changed"'));
      expect(find.text('Saved tickets-import-errors.csv.'), findsOneWidget);
    });

    testWidgets('a closed save dialog says nothing, a failed one says so', (
      tester,
    ) async {
      var fail = false;
      client.reply(200, _previewBody(valid: 1, errorCount: 1));
      await open(
        tester,
        target: CsvImportTarget.tickets,
        saveFile: (name, bytes) async {
          if (fail) throw Exception('disk full');
          return null;
        },
      );
      await choose(tester, CsvImportTarget.tickets);

      await tester.ensureVisible(find.text('Save errors as CSV'));
      await tester.tap(find.text('Save errors as CSV'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Saved '), findsNothing);
      expect(find.text('Could not save the errors.'), findsNothing);

      fail = true;
      await tester.tap(find.text('Save errors as CSV'));
      await tester.pumpAndSettle();
      expect(find.text('Could not save the errors.'), findsOneWidget);
    });
  });
}
