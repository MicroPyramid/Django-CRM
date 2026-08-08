/// Contacts on a ticket, and the field whose absence used to erase them.
///
/// `CaseDetailView.put` is a full replace: it clears `contacts` and `teams`
/// unconditionally and re-adds only what the body carries. This app edited
/// with PUT and sent neither, so every edit made from the phone unlinked every
/// contact and every team on the ticket, whatever the edit was about. The fix
/// is two-part and both parts are pinned here: the payload carries `contacts`,
/// and the request goes as PATCH, which only touches an M2M when its key is
/// present.
library;

import 'package:bottle_crm/data/models/ticket.dart';
import 'package:bottle_crm/providers/tickets_provider.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _json({List<Map<String, dynamic>>? contacts}) => {
  'id': 't1',
  'name': 'Printer is on fire',
  'status': 'New',
  'priority': 'Normal',
  'case_type': 'Question',
  'account': {'id': 'a1', 'name': 'Acme'},
  'assigned_to': const [],
  'tags': const [],
  'contacts': ?contacts,
};

void main() {
  group('parsing contacts off a ticket', () {
    test('reads ids and names', () {
      final ticket = Ticket.fromJson(
        _json(
          contacts: [
            {'id': 'c1', 'first_name': 'Dana', 'last_name': 'Reed'},
            {'id': 'c2', 'first_name': 'Amal', 'last_name': 'Khan'},
          ],
        ),
      );
      expect(ticket.contactIds, ['c1', 'c2']);
      expect(ticket.contactNames, ['Dana Reed', 'Amal Khan']);
    });

    test('falls back to the email when there is no name', () {
      final ticket = Ticket.fromJson(
        _json(
          contacts: [
            {
              'id': 'c1',
              'first_name': '',
              'last_name': '',
              'email': 'x@y.test',
            },
          ],
        ),
      );
      expect(ticket.contactNames, ['x@y.test']);
    });

    test('an absent key is an empty list, not a crash', () {
      final ticket = Ticket.fromJson(_json());
      expect(ticket.contactIds, isEmpty);
      expect(ticket.contactNames, isEmpty);
    });
  });

  group('the payload', () {
    test('always carries contacts, so a full replace cannot drop them', () {
      final ticket = Ticket.fromJson(
        _json(
          contacts: [
            {'id': 'c1', 'first_name': 'Dana', 'last_name': 'Reed'},
          ],
        ),
      );
      expect(ticket.toJson().containsKey('contacts'), isTrue);
      expect(ticket.toJson()['contacts'], ['c1']);
    });

    test('sends an empty list rather than omitting the key', () {
      // Omitting is how a PUT client erases them by accident. Sending an empty
      // list means "nobody", which is a thing somebody can mean.
      final ticket = Ticket.fromJson(_json());
      expect(ticket.toJson()['contacts'], isEmpty);
    });
  });

  group('open statuses', () {
    test('are the three where somebody still owes an answer', () {
      // Mirrors `cases.views.OPEN_STATUSES` and the web's own list. A ticket
      // rail that says "also open" has to mean the same thing on both clients.
      expect(openTicketStatuses.map((s) => s.value).toList(), [
        'New',
        'Assigned',
        'Pending',
      ]);
    });

    test('exclude every terminal one', () {
      for (final terminal in [
        TicketStatus.closed,
        TicketStatus.rejected,
        TicketStatus.duplicate,
      ]) {
        expect(openTicketStatuses, isNot(contains(terminal)));
      }
    });
  });

  group('the also-open rail', () {
    Ticket t(String id) => Ticket.fromJson({..._json(), 'id': id});

    test('drops the ticket being read', () {
      final rows = pickAlsoOpen([t('a'), t('b'), t('c')], excludeTicketId: 'b');
      expect(rows.map((x) => x.id), ['a', 'c']);
    });

    test('keeps five, because a rail is context and not a list', () {
      final rows = pickAlsoOpen([
        for (var i = 0; i < 9; i++) t('t$i'),
      ], excludeTicketId: 'none');
      expect(rows.length, 5);
    });

    test(
      'asks for the three open statuses, repeated the way the API reads',
      () {
        final url = alsoOpenQueryUrl('acct-1');
        expect(url, contains('account=acct-1'));
        expect('status=New'.allMatches(url).length, 1);
        expect('status=Assigned'.allMatches(url).length, 1);
        expect('status=Pending'.allMatches(url).length, 1);
        expect(url, isNot(contains('status=Closed')));
      },
    );

    test('asks for six so that dropping this one still leaves five', () {
      expect(alsoOpenQueryUrl('acct-1'), contains('limit=6'));
    });

    test('escapes an account id rather than pasting it into the query', () {
      // `encodeQueryComponent` writes a space as `+`, which is correct for a
      // query string. The `&` is what matters: unescaped it would end the
      // parameter and inject one of its own.
      expect(alsoOpenQueryUrl('a b&c'), contains('account=a+b%26c'));
    });
  });
}
