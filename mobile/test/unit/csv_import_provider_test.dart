import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:bottle_crm/providers/csv_import_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import '../helpers/fake_platform_file.dart';

/// Answers each request with the next queued reply and keeps what was sent,
/// so a test can check the wire as well as the state. A reply queued with a
/// gate is held until the test completes the gate.
class _QueueClient extends http.BaseClient {
  final List<(int, String, Completer<void>?)> replies = [];
  final List<http.BaseRequest> sent = [];
  final List<List<int>> bodies = [];

  void reply(int status, String body, {Completer<void>? gate}) =>
      replies.add((status, body, gate));

  /// The `mapping` form field of the [i]th request, or null without one.
  String? mappingOf(int i) =>
      (sent[i] as http.MultipartRequest).fields['mapping'];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    sent.add(request);
    bodies.add(await request.finalize().toBytes());
    final (status, body, gate) = replies.removeAt(0);
    if (gate != null) await gate.future;
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

const _csv = 'first_name,last_name\nAda,Lovelace\nAlan,Turing\n';

PlatformFile _file({String name = 'people.csv', String content = _csv}) {
  final bytes = Uint8List.fromList(utf8.encode(content));
  return FakePlatformFile(name: name, size: bytes.length, bytes: bytes);
}

/// The template-only reply tickets still get, and contacts and leads get
/// from a server older than column matching.
String _previewBody({
  String? headerError,
  int valid = 2,
  List<Map<String, Object>> errors = const [],
}) => jsonEncode({
  'header_error': headerError,
  'valid': [
    for (var i = 1; i <= valid; i++) {'row': i},
  ],
  'errors': errors,
  'summary': {
    'total': valid + errors.length,
    'valid': valid,
    'invalid': errors.length,
  },
});

const _columns = [
  {
    'index': 0,
    'header': 'Name',
    'field': 'full_name',
    'samples': ['Ada Lovelace'],
  },
  {
    'index': 1,
    'header': 'Email ID',
    'field': 'email',
    'samples': ['ada@x.test'],
  },
  {
    'index': 2,
    'header': 'Mobile',
    'field': null,
    'samples': ['98765 43210'],
  },
];

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

/// The column-matching reply (`MappedPreview.to_dict`).
String _mappedBody({
  List<Map<String, Object?>> columns = _columns,
  int valid = 2,
  List<Map<String, Object?>> skipped = const [],
  List<Map<String, Object>> dropped = const [],
}) => jsonEncode({
  'columns': columns,
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
  String field = 'last_name',
  String message = 'A contact needs a first and a last name.',
  List<String> cells = const ['Plato', 'plato@x.test', ''],
  String kind = 'row',
}) => {
  'row': row,
  'field': field,
  'message': message,
  'cells': cells,
  'kind': kind,
};

CsvImportPreview _preview({
  int total = 0,
  int valid = 0,
  List<CsvSkippedRow> skipped = const [],
}) => CsvImportPreview(
  total: total,
  valid: valid,
  invalid: 0,
  errors: const [],
  columns: const [],
  skipped: skipped,
  skippedCount: skipped.length,
);

CsvSkippedRow _row(String kind, {String field = 'email', int row = 1}) =>
    CsvSkippedRow(
      row: row,
      field: field,
      message: 'm',
      cells: const [],
      kind: kind,
    );

void main() {
  late _QueueClient client;
  late ProviderContainer container;

  setUp(() {
    client = _QueueClient();
    ApiService().setClientForTesting(client);
    container = ProviderContainer();
  });

  tearDown(() => container.dispose());

  /// The provider is autoDispose, so a listener stands in for the open sheet.
  CsvImportNotifier notifier([
    CsvImportTarget target = CsvImportTarget.contacts,
  ]) {
    container.listen(csvImportProvider(target), (_, _) {});
    return container.read(csvImportProvider(target).notifier);
  }

  CsvImportState stateOf([CsvImportTarget target = CsvImportTarget.contacts]) =>
      container.read(csvImportProvider(target));

  group('template-only preview (tickets)', () {
    test('sends the file as multipart `file`, no mapping, and reads the '
        'counts', () async {
      client.reply(200, _previewBody());

      await notifier(CsvImportTarget.tickets).choose(_file());

      final request = client.sent.single as http.MultipartRequest;
      expect(request.url.path, endsWith('/api/cases/import/preview/'));
      expect(request.files.single.field, 'file');
      expect(request.files.single.filename, 'people.csv');
      expect(request.headers['Content-Type'], startsWith('multipart/'));
      // Tickets keep the template-only import: no `mapping` is sent.
      expect(request.fields, isEmpty);
      final state = stateOf(CsvImportTarget.tickets);
      expect(state.preview!.valid, 2);
      expect(state.preview!.total, 2);
      expect(state.error, isNull);
      expect(state.canCommit, isTrue);
    });

    test('a header_error blocks the commit and sends nothing', () async {
      client.reply(
        200,
        _previewBody(
          headerError: 'Missing required header(s): status',
          valid: 0,
        ),
      );
      final n = notifier(CsvImportTarget.tickets);

      await n.choose(_file());

      final state = stateOf(CsvImportTarget.tickets);
      expect(state.preview!.headerError, 'Missing required header(s): status');
      expect(state.canCommit, isFalse);
      expect(await n.commit(), isFalse);
      expect(client.sent, hasLength(1));
    });

    test('row errors are listed and block the commit, which would refuse '
        'the whole file', () async {
      client.reply(
        200,
        _previewBody(
          valid: 1,
          errors: [
            {'row': 2, 'field': 'status', 'message': 'Unknown status'},
          ],
        ),
      );
      final n = notifier(CsvImportTarget.tickets);

      await n.choose(_file());

      final errors = stateOf(CsvImportTarget.tickets).preview!.errors;
      expect(errors.single.row, 2);
      expect(errors.single.field, 'status');
      expect(errors.single.message, 'Unknown status');
      expect(stateOf(CsvImportTarget.tickets).canCommit, isFalse);
      expect(await n.commit(), isFalse);
      expect(client.sent, hasLength(1));
    });

    test('a file with no valid rows cannot be committed', () async {
      client.reply(200, _previewBody(valid: 0));

      await notifier(CsvImportTarget.tickets).choose(_file());

      expect(stateOf(CsvImportTarget.tickets).canCommit, isFalse);
    });

    test('a 403 says who may import, in the web wording', () async {
      client.reply(403, '{"error": true, "message": "Permission denied"}');

      await notifier().choose(_file());

      final state = stateOf();
      expect(
        state.error,
        'Importing needs an admin, or a member with sales access.',
      );
      expect(state.error, csvImportForbiddenMessage);
      expect(state.preview, isNull);
      expect(state.canCommit, isFalse);
    });

    test('a 429 asks to wait, in the web wording', () async {
      client.reply(429, '{"detail": "Request was throttled."}');

      await notifier().choose(_file());

      expect(
        stateOf().error,
        'Too many tries in a minute. Wait a moment, then try again.',
      );
    });

    test('a 413 from the proxy says the file is too large, in the web '
        'wording', () async {
      // nginx answers with its own HTML page, so there is no message to show.
      client.reply(
        413,
        '<html><head><title>413 Request Entity Too Large</title></head></html>',
      );

      await notifier().choose(_file());

      final state = stateOf();
      expect(
        state.error,
        'This file is too large to upload. Split it into smaller files.',
      );
      expect(state.error, csvImportTooLargeMessage);
      expect(state.preview, isNull);
    });
  });

  group('template-only commit (tickets)', () {
    test('re-sends the same bytes and reports what was created', () async {
      client
        ..reply(200, _previewBody())
        ..reply(200, '{"error": false, "created": 2, "ids": ["a", "b"]}');
      final n = notifier(CsvImportTarget.tickets);
      await n.choose(_file());

      expect(await n.commit(), isTrue);

      expect(client.sent, hasLength(2));
      expect(client.sent[1].url.path, endsWith('/api/cases/import/commit/'));
      expect((client.sent[1] as http.MultipartRequest).fields, isEmpty);
      // Both multipart bodies carry the CSV unchanged.
      for (final body in client.bodies) {
        expect(utf8.decode(body), contains(_csv));
      }
      expect(stateOf(CsvImportTarget.tickets).result!.created, 2);
      expect(stateOf(CsvImportTarget.tickets).error, isNull);
    });

    test(
      'a 400 keeps the preview and shows the message and the rows',
      () async {
        client
          ..reply(200, _previewBody())
          ..reply(
            400,
            jsonEncode({
              'error': true,
              'message': 'Fix the invalid rows before importing',
              'errors': [
                {'row': 1, 'field': 'name', 'message': 'Duplicate name'},
              ],
              'created': 0,
            }),
          );
        final n = notifier(CsvImportTarget.tickets);
        await n.choose(_file());

        expect(await n.commit(), isFalse);

        final state = stateOf(CsvImportTarget.tickets);
        expect(state.error, 'Fix the invalid rows before importing');
        expect(state.commitErrors.single.message, 'Duplicate name');
        expect(state.preview, isNotNull);
        expect(state.result, isNull);
      },
    );

    test('a 400 carrying only header_error shows it', () async {
      client
        ..reply(200, _previewBody())
        ..reply(
          400,
          '{"error": true, "header_error": "CSV is empty", "created": 0}',
        );
      final n = notifier(CsvImportTarget.tickets);
      await n.choose(_file());

      expect(await n.commit(), isFalse);
      expect(stateOf(CsvImportTarget.tickets).error, 'CSV is empty');
    });

    test('a 403 at commit uses the same wording as at preview', () async {
      client
        ..reply(200, _previewBody())
        ..reply(403, '{"error": true, "message": "Permission denied"}');
      final n = notifier(CsvImportTarget.tickets);
      await n.choose(_file());

      expect(await n.commit(), isFalse);
      expect(stateOf(CsvImportTarget.tickets).error, csvImportForbiddenMessage);
    });
  });

  group('refused before upload', () {
    test('an .xls file is refused for contacts', () async {
      await notifier().choose(_file(name: 'people.xls'));

      expect(stateOf().error, contains('Save it as .xlsx or .csv'));
      expect(stateOf().error, 'Save it as .xlsx or .csv and try again.');
      expect(stateOf().file, isNull);
      expect(client.sent, isEmpty);
    });

    test('an .xlsx file is accepted for contacts and leads', () async {
      for (final target in [CsvImportTarget.contacts, CsvImportTarget.leads]) {
        client.reply(200, _mappedBody());

        await notifier(target).choose(_file(name: 'People.XLSX'));

        expect(stateOf(target).error, isNull, reason: target.name);
        expect(stateOf(target).file!.name, 'People.XLSX');
      }
      expect(client.sent, hasLength(2));
      expect(
        client.sent[0].url.path,
        endsWith('/api/contacts/import/preview/'),
      );
      expect(client.sent[1].url.path, endsWith('/api/leads/import/preview/'));
    });

    test('an .xlsx file is refused for tickets', () async {
      await notifier(CsvImportTarget.tickets).choose(_file(name: 'a.xlsx'));

      expect(
        stateOf(CsvImportTarget.tickets).error,
        'a.xlsx is not a CSV file. Choose a file ending in .csv.',
      );
      expect(client.sent, isEmpty);
    });

    test('an upper-case .CSV extension is accepted', () async {
      client.reply(200, _mappedBody());

      await notifier().choose(_file(name: 'PEOPLE.CSV'));

      expect(stateOf().error, isNull);
      expect(client.sent, hasLength(1));
    });

    test('a file the picker reports as over 5 MB, before reading it', () async {
      final bytes = Uint8List.fromList(utf8.encode(_csv));
      await notifier().choose(
        FakePlatformFile(name: 'big.xlsx', size: 6 * 1024 * 1024, bytes: bytes),
      );
      await notifier(CsvImportTarget.tickets).choose(
        FakePlatformFile(name: 'big.csv', size: 6 * 1024 * 1024, bytes: bytes),
      );

      expect(
        stateOf().error,
        'big.xlsx is 6.0 MB. Files must be 5 MB or smaller.',
      );
      expect(
        stateOf(CsvImportTarget.tickets).error,
        'big.csv is 6.0 MB. CSV files must be 5 MB or smaller.',
      );
      expect(client.sent, isEmpty);
    });

    test('bytes over 5 MB when the picker did not know the size', () async {
      final bytes = Uint8List(csvImportMaxBytes + 1);
      await notifier(
        CsvImportTarget.tickets,
      ).choose(FakePlatformFile(name: 'big.csv', size: 0, bytes: bytes));

      expect(
        stateOf(CsvImportTarget.tickets).error,
        contains('CSV files must be 5 MB or smaller'),
      );
      expect(client.sent, isEmpty);
    });

    test('exactly 5 MB is allowed through', () async {
      client.reply(200, _mappedBody());
      final bytes = Uint8List(csvImportMaxBytes);
      await notifier().choose(
        FakePlatformFile(name: 'edge.csv', size: bytes.length, bytes: bytes),
      );

      expect(stateOf().error, isNull);
      expect(client.sent, hasLength(1));
    });

    test('an empty file', () async {
      await notifier().choose(_file(content: ''));
      await notifier(CsvImportTarget.tickets).choose(_file(content: ''));

      // The web's sentence for contacts and leads; tickets keep theirs.
      expect(stateOf().error, 'Choose a file.');
      expect(stateOf(CsvImportTarget.tickets).error, 'Choose a CSV file.');
      expect(client.sent, isEmpty);
    });

    test('closing the picker changes nothing', () async {
      await notifier().choose(null);

      expect(stateOf().error, isNull);
      expect(stateOf().file, isNull);
      expect(client.sent, isEmpty);
    });
  });

  group('column matching (contacts and leads)', () {
    test('only contacts and leads use it', () {
      expect(CsvImportTarget.contacts.usesMapping, isTrue);
      expect(CsvImportTarget.leads.usesMapping, isTrue);
      expect(CsvImportTarget.tickets.usesMapping, isFalse);
    });

    test('contacts preview sends mapping=auto and reads columns, skipped and '
        'dropped', () async {
      client.reply(
        200,
        _mappedBody(
          skipped: [_skip(3)],
          dropped: [
            {'field': 'phone', 'count': 2},
          ],
        ),
      );

      await notifier().choose(_file());

      expect(client.mappingOf(0), 'auto');
      final state = stateOf();
      expect(state.columns.map((c) => c.header), [
        'Name',
        'Email ID',
        'Mobile',
      ]);
      expect(state.columns.map((c) => c.field), ['full_name', 'email', null]);
      expect(state.columns.last.samples, ['98765 43210']);
      expect(state.fields.map((f) => f.label), contains('Email'));
      expect(state.fields.first.required, isTrue);
      final skipped = state.skipped.single;
      expect(skipped.row, 3);
      expect(skipped.field, 'last_name');
      expect(skipped.cells, ['Plato', 'plato@x.test', '']);
      expect(skipped.kind, 'row');
      expect(state.dropped, {'phone': 2});
      expect(state.preview!.total, 3);
      expect(state.preview!.valid, 2);
      expect(state.preview!.skippedCount, 1);
      // Skipped rows do not block the import the way row errors did.
      expect(state.stale, isFalse);
      expect(state.canCommit, isTrue);
    });

    test('changing a column re-previews with the mapping JSON and frees the '
        'field from the other column', () async {
      client
        ..reply(200, _mappedBody())
        ..reply(200, _mappedBody(valid: 3));
      final n = notifier();
      await n.choose(_file());

      final change = n.setColumnField(2, 'email');
      // The choice shows at once; the preview catches up after the debounce.
      expect(stateOf().columns.map((c) => c.field), [
        'full_name',
        null,
        'email',
      ]);
      expect(stateOf().stale, isTrue);
      expect(stateOf().canCommit, isFalse);
      expect(client.sent, hasLength(1));
      await change;

      expect(client.sent, hasLength(2));
      expect(client.mappingOf(1), '{"0":"full_name","1":null,"2":"email"}');
      expect(stateOf().preview!.valid, 3);
      expect(stateOf().stale, isFalse);
      expect(stateOf().canCommit, isTrue);
      // The server's reply does not overwrite the person's own choice.
      expect(stateOf().columns[1].field, isNull);
    });

    test('quick changes send one re-preview, and an older reply that lands '
        'late is ignored', () async {
      final gate = Completer<void>();
      client
        ..reply(200, _mappedBody())
        ..reply(200, _mappedBody(valid: 1), gate: gate)
        ..reply(200, _mappedBody(valid: 5));
      final n = notifier();
      await n.choose(_file());

      // Two changes inside the debounce make one request.
      unawaited(n.setColumnField(2, 'phone'));
      final first = n.setColumnField(2, 'first_name');
      await Future<void>.delayed(const Duration(milliseconds: 500));
      expect(client.sent, hasLength(2));
      expect(
        client.mappingOf(1),
        '{"0":"full_name","1":"email","2":"first_name"}',
      );

      // A third choice while that one is still in flight replaces it.
      await n.setColumnField(2, 'phone');
      expect(client.sent, hasLength(3));
      expect(stateOf().preview!.valid, 5);

      gate.complete();
      await first;
      await pumpEventQueue();

      expect(stateOf().preview!.valid, 5);
      expect(stateOf().previewed, '{"0":"full_name","1":"email","2":"phone"}');
      expect(stateOf().canCommit, isTrue);
    });

    test('a failed re-preview keeps the last preview, blocks the import, and '
        'trying again re-sends the choice', () async {
      client
        ..reply(200, _mappedBody())
        ..reply(429, '{"detail": "Request was throttled."}')
        ..reply(200, _mappedBody(valid: 4));
      final n = notifier();
      await n.choose(_file());

      await n.setColumnField(2, 'phone');

      expect(
        stateOf().error,
        'Too many tries in a minute. Wait a moment, then try again.',
      );
      expect(stateOf().preview!.valid, 2);
      expect(stateOf().stale, isTrue);
      expect(stateOf().canCommit, isFalse);

      await n.retryPreview();

      expect(client.mappingOf(2), '{"0":"full_name","1":"email","2":"phone"}');
      expect(stateOf().error, isNull);
      expect(stateOf().preview!.valid, 4);
      expect(stateOf().canCommit, isTrue);
    });

    test(
      'a new choice after a failed re-preview drops the old error',
      () async {
        client
          ..reply(200, _mappedBody())
          ..reply(429, '{"detail": "Request was throttled."}')
          ..reply(200, _mappedBody(valid: 3));
        final n = notifier();
        await n.choose(_file());
        await n.setColumnField(2, 'phone');
        expect(stateOf().error, isNotNull);

        final next = n.setColumnField(2, 'email');

        expect(stateOf().error, isNull);
        await next;
        expect(client.mappingOf(2), '{"0":"full_name","1":null,"2":"email"}');
        expect(stateOf().preview!.valid, 3);
      },
    );

    test('commit sends the same mapping', () async {
      client
        ..reply(200, _mappedBody())
        ..reply(200, _mappedBody())
        ..reply(
          200,
          jsonEncode({
            'error': false,
            'created': 2,
            'ids': ['a', 'b'],
            'skipped': [],
            'dropped': [],
          }),
        );
      final n = notifier(CsvImportTarget.leads);
      await n.choose(_file());
      await n.setColumnField(2, 'phone');

      expect(await n.commit(), isTrue);

      expect(client.sent[2].url.path, endsWith('/api/leads/import/commit/'));
      expect(client.mappingOf(2), client.mappingOf(1));
      expect(client.mappingOf(2), '{"0":"full_name","1":"email","2":"phone"}');
      expect(utf8.decode(client.bodies[2]), contains(_csv));
      expect(stateOf(CsvImportTarget.leads).result!.created, 2);
    });

    test('a 200 commit keeps what it created, skipped and dropped, not the '
        "preview's", () async {
      client
        ..reply(
          200,
          _mappedBody(
            skipped: [_skip(9)],
            dropped: [
              {'field': 'phone', 'count': 4},
            ],
          ),
        )
        ..reply(
          200,
          jsonEncode({
            'error': false,
            'created': 3,
            'ids': ['a', 'b', 'c'],
            'skipped': [
              _skip(4, cells: ['Plato', '=1+1', '']),
              _skip(
                6,
                field: 'email',
                message: 'Already in BottleCRM.',
                kind: 'duplicate',
              ),
            ],
            'dropped': [
              {'field': 'email', 'count': 12},
            ],
          }),
        );
      final n = notifier();
      await n.choose(_file());

      expect(await n.commit(), isTrue);

      final result = stateOf().result!;
      expect(result.created, 3);
      expect(result.skipped.map((s) => s.row), [4, 6]);
      expect(result.skipped.first.cells, ['Plato', '=1+1', '']);
      expect(result.skipped.last.kind, 'duplicate');
      expect(result.skipped.last.message, 'Already in BottleCRM.');
      expect(result.dropped, {'email': 12});
      // The preview is kept for its field labels and column headers.
      expect(stateOf().fields, isNotEmpty);
      expect(stateOf().columns, hasLength(3));
    });

    test(
      'a 200 commit that skipped and dropped nothing keeps empty lists',
      () async {
        client
          ..reply(200, _mappedBody())
          ..reply(200, '{"error": false, "created": 2, "ids": ["a", "b"]}');
        final n = notifier();
        await n.choose(_file());

        expect(await n.commit(), isTrue);

        final result = stateOf().result!;
        expect(result.created, 2);
        expect(result.skipped, isEmpty);
        expect(result.dropped, isEmpty);
      },
    );

    test('a commit right after the server guessed sends the guess as JSON, '
        'not auto', () async {
      client
        ..reply(200, _mappedBody())
        ..reply(200, '{"error": false, "created": 2, "ids": ["a", "b"]}');
      final n = notifier();
      await n.choose(_file());

      expect(await n.commit(), isTrue);

      expect(client.mappingOf(1), '{"0":"full_name","1":"email","2":null}');
    });

    test(
      'a 400 Nothing in this file can be imported keeps the preview and shows '
      'the message',
      () async {
        client
          ..reply(200, _mappedBody(valid: 1))
          ..reply(
            400,
            jsonEncode({
              'error': true,
              'message': 'Nothing in this file can be imported.',
              'skipped': [_skip(1), _skip(2)],
              'created': 0,
            }),
          );
        final n = notifier();
        await n.choose(_file());

        expect(await n.commit(), isFalse);

        final state = stateOf();
        expect(state.preview, isNotNull);
        expect(state.preview!.valid, 0);
        expect(state.skipped.map((s) => s.row), [1, 2]);
        expect(state.dropped, isEmpty);
        expect(
          csvImportSummaryLine(CsvImportTarget.contacts, state.preview!),
          'Nothing in this file can be imported.',
        );
        // The summary line says it; a second copy as an error would repeat it.
        expect(state.error, isNull);
        expect(state.canCommit, isFalse);
        expect(state.result, isNull);
      },
    );

    test('the same 400 for records that arrived since the preview says they '
        'are already in BottleCRM', () async {
      client
        ..reply(200, _mappedBody(valid: 1))
        ..reply(
          400,
          jsonEncode({
            'error': true,
            'message': 'Nothing in this file can be imported.',
            'skipped': [_skip(1, field: 'email', kind: 'duplicate')],
            'created': 0,
          }),
        );
      final n = notifier();
      await n.choose(_file());

      expect(await n.commit(), isFalse);

      expect(
        csvImportSummaryLine(CsvImportTarget.contacts, stateOf().preview!),
        'Everything in this file is already in BottleCRM.',
      );
    });

    test('a 400 without skipped rows shows the server message', () async {
      client
        ..reply(200, _mappedBody())
        ..reply(
          400,
          '{"error": true, "message": "Save it as .xlsx or .csv and try '
          'again."}',
        );
      final n = notifier();
      await n.choose(_file());

      expect(await n.commit(), isFalse);

      expect(stateOf().error, 'Save it as .xlsx or .csv and try again.');
      expect(stateOf().preview!.valid, 2);
    });

    test('starting over drops the file and the choice', () async {
      client.reply(200, _mappedBody());
      final n = notifier();
      await n.choose(_file());

      n.reset();

      expect(stateOf().file, isNull);
      expect(stateOf().preview, isNull);
      expect(stateOf().columns, isEmpty);
    });
  });

  group('web parity helpers (frontend/src/lib/import/mapping.js)', () {
    const cols = [
      CsvImportColumn(index: 0, header: 'A', field: 'email', samples: []),
      CsvImportColumn(index: 1, header: 'B', field: null, samples: []),
      CsvImportColumn(index: 2, header: 'C', field: 'phone', samples: []),
    ];

    test('setColumnField moves a field off the column that held it', () {
      final next = csvSetColumnField(cols, 1, 'email');
      expect(next.map((c) => c.field), [null, 'email', 'phone']);
      // A new list; the old one is unchanged.
      expect(cols.map((c) => c.field), ['email', null, 'phone']);
      // "Don't import" frees nothing else.
      expect(csvSetColumnField(cols, 0, null).map((c) => c.field), [
        null,
        null,
        'phone',
      ]);
    });

    test('mappingPayload is the web string exactly', () {
      expect(
        csvMappingPayload(const [
          CsvImportColumn(index: 0, header: '', field: 'email', samples: []),
          CsvImportColumn(index: 1, header: '', field: null, samples: []),
        ]),
        '{"0":"email","1":null}',
      );
    });

    test('hasAnyMatch, and the hint shown when nothing matched', () {
      expect(csvHasAnyMatch(cols), isTrue);
      expect(
        csvHasAnyMatch(
          csvSetColumnField(csvSetColumnField(cols, 0, null), 2, null),
        ),
        isFalse,
      );
      expect(
        csvImportNoMatchHint,
        "We couldn't match any columns. Make sure the first row of your sheet "
        'holds the column names.',
      );
    });

    test('droppedLines, one per field, by label', () {
      expect(
        csvDroppedLines(
          const {'phone': 1, 'email': 12, 'mystery': 3},
          const [
            CsvImportField(name: 'phone', label: 'Phone', required: false),
            CsvImportField(name: 'email', label: 'Email', required: false),
          ],
        ),
        [
          "Phone: 1 value we couldn't use was left blank.",
          "Email: 12 values we couldn't use were left blank.",
          "mystery: 3 values we couldn't use were left blank.",
        ],
      );
    });

    test('summaryLine, every sentence the web shows', () {
      String line(CsvImportPreview p) =>
          csvImportSummaryLine(CsvImportTarget.contacts, p);

      expect(line(_preview()), 'This file has no rows to import.');
      expect(
        line(
          _preview(total: 2, skipped: [_row('duplicate'), _row('duplicate')]),
        ),
        'Everything in this file is already in BottleCRM.',
      );
      expect(
        line(_preview(total: 2, skipped: [_row('duplicate'), _row('row')])),
        'Nothing in this file can be imported.',
      );
      expect(line(_preview(total: 1, valid: 1)), '1 contact will be imported.');
      expect(
        line(_preview(total: 3, valid: 3)),
        '3 contacts will be imported.',
      );
      expect(
        line(_preview(total: 3, valid: 2, skipped: [_row('duplicate')])),
        '2 contacts will be imported, and 1 duplicate row will be skipped.',
      );
      expect(
        line(
          _preview(
            total: 4,
            valid: 2,
            skipped: [_row('duplicate'), _row('duplicate')],
          ),
        ),
        '2 contacts will be imported, and 2 duplicate rows will be skipped.',
      );
      expect(
        line(_preview(total: 3, valid: 2, skipped: [_row('row')])),
        '2 contacts will be imported, and 1 row will be skipped.',
      );
      expect(
        line(
          _preview(
            total: 4,
            valid: 2,
            skipped: [_row('row'), _row('duplicate')],
          ),
        ),
        '2 contacts will be imported, and 2 rows will be skipped.',
      );
      expect(
        csvImportSummaryLine(
          CsvImportTarget.leads,
          _preview(total: 1, valid: 1),
        ),
        '1 lead will be imported.',
      );
    });

    test(
      'contacts rows skipped for a missing name suggest importing as leads',
      () {
        final lastName = _row('row', field: 'last_name');
        final firstName = _row('row', field: 'first_name');
        expect(csvSuggestLeads(CsvImportTarget.contacts, [lastName]), isTrue);
        expect(csvSuggestLeads(CsvImportTarget.contacts, [firstName]), isTrue);
        // Leads already accept one name, so there is nothing to suggest.
        expect(csvSuggestLeads(CsvImportTarget.leads, [lastName]), isFalse);
        // A duplicate person would be duplicated as a lead too.
        expect(
          csvSuggestLeads(CsvImportTarget.contacts, [
            _row('duplicate', field: 'last_name'),
          ]),
          isFalse,
        );
        // Decided by `kind` and `field`, never by the message text.
        expect(
          csvSuggestLeads(CsvImportTarget.contacts, [_row('row')]),
          isFalse,
        );
        expect(csvSuggestLeads(CsvImportTarget.contacts, const []), isFalse);
      },
    );

    test('skipped rows save with original cells and a Reason column, '
        'formula-safe', () {
      final csv = csvSkippedRowsCsv(
        ['Name', 'Email'],
        const [
          CsvSkippedRow(
            row: 2,
            field: 'email',
            message: 'Already in BottleCRM, so it was skipped',
            cells: ['Ada', '=HYPERLINK("x")'],
            kind: 'duplicate',
          ),
          CsvSkippedRow(
            row: 3,
            field: 'last_name',
            message: 'A contact needs a first and a last name.',
            cells: ['Plato'],
            kind: 'row',
          ),
          CsvSkippedRow(
            row: 4,
            field: 'last_name',
            message: 'Needs a last name',
            cells: ['@x', ' -1', 'extra'],
            kind: 'row',
          ),
        ],
      );
      expect(
        csv,
        'Name,Email,,Reason\n'
        'Ada,"\'=HYPERLINK(""x"")",,"Already in BottleCRM, so it was '
        'skipped"\n'
        'Plato,,,A contact needs a first and a last name.\n'
        "'@x,' -1,extra,Needs a last name",
      );
    });

    test('the skipped rows file is named as on the web', () {
      expect(
        CsvImportTarget.contacts.skippedFileName,
        'contacts-skipped-rows.csv',
      );
      expect(CsvImportTarget.leads.skippedFileName, 'leads-skipped-rows.csv');
    });
  });

  group('targets', () {
    test('each module posts to its own two-step import, never upload/', () {
      expect(
        CsvImportTarget.tickets.previewUrl,
        endsWith('/api/cases/import/preview/'),
      );
      expect(
        CsvImportTarget.tickets.commitUrl,
        endsWith('/api/cases/import/commit/'),
      );
      expect(
        CsvImportTarget.leads.previewUrl,
        endsWith('/api/leads/import/preview/'),
      );
      expect(
        CsvImportTarget.leads.commitUrl,
        endsWith('/api/leads/import/commit/'),
      );
      for (final t in CsvImportTarget.values) {
        expect(t.commitUrl, isNot(contains('upload')));
      }
    });

    test('every template has one example cell per header and includes the '
        'required headers', () {
      for (final t in CsvImportTarget.values) {
        expect(t.templateExample, hasLength(t.templateHeaders.length));
        expect(t.templateHeaders, containsAll(t.requiredHeaders));
        final lines = t.templateCsv.split('\n');
        expect(lines, hasLength(2));
        expect(lines.first, t.templateHeaders.join(','));
      }
    });
  });

  group('errors file and valid sample (web drawer parity)', () {
    test('errors are row,field,message, quoted and formula-safe', () {
      final csv = csvImportErrorsCsv(const [
        CsvRowError(row: 2, field: 'email', message: 'Not an email'),
        CsvRowError(row: 3, field: 'name', message: 'Say "hi", then\nleave'),
        CsvRowError(row: 4, field: 'phone', message: '=HYPERLINK("x")'),
        CsvRowError(row: 5, field: 'city', message: ' -1'),
      ]);
      expect(
        csv,
        'row,field,message\n'
        '2,email,Not an email\n'
        '3,name,"Say ""hi"", then\nleave"\n'
        '4,phone,"\'=HYPERLINK(""x"")"\n'
        "5,city,' -1",
      );
    });

    test('file names match the web drawers', () {
      expect(
        CsvImportTarget.contacts.errorsFileName,
        'contacts-import-errors.csv',
      );
      expect(
        CsvImportTarget.tickets.errorsFileName,
        'tickets-import-errors.csv',
      );
      expect(CsvImportTarget.leads.errorsFileName, 'leads-import-errors.csv');
    });

    test('each module samples the columns its web table shows', () {
      expect(
        CsvImportTarget.leads.sampleLine({
          'first_name': 'Ada',
          'last_name': 'Lovelace',
          'email': 'ada@x.test',
          'company_name': 'Engines',
          'status': 'assigned',
        }),
        (
          title: 'Ada Lovelace',
          details: 'ada@x.test \u00b7 Engines \u00b7 assigned',
        ),
      );
      expect(
        CsvImportTarget.contacts.sampleLine({
          'first_name': 'Alan',
          'last_name': '',
          'email': '',
          'phone': '+1 555',
          'organization': 'NPL',
        }),
        (title: 'Alan', details: '+1 555 \u00b7 NPL'),
      );
      expect(
        CsvImportTarget.tickets.sampleLine({
          'name': 'Login broken',
          'status': 'New',
          'priority': 'High',
          'account_id': 'a1',
        }),
        (
          title: 'Login broken',
          details: 'New \u00b7 High \u00b7 account linked',
        ),
      );
      expect(
        CsvImportTarget.tickets.sampleLine({
          'name': 'Other',
          'status': 'New',
          'priority': 'Low',
          'account_id': null,
        }).details,
        'New \u00b7 Low',
      );
    });

    test('the preview keeps the valid rows it was sent', () {
      final preview = CsvImportPreview.fromJson({
        'valid': [
          {'row': 1, 'name': 'A'},
          'junk',
        ],
        'errors': [],
        'summary': {'total': 1, 'valid': 1, 'invalid': 0},
      });
      expect(preview.validRows, [
        {'row': 1, 'name': 'A'},
      ]);
      expect(preview.mapped, isFalse);
    });
  });
}
