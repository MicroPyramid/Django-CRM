/// Lead webhooks: a URL a form tool or portal posts to, each post a lead.
///
/// The key is never held here. The server answers it in full only to a create
/// or a replace, and this app shows that answer once and keeps nothing; every
/// read carries [LeadIntake.keyHint], its last four characters.
library;

const Map<String, String> intakePresetLabels = {
  'generic': 'Any tool that posts JSON or a form',
  'google_ads': 'Google Ads lead form',
  'tally': 'Tally',
  'gravity_forms': 'Gravity Forms',
};

/// One line of a field mapping: a dot path in the posted body, and the lead
/// field it fills.
class IntakeMapping {
  const IntakeMapping({required this.from, required this.to});

  final String from;
  final String to;

  static List<IntakeMapping> listFrom(dynamic raw) {
    if (raw is! List) return const [];
    return [
      for (final row in raw.whereType<Map>())
        IntakeMapping(
          from: row['from']?.toString() ?? '',
          to: row['to']?.toString() ?? '',
        ),
    ];
  }
}

class LeadIntake {
  const LeadIntake({
    required this.id,
    this.name = '',
    this.preset = 'generic',
    this.url = '',
    this.keyHint = '',
    this.mapping = const [],
    this.defaultSource = '',
    this.sourceDetail = '',
    this.isActive = true,
    this.lastReceivedAt,
    this.lastError = '',
  });

  final String id;
  final String name;
  final String preset;

  /// The full public URL. It never changes, so it is safe to paste anywhere.
  final String url;
  final String keyHint;
  final List<IntakeMapping> mapping;
  final String defaultSource;
  final String sourceDetail;
  final bool isActive;
  final DateTime? lastReceivedAt;
  final String lastError;

  String get presetLabel => intakePresetLabels[preset] ?? 'Any tool';

  /// As the web words it: off, on with nothing yet, or on and receiving.
  String get stateLabel => !isActive
      ? 'Off'
      : lastReceivedAt == null
      ? 'Waiting'
      : 'Receiving';

  factory LeadIntake.fromJson(Map<String, dynamic> json) => LeadIntake(
    id: json['id']?.toString() ?? '',
    name: json['name']?.toString() ?? '',
    preset: json['preset']?.toString() ?? 'generic',
    url: json['url']?.toString() ?? '',
    keyHint: json['key_hint']?.toString() ?? '',
    mapping: IntakeMapping.listFrom(json['mapping']),
    defaultSource: json['default_source']?.toString() ?? '',
    sourceDetail: json['source_detail']?.toString() ?? '',
    isActive: json['is_active'] as bool? ?? true,
    lastReceivedAt: DateTime.tryParse(
      json['last_received_at']?.toString() ?? '',
    )?.toLocal(),
    lastError: json['last_error']?.toString() ?? '',
  );
}

class IntakeDelivery {
  const IntakeDelivery({
    required this.id,
    this.receivedAt,
    this.result = '',
    this.leadId,
    this.externalId = '',
    this.error = '',
  });

  final String id;
  final DateTime? receivedAt;

  /// `created`, `merged`, `duplicate`, `test` or `rejected`.
  final String result;
  final String? leadId;
  final String externalId;
  final String error;

  String get resultLabel => switch (result) {
    'created' => 'Created',
    'merged' => 'Merged',
    'duplicate' => 'Duplicate',
    'test' => 'Test',
    'rejected' => 'Rejected',
    '' => 'Unknown',
    _ => result,
  };

  factory IntakeDelivery.fromJson(Map<String, dynamic> json) {
    final raw = json['lead'];
    final lead = (raw is Map ? raw['id'] : raw)?.toString();
    return IntakeDelivery(
      id: json['id']?.toString() ?? '',
      receivedAt: DateTime.tryParse(
        json['received_at']?.toString() ?? '',
      )?.toLocal(),
      result: json['result']?.toString() ?? '',
      leadId: lead == null || lead.isEmpty ? null : lead,
      externalId: json['external_id']?.toString() ?? '',
      error: json['error']?.toString() ?? '',
    );
  }
}
