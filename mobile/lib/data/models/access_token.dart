/// Personal access tokens, as the org-wide oversight screen reads them.
///
/// **A token value is shown once, in the response to the request that created
/// it, and never again.** The server keeps a SHA-256 hash plus a 13-character
/// prefix, so there is nothing to re-display even if someone asks. Nothing in
/// this file stores, caches or formats a raw value; the create call hands it
/// straight to the screen that shows it and it is gone with that screen.
///
/// `frontend/src/routes/(app)/settings/api-tokens/oversight.js` carries the
/// same rules.
library;

/// Who a token authenticates as. A token inherits its owner's role and org,
/// which is why the row has to name them.
class TokenOwner {
  const TokenOwner({
    required this.id,
    required this.name,
    required this.role,
    required this.isActive,
  });

  final String id;
  final String name;
  final String role;

  /// `resolve_valid_pat` refuses a token whose owner's profile is inactive, so
  /// a token here is dormant rather than live. It would authenticate again if
  /// the account were reactivated, which is why it is worth revoking anyway.
  final bool isActive;

  bool get isAdmin => role == 'ADMIN';

  String get roleLabel => isAdmin ? 'Admin' : 'Member';

  factory TokenOwner.fromJson(Map<String, dynamic> json) => TokenOwner(
    id: json['id']?.toString() ?? '',
    name: json['name']?.toString() ?? 'Unknown',
    role: json['role']?.toString() ?? 'USER',
    isActive: json['is_active'] as bool? ?? true,
  );

  /// The first word of the display name, for "Everything Ada can".
  String get firstName {
    final parts = name.trim().split(RegExp(r'\s+'));
    return parts.isEmpty ? '' : parts.first;
  }
}

class AccessToken {
  const AccessToken({
    required this.id,
    required this.name,
    required this.tokenPrefix,
    required this.owner,
    this.scopes = const [],
    this.expiresAt,
    this.lastUsedAt,
    this.createdAt,
    this.revokedAt,
    this.isLive = true,
  });

  final String id;
  final String name;

  /// The first 13 characters, which is all the server keeps in the clear. The
  /// row shows this and stops.
  final String tokenPrefix;

  final TokenOwner owner;

  /// `<resource>:<action>` strings. **An empty list means unrestricted**, which
  /// is what every token issued before `common/scopes.py` carries, so it must
  /// never be drawn as "no access".
  final List<String> scopes;

  final DateTime? expiresAt;
  final DateTime? lastUsedAt;
  final DateTime? createdAt;
  final DateTime? revokedAt;

  /// Server-computed: not revoked and not past its expiry.
  final bool isLive;

  factory AccessToken.fromJson(Map<String, dynamic> json) => AccessToken(
    id: json['id']?.toString() ?? '',
    name: json['name']?.toString() ?? '',
    tokenPrefix: json['token_prefix']?.toString() ?? '',
    owner: TokenOwner.fromJson(
      (json['owner'] as Map?)?.cast<String, dynamic>() ?? const {},
    ),
    scopes:
        (json['scopes'] as List?)?.map((s) => s.toString()).toList() ??
        const [],
    expiresAt: _date(json['expires_at']),
    lastUsedAt: _date(json['last_used_at']),
    createdAt: _date(json['created_at']),
    revokedAt: _date(json['revoked_at']),
    // `is_live` is a derived flag the ORG oversight endpoint computes; the
    // self-scoped list does not send it. Defaulting to true drew every revoked
    // and expired token on that list as Live, so absent means "work it out"
    // from the two stored facts rather than "assume the best".
    isLive:
        json['is_live'] as bool? ??
        _derivedIsLive(_date(json['revoked_at']), _date(json['expires_at'])),
  );

  static bool _derivedIsLive(DateTime? revokedAt, DateTime? expiresAt) {
    if (revokedAt != null) return false;
    if (expiresAt == null) return true;
    return expiresAt.isAfter(DateTime.now());
  }

