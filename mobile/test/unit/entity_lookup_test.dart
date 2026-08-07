import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/data/api_envelope.dart';
import 'package:bottle_crm/data/models/lookup_models.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:flutter_test/flutter_test.dart';

/// Every picker in this app was capped at ten rows, and none of them said so.
///
/// The endpoints use DRF's `LimitOffsetPagination` with `PAGE_SIZE = 10`. A
/// lookup that sent no `limit` got ten. Confirmed live against the seeded org:
/// `/api/contacts/` answers `contacts_count: 15` beside ten rows, so five
/// contacts could not be attached to anything from the phone. There was no
/// error, no truncation notice, and no way to tell from the screen.
void main() {
  group('the lookup request', () {
    test('asks for more than one page', () {
      final url = lookupUrl(ApiConfig.contacts);

      expect(url, contains('limit=$lookupPageLimit'));
      expect(lookupPageLimit, greaterThan(10));
    });

    test('keeps the path it was given', () {
      expect(lookupUrl(ApiConfig.tags), startsWith(ApiConfig.tags));
    });
  });

  group('the envelope each new lookup reads', () {
    test('leads are two levels down, under the open group', () {
      // Same shape trap as accounts. `results` is absent, and a missed path
      // reads as "this org has no leads" rather than as a failure.
      final body = <String, dynamic>{
        'open_leads': {
          'open_leads': [
            {'id': 'l1', 'first_name': 'Jill', 'last_name': 'Shaffer'},
          ],
          'leads_count': 20,
        },
        'close_leads': {
          'close_leads': [
            {'id': 'l9', 'first_name': 'Gone', 'last_name': 'Away'},
          ],
        },
      };

      expect(listFromEnvelope(body, const ['results']), isEmpty);
      expect(
        listFromEnvelope(body, const ['open_leads.open_leads']),
        hasLength(1),
      );
    });

    test('deals and tickets sit at the top level under their own key', () {
      expect(
        listFromEnvelope(
          {
            'opportunities': [
              {'id': 'o1', 'name': 'Renewal'},
            ],
          },
          const ['opportunities'],
        ),
        hasLength(1),
      );
      expect(
        listFromEnvelope(
          {
            'cases': [
              {'id': 'c1', 'name': 'Login fails'},
            ],
          },
          const ['cases'],
        ),
        hasLength(1),
      );
    });
  });

  group('a labelled record', () {
    test('a deal is named by its name field, not its title field', () {
      // `title` exists on the row and is null on every deal the API returned.
      // Reading it would label every option "Untitled".
      final deal = EntityLookup.fromJson(
        {'id': 'o1', 'name': 'Stand-alone throughput Deal', 'title': null},
        labelKeys: const ['name'],
      );

      expect(deal.label, 'Stand-alone throughput Deal');
    });

    test('a row with nothing to show still carries its id', () {
      final deal = EntityLookup.fromJson(
        {'id': 'o2'},
        labelKeys: const ['name'],
      );

      // Selectable, and visibly odd. An empty label would render a blank row
      // that looks like a rendering bug and cannot be tapped with confidence.
      expect(deal.id, 'o2');
      expect(deal.label, 'Untitled');
    });
  });

  group('a person', () {
    test('is named first and last', () {
      final lead = EntityLookup.person({
        'id': 'l1',
        'first_name': 'Jill',
        'last_name': 'Shaffer',
        'email': 'jill@example.test',
      });

      expect(lead.label, 'Jill Shaffer');
    });

    test('with only one name part does not carry a stray space', () {
      final lead = EntityLookup.person({
        'id': 'l1',
        'first_name': 'Jill',
        'last_name': '',
      });

      expect(lead.label, 'Jill');
    });

    test('with no name falls back in order, email before company', () {
      final lead = EntityLookup.person(
        {
          'id': 'l1',
          'first_name': '',
          'last_name': '',
          'email': 'agarcia@example.test',
          'company_name': 'Cruz Group',
        },
        fallbackKeys: const ['email', 'company_name'],
      );

      expect(lead.label, 'agarcia@example.test');
    });

    test('with no name and no email falls through to the company', () {
      final lead = EntityLookup.person(
        {'id': 'l1', 'company_name': 'Cruz Group'},
        fallbackKeys: const ['email', 'company_name'],
      );

      expect(lead.label, 'Cruz Group');
    });

    test('with nothing at all is still tappable', () {
      final lead = EntityLookup.person({'id': 'l1'});

      expect(lead.id, 'l1');
      expect(lead.label, 'Unnamed');
    });
  });

  group('identity', () {
    test('two rows with the same id are the same option', () {
      // The picker compares options to mark the current selection. Comparing
      // by label would tie two people who share a name.
      expect(
        const EntityLookup(id: 'x', label: 'One'),
        const EntityLookup(id: 'x', label: 'Another'),
      );
    });
  });
}
