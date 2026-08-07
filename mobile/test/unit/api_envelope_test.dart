import 'package:bottle_crm/data/api_envelope.dart';
import 'package:flutter_test/flutter_test.dart';

/// The shapes below were copied from live responses, not invented. The
/// accounts one is the reason this helper exists: the picker read `accounts`
/// then `results`, the endpoint publishes neither, and the miss showed up as
/// an empty picker rather than as an error.
void main() {
  group('listFromEnvelope', () {
    test('finds accounts nested two deep', () {
      final body = <String, dynamic>{
        'per_page': 10,
        'page_number': 1,
        'active_accounts': {
          'offset': 0,
          'open_accounts': [
            {'id': 'a1', 'name': 'Kline-Cooke'},
            {'id': 'a2', 'name': 'Bowers, Singleton and Davis'},
          ],
          'open_accounts_count': 2,
        },
        'closed_accounts': {
          'close_accounts': [
            {'id': 'a3', 'name': 'Dormant Ltd'},
          ],
        },
        // The endpoint also publishes a top-level `contacts` list, which is
        // not the account rows and must not be picked up by accident.
        'contacts': [
          {'id': 'c1', 'first_name': 'Eric'},
        ],
      };

      final rows = listFromEnvelope(body, const [
        'active_accounts.open_accounts',
        'accounts',
        'results',
      ]);

      expect(rows.map((r) => r['name']), [
        'Kline-Cooke',
        'Bowers, Singleton and Davis',
      ]);
    });

    test('the old guesses would have found nothing in that body', () {
      final body = <String, dynamic>{
        'active_accounts': {
          'open_accounts': [
            {'id': 'a1', 'name': 'Kline-Cooke'},
          ],
        },
      };

      expect(listFromEnvelope(body, const ['accounts', 'results']), isEmpty);
    });

    test('takes the first path that resolves to a list', () {
      final body = <String, dynamic>{
        'results': [
          {'id': 'c1'},
        ],
        'contacts': [
          {'id': 'wrong'},
        ],
      };

      expect(
        listFromEnvelope(body, const ['results', 'contacts']).single['id'],
        'c1',
      );
    });

    test('skips a path whose value is not a list', () {
      final body = <String, dynamic>{
        'tags': 'not-a-list',
        'results': [
          {'id': 't1'},
        ],
      };

      expect(
        listFromEnvelope(body, const ['tags', 'results']).single['id'],
        't1',
      );
    });

    test('returns empty rather than throwing when nothing matches', () {
      expect(listFromEnvelope(const {}, const ['a.b.c']), isEmpty);
      expect(listFromEnvelope(const {'a': 1}, const ['a.b']), isEmpty);
    });

    test('drops non-map entries instead of failing the whole list', () {
      final body = <String, dynamic>{
        'profiles': [
          {'id': 'p1'},
          'junk',
          null,
          {'id': 'p2'},
        ],
      };

      expect(listFromEnvelope(body, const ['profiles']).map((r) => r['id']), [
        'p1',
        'p2',
      ]);
    });
  });
}
