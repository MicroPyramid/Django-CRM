/// A call, meeting, email, WhatsApp, SMS or enquiry logged on a record, from
/// `/api/interactions/`.
enum InteractionKind {
  call('call', 'Call', 'call'),
  meeting('meeting', 'Meeting', 'meeting'),
  email('email', 'Email', 'email'),
  whatsapp('whatsapp', 'WhatsApp', 'WhatsApp message'),
  sms('sms', 'Text', 'text message'),
  enquiry('enquiry', 'Enquiry', 'enquiry');

  const InteractionKind(this.value, this.label, this.noun);

  final String value;
  final String label;

  /// How a sentence names one: "Log this WhatsApp message to Maria?".
  final String noun;

  /// Every kind a person may log. An enquiry is written by the server only.
  static const loggable = [call, meeting, email, whatsapp, sms];

  static InteractionKind? parse(String? value) {
    for (final kind in values) {
      if (kind.value == value) return kind;
    }
    return null;
  }
}

enum CallOutcome {
  connected('connected', 'Connected'),
  noAnswer('no_answer', 'No answer'),
  voicemail('voicemail', 'Voicemail'),
  busy('busy', 'Busy'),
  wrongNumber('wrong_number', 'Wrong number');

  const CallOutcome(this.value, this.label);

  final String value;
  final String label;

  static CallOutcome? parse(String? value) {
    for (final outcome in values) {
      if (outcome.value == value) return outcome;
    }
    return null;
  }
}

/// The record kinds an interaction can belong to, named as the API's filter
/// and create parameters name them.
enum InteractionHome {
  lead('lead'),
  contact('contact'),
  account('account'),
  opportunity('opportunity'),
  ticket('case');

  const InteractionHome(this.param);

  final String param;
}

/// One record whose interactions are listed, or that a new one is logged on.
typedef InteractionTarget = ({InteractionHome home, String id});

class Interaction {
  const Interaction({
    required this.id,
    required this.kindValue,
    required this.inbound,
    required this.occurredAt,
    this.durationSeconds,
    this.durationEstimated = false,
    this.outcome = '',
    this.subject = '',
    this.body = '',
    this.loggedById,
    this.loggedByName,
    this.origin = '',
    this.canEdit = false,
  });

  final String id;

  /// As the server sent it, so a kind added later still shows.
  final String kindValue;
  final bool inbound;
  final DateTime occurredAt;
  final int? durationSeconds;
  final bool durationEstimated;
  final String outcome;
  final String subject;
  final String body;
  final String? loggedById;
  final String? loggedByName;
  final String origin;
  final bool canEdit;

  InteractionKind? get kind => InteractionKind.parse(kindValue);

  /// "Outgoing call", "Email received", "Enquiry via web form": the web's
  /// wording for a timeline row.
  String get title => switch (kind) {
    InteractionKind.call => inbound ? 'Incoming call' : 'Outgoing call',
    InteractionKind.meeting => 'Meeting',
    InteractionKind.email => inbound ? 'Email received' : 'Email sent',
    InteractionKind.whatsapp => inbound ? 'WhatsApp received' : 'WhatsApp sent',
    InteractionKind.sms => inbound ? 'Text received' : 'Text sent',
    InteractionKind.enquiry => switch (origin) {
      '' || 'manual' => 'Enquiry',
      'webform' => 'Enquiry via web form',
      'intake' => 'Enquiry via lead webhook',
      'email' => 'Enquiry via email',
      _ => 'Enquiry via $origin',
    },
    null => 'Activity',
  };

  /// "about 4 min" when the phone estimated it, else "4 min"; null if unknown.
  String? get durationText {
    final seconds = durationSeconds;
    if (seconds == null) return null;
    final text = shortElapsed(Duration(seconds: seconds));
    return durationEstimated ? 'about $text' : text;
  }

  factory Interaction.fromJson(Map<String, dynamic> json) {
    final logger = json['logged_by_details'];
    String? loggerName;
    if (logger is Map) {
      final name = logger['name']?.toString().trim() ?? '';
      final email = logger['email']?.toString().trim() ?? '';
      loggerName = name.isNotEmpty
          ? name
          : (email.isNotEmpty ? email.split('@').first : null);
    }
    final duration = json['duration_seconds'];
    return Interaction(
      id: json['id']?.toString() ?? '',
      kindValue: json['kind']?.toString() ?? '',
      inbound: json['direction'] == 'inbound',
      occurredAt:
          DateTime.tryParse(json['occurred_at']?.toString() ?? '') ??
          DateTime.tryParse(json['created_at']?.toString() ?? '') ??
          DateTime.fromMillisecondsSinceEpoch(0),
      durationSeconds: duration is num ? duration.toInt() : null,
      durationEstimated: json['duration_estimated'] == true,
      outcome: json['outcome']?.toString() ?? '',
      subject: json['subject']?.toString() ?? '',
      body: json['body']?.toString() ?? '',
      loggedById: json['logged_by']?.toString(),
      loggedByName: loggerName,
      origin: json['origin']?.toString() ?? '',
      canEdit: json['can_edit'] == true,
    );
  }
}

/// One record's interactions, newest first. [offered] is false when the API
/// answered 404, which an API older than interactions does.
class RecordInteractions {
  const RecordInteractions({required this.items, required this.count})
    : offered = true;

  const RecordInteractions.notOffered()
    : items = const [],
      count = 0,
      offered = false;

  final List<Interaction> items;

  /// Every interaction the record has, which can be more than [items] holds.
  final int count;
  final bool offered;
}

/// What a person logs. Outbound always: the phone logs what its user did.
class InteractionDraft {
  const InteractionDraft({
    required this.target,
    required this.kind,
    required this.occurredAt,
    required this.origin,
    this.durationSeconds,
    this.durationEstimated = false,
    this.outcome,
    this.body = '',
  });

  final InteractionTarget target;
  final InteractionKind kind;
  final DateTime occurredAt;

  /// `phone_tap` after a tap on Call, WhatsApp, SMS or Email, else `manual`.
  final String origin;
  final int? durationSeconds;
  final bool durationEstimated;
  final CallOutcome? outcome;
  final String body;

  Map<String, dynamic> toJson() => {
    'kind': kind.value,
    'direction': 'outbound',
    'occurred_at': occurredAt.toUtc().toIso8601String(),
    if (durationSeconds != null) ...{
      'duration_seconds': durationSeconds,
      'duration_estimated': durationEstimated,
    },
    if (kind == InteractionKind.call && outcome != null)
      'outcome': outcome!.value,
    if (body.trim().isNotEmpty) 'body': body.trim(),
    'origin': origin,
    target.home.param: target.id,
  };
}

/// "under a minute", "14 min", "2 h 14 min", "3 d 4 h": a call's length or a
/// lead's wait, as the web writes it.
String shortElapsed(Duration d) {
  if (d.inMinutes < 1) return 'under a minute';
  if (d.inMinutes < 60) return '${d.inMinutes} min';
  if (d.inHours < 24) {
    final minutes = d.inMinutes % 60;
    return minutes == 0 ? '${d.inHours} h' : '${d.inHours} h $minutes min';
  }
  final hours = d.inHours % 24;
  return hours == 0 ? '${d.inDays} d' : '${d.inDays} d $hours h';
}
