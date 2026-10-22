import '../../config/api_config.dart';
import '../../routes/app_routes.dart';
import '../../routes/record_routes.dart';
import '../../services/run_time.dart';

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
    this.message,
    this.ruleName,
    this.reason,
    this.ruleNames,
    this.windowStart,
  });

  final String id;

  /// Dotted identifier, e.g. `case.mentioned`. Only values in [producedVerbs]
  /// are dispatched by backend code today.
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

  /// From `data`, for the automation verbs; each is null when absent or not
  /// the type the API sends.
  final String? message;
  final String? ruleName;
  final String? reason;
  final List<String>? ruleNames;
  final DateTime? windowStart;

  bool get isUnread => readAt == null;
  String get displayActorName => verb.startsWith('support.')
      ? 'BottleCRM Support'
      : actorName ?? 'The system';

  /// Whether anything in the backend actually produces this verb. A row with
  /// an unknown verb still renders, as a readable sentence, so a new producer
  /// shipping before its copy does not show a raw dotted identifier.
  bool get isKnownVerb => producedVerbs.contains(verb);

  /// The CRM ticket this notification points at, or null.
  ///
  /// The stored `link` is a value from the database, so it is parsed rather
  /// than followed. Only `/cases/<id>` and `/tickets/<id>` resolve here, and
  /// both identify the same CRM ticket. Product-support destinations are
  /// rebuilt separately in [destinationPath]. Anything else, including an
  /// absolute URL or a `javascript:` URL, yields no tappable destination.
  String? get ticketId {
    final value = link;
    if (value == null) return null;
    final match = RegExp(r'^/(?:cases|tickets)/([^/?#]+)/?$').firstMatch(value);
    return match?.group(1);
  }

  /// A safe in-app destination for the notification, or null.
  ///
  /// Product support resolves to `/help/<id>`. The `/support/<id>` spelling is
  /// accepted too, because that is what the producer wrote before the page was
  /// renamed, for the same reason `/cases/` is still accepted above. The
  /// automation verbs' web paths (a record, or the rules) map to their screens
  /// only with a UUID id and a valid object key.
  String? get destinationPath {
    final ticket = ticketId;
    if (ticket != null) return '/tickets/$ticket';
    final value = link;
    if (value == null) return null;
    final help = RegExp(r'^/(?:support|help)/([^/?#]+)/?$').firstMatch(value);
    if (help != null) return '/help/${help.group(1)}';
    // Exactly the paths the engine writes, as the web's `resolvedLink` reads
    // them: no trailing slash, no case folding.
    if (value == '/settings/automation') return AppRoutes.settingsAutomation;
    final rule = RegExp(
      r'^/settings/automation/([^/?#]+)$',
    ).firstMatch(value)?.group(1);
    if (rule != null) {
      return ApiConfig.isUuid(rule)
          ? AppRoutes.settingsAutomationRule(rule)
          : null;
    }
    final custom = RegExp(r'^/objects/([^/?#]+)/([^/?#]+)$').firstMatch(value);
    if (custom != null) {
      return _record('obj:${custom.group(1)}', custom.group(2)!);
    }
    final record = RegExp(
      r'^/(leads|contacts|accounts|pipeline|tasks)/([^/?#]+)$',
    ).firstMatch(value);
    if (record == null) return null;
    return _record(_recordKinds[record.group(1)]!, record.group(2)!);
  }

  /// The feed's actor is `CommentUserSerializer`: `{id, user_details: {email,
  /// profile_pic}}`, with no name. A name is read first in case one is added.
  static String _actorName(Map actor) {
    String? text(Object? v) => v is String && v.isNotEmpty ? v : null;
    final details = actor['user_details'];
    return text(actor['name']) ??
        (details is Map ? text(details['email']) : null) ??
        'Someone';
  }

  static String? _record(String kind, String id) =>
      ApiConfig.isUuid(id) ? linkedRecordRoute(kind, id) : null;

  static const _recordKinds = {
    'leads': 'lead',
    'contacts': 'contact',
    'accounts': 'account',
    'pipeline': 'deal',
    'tasks': 'task',
  };

  /// The automation verbs' sentence, the web's `notificationText`, or null
  /// for any other verb or for `data` of the wrong type. [zone] is the org's
  /// timezone; null reads it from the session.
  String? automationText({String? zone, DateTime? now}) {
    switch (verb) {
      case 'automation.message':
        return ruleName == null ? null : message;
      case 'automation.failed':
        final rule = ruleName, why = reason;
        if (rule == null || why == null) return null;
        return 'The rule "$rule" failed: $why';
      case 'automation.paused':
        final names = ruleNames, why = reason;
        if (names == null || why == null) return null;
        return '$why Paused: ${names.join(', ')}.';
      case 'automation.limit':
        final at = windowStart;
        if (at == null) return null;
        final from = runTimeLabel(at, zone: zone, now: now).replaceFirstMapped(
          RegExp(r'^(Today|Yesterday) '),
          (m) => m[0]!.toLowerCase(),
        );
        return 'Automation reached its limit of 1,000 runs in the hour from '
            '$from. '
            "The rest of that hour's runs were skipped.";
    }
    return null;
  }

  /// The line under a message naming the rule that sent it.
  String? get automationSource =>
      verb == 'automation.message' && automationText() != null
      ? 'From the rule "$ruleName"'
      : null;

  /// "mentioned you on" / "commented on" for the verbs that exist, and a
  /// readable fallback for the ones that do not: `case.sla_breached` reads as
  /// "sla breached" rather than as its identifier.
  String get verbPhrase {
    if (verb == 'case.mentioned') return 'mentioned you on';
    if (verb == 'case.commented') return 'commented on';
    if (verb == 'support.replied') return 'replied to';
    if (verb == 'support.status_changed') return 'updated';
    return verb.replaceFirst(RegExp(r'^[^.]+\.'), '').replaceAll('_', ' ');
  }

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    final actor = json['actor'];
    final data = json['data'];
    String? text(String key) =>
        data is Map && data[key] is String ? data[key] as String : null;
    final rules = data is Map ? data['rules'] : null;
    final windowStart = text('window_start');
    return AppNotification(
      id: json['id']?.toString() ?? '',
      verb: json['verb']?.toString() ?? '',
      actorName: actor is Map ? _actorName(actor) : null,
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
      message: text('message'),
      ruleName: text('rule'),
      reason: text('reason'),
      ruleNames: rules is List && rules.every((r) => r is String)
          ? List<String>.unmodifiable(rules)
          : null,
      windowStart: windowStart == null ? null : DateTime.tryParse(windowStart),
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
    message: message,
    ruleName: ruleName,
    reason: reason,
    ruleNames: ruleNames,
    windowStart: windowStart,
  );
}

/// Verbs the backend dispatches. CRM tickets, platform support and
/// automation rules are the current producers. Anything else is rendered
/// plainly rather than given copy for a feature that does not exist.
const List<String> producedVerbs = [
  'case.mentioned',
  'case.commented',
  'support.replied',
  'support.status_changed',
  'automation.message',
  'automation.failed',
  'automation.paused',
  'automation.limit',
];
