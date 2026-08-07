/// An in-app notification, as `/api/notifications/` returns it.
///
/// Named `AppNotification` rather than `Notification` because Flutter already
/// has a `Notification` class in widgets, and the collision is silent: the
/// wrong one resolves and the error lands somewhere else entirely.
class AppNotification {
  const AppNotification({
    required this.id,
    required this.verb,
    this.actorName,
    this.entityName,
    this.commentExcerpt,
    this.link,
    this.readAt,
    required this.createdAt,
  });

  final String id;

  /// Dotted identifier, e.g. `case.mentioned`. Only the two in [producedVerbs]
  /// are dispatched by any backend code today.
  final String verb;

  /// Null for a notification the system raised rather than a person.
  final String? actorName;
  final String? entityName;

  /// Somebody else's comment body, truncated server-side. Rendered as text.
  final String? commentExcerpt;

  /// The stored client path. Never navigated to as-is: see [ticketId].
  final String? link;
  final DateTime? readAt;
  final DateTime createdAt;

  bool get isUnread => readAt == null;

  /// Whether anything in the backend actually produces this verb. A row with
  /// an unknown verb still renders, as a readable sentence, so a new producer
  /// shipping before its copy does not show a raw dotted identifier.
  bool get isKnownVerb => producedVerbs.contains(verb);

  /// The ticket this notification points at, or null.
  ///
  /// The stored `link` is a value from the database, so it is parsed rather
  /// than followed. Only `/cases/<id>` and `/tickets/<id>` resolve, and both
  /// resolve to the same ticket id; anything else, including an absolute
  /// `https://` or a `javascript:` URL that ever found its way into the
  /// column, yields null and the row is not tappable. Rows written before the
  /// producer was fixed carry the `/cases/` form, which no client has ever
  /// served, which is why both spellings are accepted here.
  String? get ticketId {
    final value = link;
    if (value == null) return null;
    final match = RegExp(r'^/(?:cases|tickets)/([^/?#]+)/?$').firstMatch(value);
    return match?.group(1);
  }

  /// "mentioned you on" / "commented on" for the verbs that exist, and a
  /// readable fallback for the ones that do not: `case.sla_breached` reads as
  /// "sla breached" rather than as its identifier.
  String get verbPhrase {
    if (verb == 'case.mentioned') return 'mentioned you on';
    if (verb == 'case.commented') return 'commented on';
    return verb.replaceFirst(RegExp(r'^[^.]+\.'), '').replaceAll('_', ' ');
  }

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    final actor = json['actor'];
    final data = json['data'];
    return AppNotification(
      id: json['id']?.toString() ?? '',
      verb: json['verb']?.toString() ?? '',
      actorName: actor is Map<String, dynamic>
          ? (actor['name'] as String?) ?? (actor['email'] as String?)
          : null,
      entityName: json['entity_name'] as String?,
      commentExcerpt: data is Map<String, dynamic>
          ? data['comment_excerpt'] as String?
          : null,
      link: json['link'] as String?,
      readAt: json['read_at'] != null
          ? DateTime.tryParse(json['read_at'].toString())
          : null,
      createdAt:
          DateTime.tryParse(json['created_at']?.toString() ?? '') ??
          DateTime.now(),
    );
  }

  AppNotification copyWith({DateTime? readAt}) => AppNotification(
    id: id,
    verb: verb,
    actorName: actorName,
    entityName: entityName,
    commentExcerpt: commentExcerpt,
    link: link,
    readAt: readAt ?? this.readAt,
    createdAt: createdAt,
  );
}

/// Verbs the backend dispatches. `cases/notifications.py` is the only producer
/// and it writes these two. Anything else is rendered plainly rather than
/// given copy for a feature that does not exist.
const List<String> producedVerbs = ['case.mentioned', 'case.commented'];
