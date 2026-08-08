import 'package:bottle_crm/data/models/access_token.dart';
import 'package:flutter_test/flutter_test.dart';

final DateTime now = DateTime.utc(2026, 8, 8, 12);

String ago(int days) => now.subtract(Duration(days: days)).toIso8601String();

/// A token as `/api/org/tokens/` returns one: the safe field set, an owner
/// block, and the derived `is_live`.
Map<String, dynamic> tokenJson({
  String id = 't1',
  String name = 'Nightly export',
  List<String> scopes = const [],
  String? lastUsedAt,
  String? createdAt,
  String? expiresAt,
  String? revokedAt,
  bool isLive = true,
  String ownerName = 'Ada Lovelace',
  String ownerRole = 'ADMIN',
  bool ownerActive = true,
}) => {
  'id': id,
  'name': name,
  'token_prefix': 'bcrm_pat_abc',
  'scopes': scopes,
  'expires_at': expiresAt,
  'last_used_at': lastUsedAt,
  'created_at': createdAt ?? ago(1),
  'revoked_at': revokedAt,
  'is_live': isLive,
  'owner': {
    'id': 'p1',
    'name': ownerName,
    'role': ownerRole,
    'is_active': ownerActive,
  },
};

AccessToken build([Map<String, dynamic>? json]) =>
    AccessToken.fromJson(json ?? tokenJson());