  /// Revoked and expired are different reasons for the same outcome, so they
  /// read differently and tone the same. Neither is a live credential.
  String get statusLabel {
    if (revokedAt != null) return 'Revoked';
    if (!isLive) return 'Expired';
    return 'Live';
  }

  /// When this token last did anything, falling back to when it was issued.
  ///
  /// **`lastUsedAt` being null does not mean "long ago".** It is null both for
  /// a token issued three years ago and for one issued a minute ago, and the
  /// "Unused 90+ days" figure used to count on null alone, so creating a token
  /// put the token you had just made into that count on the very next read.
  /// `OrgAccessTokenListView` now measures the same fallback for its total, and
  /// this is the row-level half: the card and the row have to be counting the
  /// same rows.
  DateTime? get lastActivityAt => lastUsedAt ?? createdAt;

  /// The warning line under a row, or null when there is nothing to say.
  ///
  /// Only for a live token. A revoked or expired one is already not a
  /// credential, and calling it neglected as well would bury the rows worth
  /// acting on.
  String? stalenessNote(DateTime now) {
    if (!isLive) return null;
    final since = lastActivityAt;
    if (since == null) return null;
    final days = now.difference(since).inDays;
    if (days <= 90) return null;
    return lastUsedAt != null
        ? 'unused for $days days'
        : 'never used, issued $days days ago';
  }

  /// What this token may do, in the words the screen uses.
  ///
  /// `ownerLabel` exists because the self-scoped list carries no `owner` block
  /// (the endpoint is already narrowed to you), and "Everything its owner can"
  /// reads oddly on a screen about your own tokens.
  String scopeSummaryFor({String? ownerLabel}) {
    if (scopes.isEmpty) {
      if (ownerLabel != null && ownerLabel.isNotEmpty) {
        return 'Everything $ownerLabel can';
      }
      final first = owner.firstName;
      return first.isEmpty
          ? 'Everything its owner can'
          : 'Everything $first can';
    }
    if (scopes.every((s) => s.endsWith(':read'))) return 'Read only';
    return scopes.join(', ');
  }

  String get scopeSummary => scopeSummaryFor();

  /// True when this row is a live token on a deactivated account: the loose end
  /// the screen offers to clear in one go.
  bool get isOrphaned => isLive && !owner.isActive;
}

/// The server's own totals, computed over the org's whole token set rather than
/// the rows on screen.
class TokenTotals {
  const TokenTotals({
    this.count = 0,
    this.live = 0,
    this.orphaned = 0,
    this.unused90d = 0,
  });

  final int count;
  final int live;
  final int orphaned;

  /// Live tokens whose last activity, or issue date when they have never been
  /// used, is more than 90 days old.
  final int unused90d;

  factory TokenTotals.fromJson(Map<String, dynamic> json) => TokenTotals(
    count: _int(json['count']),
    live: _int(json['live']),
    orphaned: _int(json['orphaned']),
    unused90d: _int(json['unused_90d']),
  );
}

DateTime? _date(dynamic value) {
  if (value == null) return null;
  return DateTime.tryParse(value.toString())?.toLocal();
}

int _int(dynamic value) {
  if (value is int) return value;
  if (value is num) return value.round();
  if (value is String) return int.tryParse(value) ?? 0;
  return 0;
}

/// Live first, then most-recently-active first, which is the order an admin
/// scans in. The dormant and revoked rows sink to the bottom.
List<AccessToken> sortedTokens(List<AccessToken> tokens) {
  final out = [...tokens];
  out.sort((a, b) {
    if (a.isLive != b.isLive) return a.isLive ? -1 : 1;
    final left = b.lastUsedAt?.millisecondsSinceEpoch ?? 0;
    final right = a.lastUsedAt?.millisecondsSinceEpoch ?? 0;
    return left.compareTo(right);
  });
  return out;
}

/// The ids "revoke them all" acts on, derived from the rows the server sent
/// rather than from anything the screen holds.
List<String> orphanedTokenIds(List<AccessToken> tokens) =>
    tokens.where((t) => t.isOrphaned).map((t) => t.id).toList();

