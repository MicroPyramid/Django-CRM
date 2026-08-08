/// Backend-side `Attachments` row attached to a parent record via
/// ContentType. The detail endpoints return these as a top-level
/// `attachments` list separate from the parent object.
class Attachment {
  final String id;
  final String fileName;

  /// The stored path, kept only to tell whether a row has a file behind it.
  ///
  /// **Never turn this into a URL.** It resolves under `/media/`, which is
  /// served with no per-file authorization, so a request for it either fails
  /// (an external browser carries no token) or succeeds for somebody who
  /// should not have it. Download through
  /// `ApiConfig.attachmentDownload(id)` instead, which is gated by the parent
  /// record's own read predicate.
  final String? filePath;
  final DateTime? createdAt;
  final String? createdBy;

  /// Whether there is anything to download. See `filePath`.
  bool get hasFile => (filePath ?? '').trim().isNotEmpty;

  const Attachment({
    required this.id,
    required this.fileName,
    this.filePath,
    this.createdAt,
    this.createdBy,
  });

  factory Attachment.fromJson(Map<String, dynamic> json) {
    String? createdByEmail;
    final cb = json['created_by'];
    if (cb is Map<String, dynamic>) {
      createdByEmail =
          (cb['email'] as String?) ?? (cb['user_details']?['email'] as String?);
    } else if (cb is String) {
      createdByEmail = cb;
    }
    return Attachment(
      id: json['id']?.toString() ?? '',
      fileName: json['file_name'] as String? ?? 'Attachment',
      filePath: json['file_path'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
      createdBy: createdByEmail,
    );
  }
}