void main() {
  group('AccessToken.fromJson', () {
    test('reads the safe field set and the owner block', () {
      final token = build(
        tokenJson(scopes: const ['*:read'], ownerRole: 'USER'),
      );
      expect(token.name, 'Nightly export');
      expect(token.tokenPrefix, 'bcrm_pat_abc');
      expect(token.scopes, ['*:read']);
      expect(token.owner.name, 'Ada Lovelace');
      expect(token.owner.roleLabel, 'Member');
    });

    test('a row missing its owner block parses rather than throwing', () {
      final json = tokenJson()..remove('owner');
      expect(AccessToken.fromJson(json).owner.name, 'Unknown');
    });

    test('never carries a raw value, because none is ever sent', () {
      // The list serializer has no `token` field: the server keeps a hash.
      // Nothing on this model could hold one even if a body carried it.
      final json = tokenJson()..['token'] = 'bcrm_pat_leaked';
      final token = AccessToken.fromJson(json);
      expect(token.tokenPrefix, 'bcrm_pat_abc');
      expect(token.scopeSummary, isNot(contains('leaked')));
    });
  });

  group('statusLabel', () {
    test('names revoked and expired apart', () {
      expect(
        build(tokenJson(revokedAt: ago(1), isLive: false)).statusLabel,
        'Revoked',
      );
      expect(build(tokenJson(isLive: false)).statusLabel, 'Expired');
    });

    test('is Live otherwise', () {
      expect(build().statusLabel, 'Live');
    });
  });

  group('stalenessNote', () {
    test('says nothing about a token issued today and not yet used', () {
      // The finding: a null last_used_at is not "long ago". A token created a
      // minute ago has to read as new on the row AND in the count.
      expect(build().stalenessNote(now), isNull);
    });

    test('flags a never-used token once it is old enough, and dates it', () {
      final token = build(tokenJson(createdAt: ago(120)));
      expect(token.stalenessNote(now), 'never used, issued 120 days ago');
    });

    test('flags a token last used more than 90 days ago', () {
      final token = build(tokenJson(lastUsedAt: ago(120)));
      expect(token.stalenessNote(now), 'unused for 120 days');
    });

    test('says nothing at exactly 90 days, matching the backend > 90', () {
      expect(build(tokenJson(lastUsedAt: ago(90))).stalenessNote(now), isNull);
      expect(
        build(tokenJson(lastUsedAt: ago(91))).stalenessNote(now),
        'unused for 91 days',
      );
    });

    test('says nothing about a token that is no longer live', () {
      final token = build(tokenJson(isLive: false, createdAt: ago(400)));
      expect(token.stalenessNote(now), isNull);
    });
  });

  group('scopeSummary', () {
    test('an empty list is unrestricted, said in the owner name', () {
      // Empty means unrestricted server-side, which is what every token issued
      // before enforcement carries. Drawing those as limited would be a lie.
      expect(build().scopeSummary, 'Everything Ada can');
    });

    test('falls back to a name-free phrasing without an owner', () {
      final json = tokenJson()..remove('owner');
      expect(AccessToken.fromJson(json).scopeSummary, 'Everything Unknown can');
    });

    test('an all-read list is read only', () {
      expect(
        build(tokenJson(scopes: const ['*:read'])).scopeSummary,
        'Read only',
      );
      expect(
        build(
          tokenJson(scopes: const ['leads:read', 'cases:read']),
        ).scopeSummary,
        'Read only',
      );
    });

    test('anything narrower is listed verbatim', () {
      expect(
        build(
          tokenJson(scopes: const ['leads:read', 'cases:write']),
        ).scopeSummary,
        'leads:read, cases:write',
      );
    });
  });

  group('isOrphaned', () {
    test('is a live token on a deactivated account', () {
      expect(build(tokenJson(ownerActive: false)).isOrphaned, isTrue);
    });

    test('is not a revoked token on a deactivated account', () {
      expect(
        build(tokenJson(ownerActive: false, isLive: false)).isOrphaned,
        isFalse,
      );
    });

    test('is not a live token on an active account', () {
      expect(build().isOrphaned, isFalse);
    });
  });

  group('sortedTokens', () {
    test('live rows come before dormant ones', () {
      final tokens = [
        build(tokenJson(id: 'dead', isLive: false, lastUsedAt: ago(1))),
        build(tokenJson(id: 'alive', lastUsedAt: ago(30))),
      ];
      expect(sortedTokens(tokens).first.id, 'alive');
    });

    test('most recently used first inside the live rows', () {
      final tokens = [
        build(tokenJson(id: 'old', lastUsedAt: ago(30))),
        build(tokenJson(id: 'recent', lastUsedAt: ago(1))),
      ];
      expect(sortedTokens(tokens).map((t) => t.id).toList(), ['recent', 'old']);
    });

    test('does not mutate the list it was given', () {
      final tokens = [
        build(tokenJson(id: 'dead', isLive: false)),
        build(tokenJson(id: 'alive')),
      ];
      sortedTokens(tokens);
      expect(tokens.first.id, 'dead');
    });
  });

  group('orphanedTokenIds', () {
    test('is only the live rows on deactivated accounts', () {
      final tokens = [
        build(tokenJson(id: 'a', ownerActive: false)),
        build(tokenJson(id: 'b', ownerActive: false, isLive: false)),
        build(tokenJson(id: 'c')),
      ];
      expect(orphanedTokenIds(tokens), ['a']);
    });
  });

  group('TokenTotals', () {
    test('reads the four figures', () {
      final totals = TokenTotals.fromJson(const {
        'count': 5,
        'live': 3,
        'orphaned': 1,
        'unused_90d': 2,
      });
      expect(totals.count, 5);
      expect(totals.live, 3);
      expect(totals.orphaned, 1);
      expect(totals.unused90d, 2);
    });

    test('a missing block reads as zeros rather than throwing', () {
      final totals = TokenTotals.fromJson(const {});
      expect(totals.count, 0);
      expect(totals.unused90d, 0);
    });
  });

  group('expiryFromChoice', () {
    test('counts the days the label promises', () {
      final iso = expiryFromChoice('30', now)!;
      expect(DateTime.parse(iso).difference(now).inDays, 30);
    });

    test(
      'every offered choice lands in the future, which the API requires',
      () {
        for (final choice in expiryChoices.where((c) => c.days != null)) {
          final iso = expiryFromChoice(choice.value, now)!;
          expect(
            DateTime.parse(iso).isAfter(now),
            isTrue,
            reason: choice.value,
          );
        }
      },
    );

    test('is null for never, and for anything unrecognised', () {
      expect(expiryFromChoice('never', now), isNull);
      expect(expiryFromChoice('tuesday', now), isNull);
      expect(expiryFromChoice(null, now), isNull);
    });

    test('offers 90 days first, so the default is an expiry not never', () {
      expect(expiryChoices.first.value, '90');
    });
  });

  group('scopesFromChoice', () {
    test('read means a read-only wildcard', () {
      expect(scopesFromChoice('read'), ['*:read']);
    });

    test('anything else means unrestricted, the empty list', () {
      expect(scopesFromChoice('full'), isEmpty);
      expect(scopesFromChoice(null), isEmpty);
    });
  });

  group('tokenCreatePayload', () {
    test('sends name, scopes and expiry, and nothing else', () {
      final body = tokenCreatePayload(
        name: '  Nightly export  ',
        expiryChoice: '90',
        accessChoice: 'read',
        now: now,
      );
      expect(body.keys.toSet(), {'name', 'scopes', 'expires_at'});
      expect(body['name'], 'Nightly export');
      expect(body['scopes'], ['*:read']);
    });

    test('never carries an owner, because the server sets it', () {
      // A "create on behalf of" field is the one thing this endpoint must not
      // accept, and the surest way not to send it is not to have it.
      final body = tokenCreatePayload(
        name: 'x',
        expiryChoice: 'never',
        accessChoice: 'full',
        now: now,
      );
      expect(body.containsKey('profile'), isFalse);
      expect(body.containsKey('owner'), isFalse);
      expect(body.containsKey('org'), isFalse);
      expect(body['expires_at'], isNull);
    });
  });

  group('tokenNameProblem', () {
    test('accepts an ordinary name', () {
      expect(tokenNameProblem('Nightly export'), isNull);
    });

    test('refuses an empty or blank name, which the serializer refuses', () {
      expect(tokenNameProblem(''), isNotNull);
      expect(tokenNameProblem('   '), isNotNull);
    });

    test('refuses more than 255 characters', () {
      expect(tokenNameProblem('x' * 256), isNotNull);
      expect(tokenNameProblem('x' * 255), isNull);
    });
  });
}
