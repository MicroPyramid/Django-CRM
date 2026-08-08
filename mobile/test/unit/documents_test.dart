import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/data/models/crm_document.dart';
import 'package:flutter_test/flutter_test.dart';

CrmDocument doc({
  String id = 'd1',
  String title = 'Contract',
  String file = 'documents/contract.pdf',
  String status = 'active',
  List<DocumentShare> sharedTo = const [],
  List<DocumentTeamShare> teams = const [],
  int? sizeBytes = 1024,
  String? uploaderEmail = 'ada@example.com',
}) => CrmDocument(
  id: id,
  title: title,
  documentFile: file,
  status: status,
  sharedTo: sharedTo,
  teams: teams,
  sizeBytes: sizeBytes,
  uploaderEmail: uploaderEmail,
);

void main() {
  group('documentKind', () {
    test('buckets the three named groups', () {
      expect(documentKind('a.pdf'), DocumentKind.pdf);
      expect(documentKind('a.xlsx'), DocumentKind.sheet);
      expect(documentKind('a.csv'), DocumentKind.sheet);
      expect(documentKind('a.docx'), DocumentKind.text);
      expect(documentKind('a.md'), DocumentKind.text);
    });

    test('collapses everything else to a generic file', () {
      expect(documentKind('a.png'), DocumentKind.file);
      expect(documentKind('a.zip'), DocumentKind.file);
      expect(documentKind('README'), DocumentKind.file);
      expect(documentKind(''), DocumentKind.file);
    });

    test('is case insensitive, because uploads are not normalised', () {
      expect(documentKind('SCAN.PDF'), DocumentKind.pdf);
    });

    test('reads the LAST dot, not the first', () {
      // `my.notes.backup.pdf` is a PDF. Splitting on the first dot would call
      // it a `notes` file and fall through to the generic icon.
      expect(documentKind('my.notes.backup.pdf'), DocumentKind.pdf);
    });
  });

  group('documentFileName', () {
    test('drops the upload directory the API prefixes', () {
      expect(documentFileName('documents/2026/contract.pdf'), 'contract.pdf');
    });

    test('leaves a bare filename alone', () {
      expect(documentFileName('contract.pdf'), 'contract.pdf');
      expect(documentFileName(''), '');
    });
  });

  group('documentSizeLabel', () {
    test('scales through bytes, kB and MB', () {
      expect(documentSizeLabel(512), '512 B');
      expect(documentSizeLabel(2048), '2 kB');
      expect(documentSizeLabel(5 * 1024 * 1024), '5.0 MB');
    });

    test('says unknown rather than zero when the server could not stat it', () {
      // `DocumentSerializer.get_size_bytes` returns None for a row whose file
      // is missing. Printing "0 B" would assert something false about the file.
      expect(documentSizeLabel(null), 'Size unknown');
    });

    test('handles an actually empty file', () {
      expect(documentSizeLabel(0), '0 B');
    });
  });

  group('documentShareSummary', () {
    test('says plainly when a document reaches nobody', () {
      expect(documentShareSummary(doc()), contains('nobody'));
    });

    test('names the people it is shared with', () {
      final summary = documentShareSummary(
        doc(
          sharedTo: const [
            DocumentShare(id: 'p1', name: 'Ada'),
            DocumentShare(id: 'p2', name: 'Grace'),
          ],
        ),
      );
      expect(summary, contains('Ada'));
      expect(summary, contains('Grace'));
    });

    test('names a team with its size, not its members', () {
      // A team share follows the team. Listing today's members would go stale
      // the moment somebody joined, and would say the wrong thing about what
      // the stored share means.
      final summary = documentShareSummary(
        doc(
          teams: const [
            DocumentTeamShare(id: 't1', name: 'Support', memberCount: 3),
          ],
        ),
      );
      expect(summary, contains('Support (3)'));
    });

    test('shows both kinds of share at once', () {
      final summary = documentShareSummary(
        doc(
          sharedTo: const [DocumentShare(id: 'p1', name: 'Ada')],
          teams: const [
            DocumentTeamShare(id: 't1', name: 'Support', memberCount: 3),
          ],
        ),
      );
      expect(summary, contains('Ada'));
      expect(summary, contains('Support (3)'));
      expect(summary, isNot(contains('nobody')));
    });
  });

  group('canWriteDocument', () {
    test('lets an admin write anything', () {
      expect(
        canWriteDocument(
          isAdmin: true,
          myEmail: 'someone@example.com',
          uploaderEmail: 'ada@example.com',
        ),
        isTrue,
      );
    });

    test('lets the uploader write their own', () {
      expect(
        canWriteDocument(
          isAdmin: false,
          myEmail: 'ada@example.com',
          uploaderEmail: 'ada@example.com',
        ),
        isTrue,
      );
    });

    test('refuses somebody the document was merely shared with', () {
      // The finding this mirrors: PUT used to authorise on `_may_read`, so
      // anyone in `shared_to` could overwrite the file, rename it, archive it,
      // and wipe the share list. A share is a copy to work with, not the
      // original to rewrite.
      expect(
        canWriteDocument(
          isAdmin: false,
          myEmail: 'grace@example.com',
          uploaderEmail: 'ada@example.com',
        ),
        isFalse,
      );
    });

    test('ignores case and surrounding space on both sides', () {
      expect(
        canWriteDocument(
          isAdmin: false,
          myEmail: ' Ada@Example.com ',
          uploaderEmail: 'ada@example.com',
        ),
        isTrue,
      );
    });

    test(
      'refuses when either side is unknown, so nothing is offered blind',
      () {
        expect(
          canWriteDocument(
            isAdmin: false,
            myEmail: null,
            uploaderEmail: 'ada@example.com',
          ),
          isFalse,
        );
        expect(
          canWriteDocument(
            isAdmin: false,
            myEmail: 'ada@example.com',
            uploaderEmail: null,
          ),
          isFalse,
        );
        expect(
          canWriteDocument(isAdmin: false, myEmail: '', uploaderEmail: ''),
          isFalse,
        );
      },
    );

    test('an admin is not blocked by an unknown uploader', () {
      expect(
        canWriteDocument(isAdmin: true, myEmail: null, uploaderEmail: null),
        isTrue,
      );
    });
  });

  group('documentTotals', () {
    test('splits active from archived and counts the unshared', () {
      final totals = documentTotals([
        doc(id: 'a'),
        doc(id: 'b', status: 'inactive'),
        doc(
          id: 'c',
          sharedTo: const [DocumentShare(id: 'p1', name: 'Ada')],
        ),
      ]);
      expect(totals.count, 3);
      expect(totals.active, 2);
      expect(totals.archived, 1);
      // a and b reach nobody; c reaches Ada.
      expect(totals.unshared, 2);
    });

    test('counts a team-only share as shared', () {
      final totals = documentTotals([
        doc(
          teams: const [
            DocumentTeamShare(id: 't1', name: 'Support', memberCount: 2),
          ],
        ),
      ]);
      expect(totals.unshared, 0);
    });

    test('is all zeroes for an empty list', () {
      expect(documentTotals(const []).count, 0);
    });
  });

  group('CrmDocument.fromJson', () {
    test('reads the shapes the serializer actually sends', () {
      final parsed = CrmDocument.fromJson({
        'id': 'd1',
        'title': 'Contract',
        'document_file': 'documents/contract.pdf',
        'status': 'active',
        'shared_to': [
          {
            'id': 'p1',
            'user_details': {'name': 'Ada', 'email': 'ada@example.com'},
          },
        ],
        'teams': [
          {'id': 't1', 'name': 'Support', 'member_count': 3},
        ],
        'size_bytes': 2048,
        'created_at': '2026-08-01T10:00:00Z',
        'created_by': {'id': 'u1', 'name': 'Ada', 'email': 'ada@example.com'},
      });

      // `shared_to` is a ProfileSerializer, so this id is a PROFILE id, which
      // is what the write path takes back.
      expect(parsed.sharedTo.single.id, 'p1');
      expect(parsed.sharedTo.single.name, 'Ada');
      expect(parsed.teams.single.memberCount, 3);
      // `created_by` is a UserSerializer, so this is the USER's email, which is
      // what `canWriteDocument` compares against.
      expect(parsed.uploaderEmail, 'ada@example.com');
      expect(parsed.kind, DocumentKind.pdf);
      expect(parsed.fileName, 'contract.pdf');
    });

    test('survives a size the server could not compute', () {
      final parsed = CrmDocument.fromJson({'id': 'd1', 'size_bytes': null});
      expect(parsed.sizeBytes, isNull);
      expect(documentSizeLabel(parsed.sizeBytes), 'Size unknown');
    });

    test('survives a payload with nothing in it', () {
      final parsed = CrmDocument.fromJson(const {});
      expect(parsed.id, '');
      expect(parsed.status, 'active');
      expect(parsed.uploaderName, 'Unknown');
      expect(parsed.uploaderEmail, isNull);
      // Which means no row can be edited on the strength of a broken payload.
      expect(
        canWriteDocument(
          isAdmin: false,
          myEmail: 'ada@example.com',
          uploaderEmail: parsed.uploaderEmail,
        ),
        isFalse,
      );
    });
  });

  group('validateDocumentTitle', () {
    test('accepts a title', () {
      expect(validateDocumentTitle('Contract'), isNull);
    });

    test('refuses a blank or whitespace-only one', () {
      expect(validateDocumentTitle(''), isNotNull);
      expect(validateDocumentTitle('   '), isNotNull);
    });
  });

  group('status labels', () {
    test('call inactive archived, because nothing is deleted', () {
      expect(documentStatusLabel('active'), 'Active');
      expect(documentStatusLabel('inactive'), 'Archived');
    });

    test('cover every status the backend accepts', () {
      for (final status in documentStatuses) {
        expect(documentStatusLabel(status), isNotEmpty);
      }
    });
  });

  group('reaching the bytes', () {
    test('hasFile is false when the row carries no file', () {
      expect(doc(file: 'documents/contract.pdf').hasFile, isTrue);
      expect(doc(file: '').hasFile, isFalse);
      expect(doc(file: '   ').hasFile, isFalse);
    });

    test('the download URL is the API, never the storage path', () {
      // The whole point: `/media/` has no per-file authorization, so a URL
      // built from `documentFile` would be readable by other tenants and
      // unusable by the person entitled to it.
      final url = ApiConfig.documentDownload('abc');
      expect(url, endsWith('/documents/abc/download/'));
      expect(url, isNot(contains('/media/')));
    });

    test('an attachment downloads by id, not by its stored path', () {
      final url = ApiConfig.attachmentDownload('abc');
      expect(url, endsWith('/attachments/abc/download/'));
      expect(url, isNot(contains('/media/')));
    });
  });
}
