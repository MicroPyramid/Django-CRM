/// Inbound/outbound email associated with a ticket.
///
/// Mirrors `cases.models.EmailMessage` — read-only for now. Direction is one
/// of `in` (customer → us) or `out` (us → customer).
class EmailMessage {
  final String id;
  final String direction;
  final String? fromAddress;
  final List<String> toAddresses;
  final List<String> ccAddresses;
  final String? subject;
  final String? bodyText;
  final DateTime? receivedAt;
  final DateTime? createdAt;

  const EmailMessage({
    required this.id,
    required this.direction,
    this.fromAddress,
    this.toAddresses = const [],
    this.ccAddresses = const [],
    this.subject,
    this.bodyText,
    this.receivedAt,
    this.createdAt,
  });

  bool get isInbound => direction == 'in';

  factory EmailMessage.fromJson(Map<String, dynamic> json) {
    List<String> parseList(dynamic raw) {
      if (raw is List) {
        return raw
            .map((e) => e?.toString() ?? '')
            .where((s) => s.isNotEmpty)
            .toList();
      }
      if (raw is String && raw.isNotEmpty) {
        return raw
            .split(RegExp(r'[;,]'))
            .map((s) => s.trim())
            .where((s) => s.isNotEmpty)
            .toList();
      }
      return const [];
    }

    return EmailMessage(
      id: json['id']?.toString() ?? '',
      direction: json['direction'] as String? ?? 'in',
      fromAddress: json['from_address'] as String?,
      toAddresses: parseList(json['to_addresses']),
      ccAddresses: parseList(json['cc_addresses']),
      subject: json['subject'] as String?,
      bodyText: json['body_text'] as String?,
      receivedAt: json['received_at'] != null
          ? DateTime.tryParse(json['received_at'] as String)
          : null,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }
}