/// One coarse expiry choice.
typedef ExpiryChoice = ({String value, String label, int? days});

/// The choices the form offers, in the order it offers them.
///
/// Coarse on purpose: a date picker is more precision than a token expiry
/// needs, and "Never" is a named option rather than an empty field so the
/// riskiest choice is a deliberate one. 90 days is first, so the default is an
/// expiry rather than never.
const List<ExpiryChoice> expiryChoices = [
  (value: '90', label: 'In 90 days', days: 90),
  (value: '30', label: 'In 30 days', days: 30),
  (value: '365', label: 'In 1 year', days: 365),
  (value: 'never', label: 'Never', days: null),
];

/// The two access choices. The backend grammar supports `leads:read`, but a
/// picker listing thirty resources is a worse question than "may it change
/// anything?". A caller wanting finer scopes creates the token through the API.
const List<({String value, String label})> accessChoices = [
  (value: 'read', label: 'Read only'),
  (value: 'full', label: 'Everything the owner can'),
];

/// An ISO instant the API will accept, or null for "never".
///
/// Anything unrecognised is "never" rather than an error, matching the
/// serializer, which treats an absent `expires_at` the same way.
String? expiryFromChoice(String? choice, DateTime now) {
  final match = expiryChoices.where((c) => c.value == choice);
  final days = match.isEmpty ? null : match.first.days;
  if (days == null) return null;
  return now.toUtc().add(Duration(days: days)).toIso8601String();
}

/// `common/scopes.py` treats an empty list as unrestricted, so "full" sends
/// nothing rather than trying to enumerate everything.
List<String> scopesFromChoice(String? choice) =>
    choice == 'read' ? const ['*:read'] : const [];

/// The body for `POST /api/profile/tokens/`.
///
/// **Self-scoped: the server sets the owner from the caller's own profile.**
/// There is no "create on behalf of", by design, so there is no owner field
/// here to get wrong.
Map<String, dynamic> tokenCreatePayload({
  required String name,
  required String expiryChoice,
  required String accessChoice,
  required DateTime now,
}) => {
  'name': name.trim(),
  'scopes': scopesFromChoice(accessChoice),
  'expires_at': expiryFromChoice(expiryChoice, now),
};

/// What a create has to fix before it is worth sending, or null.
///
/// `PersonalAccessTokenCreateSerializer.validate_name` is the authority; this
/// exists so an empty field answers immediately rather than after a round trip.
String? tokenNameProblem(String name) {
  final trimmed = name.trim();
  if (trimmed.isEmpty) return 'Give the token a name.';
  if (trimmed.length > 255) {
    return 'That name is too long (255 characters max).';
  }
  return null;
}

/// What revoking does, said before it is done.
const String tokenRevokeExplanation =
    'The token stops working on the next request that uses it. Anything built '
    'on it, a script or an integration, fails until it is given a new one. '
    'This cannot be undone: a revoked token is never reissued.';

/// The line the screen shows beside a one-time reveal.
const String tokenRevealWarning =
    'This is the only time the full token is shown. Store it somewhere safe. '
    'The server keeps only a hash, so it cannot be retrieved again.';

/// "Last used 12 Aug 2026 · expires 4 Nov 2026", or the honest absences.
///
/// Shared by the admin oversight screen and the self-service one, because a
/// row means the same thing on both and a second copy is a second wording.
String tokenActivityLine(AccessToken token) {
  final used = token.lastUsedAt == null
      ? 'Never used'
      : 'Last used ${tokenHumanDate(token.lastUsedAt!)}';
  final expiry = token.expiresAt == null
      ? 'never expires'
      : 'expires ${tokenHumanDate(token.expiresAt!)}';
  return '$used · $expiry';
}

String tokenHumanDate(DateTime date) {
  const months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];
  return '${date.day} ${months[date.month - 1]} ${date.year}';
}
