/// Shared files, from `/api/documents/`.
///
/// Three access rules, and they are deliberately different widths. Reading is
/// broad (`_visible_to`: the uploader, anyone the document is shared with, any
/// member of a shared team, or an admin) and the server has already applied it,
/// so every row this app receives is one the viewer may open. Editing and
/// deleting are narrow and identical (`_may_write` == `_may_delete`: the
/// uploader or an admin), because a share hands someone a copy to work with,
/// not the original to rewrite. Uploading is open to any member.
///
/// [canWriteDocument] mirrors the narrow rule so a row never offers an action
/// the server would refuse. It is not what keeps anyone out.
library;

/// The two states the backend accepts (`Document.DOCUMENT_STATUS_CHOICE`).
///
/// Nothing here calls `inactive` "deleted". It is an archive: the row stays,
/// the file stays, and the only thing that changes is that the list stops
/// showing it by default.
const List<String> documentStatuses = ['active', 'inactive'];

String documentStatusLabel(String status) =>
    status == 'inactive' ? 'Archived' : 'Active';

/// The icon buckets a filename falls into. Anything outside the three named
/// groups collapses to a generic file, which is what the web does too.
enum DocumentKind { pdf, sheet, text, file }

DocumentKind documentKind(String path) {
  final dot = path.lastIndexOf('.');
  final ext = dot == -1 ? '' : path.substring(dot + 1).toLowerCase();
  if (ext == 'pdf') return DocumentKind.pdf;
  if (const ['xls', 'xlsx', 'csv', 'ods', 'numbers'].contains(ext)) {
    return DocumentKind.sheet;
  }
  if (const [
    'txt',
    'md',
    'markdown',
    'doc',
    'docx',
    'rtf',
    'odt',
  ].contains(ext)) {
    return DocumentKind.text;
  }
  return DocumentKind.file;
}

/// The stored filename, without the upload directory the API prefixes.
String documentFileName(String path) {
  final slash = path.lastIndexOf('/');
  return slash == -1 ? path : path.substring(slash + 1);
}

/// A size for a person. Null means the server could not stat the file (a stale
/// path, an unsynced media directory), which is not an error worth alarming
/// anyone about, so it reads as unknown rather than as zero.
String documentSizeLabel(int? bytes) {
  if (bytes == null) return 'Size unknown';
  if (bytes < 1024) return '$bytes B';
  if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(0)} kB';
  return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
}

/// Who can reach a document besides its uploader and the org's admins.
///
/// A team is named rather than flattened to its members, with the count beside
/// it, because that is what the share actually means: people joining and
/// leaving the team change who it reaches, and a list of today's members would
/// go stale the moment somebody joined.
String documentShareSummary(CrmDocument doc) {
  if (doc.sharedTo.isEmpty && doc.teams.isEmpty) {
    return 'Shared with nobody. Only you and an admin can open it.';
  }
  final parts = <String>[];
  if (doc.sharedTo.isNotEmpty) {
    parts.add(doc.sharedTo.map((p) => p.name).join(', '));
  }
  for (final team in doc.teams) {
    parts.add('${team.name} (${team.memberCount})');
  }
  return parts.join(' · ');
}

/// Whether this viewer may edit or delete [doc].
///
/// Mirrors `DocumentDetailView._may_write`, which is `_may_delete`: an admin,
/// or the person who uploaded it. Compared on email, the one identifier this
/// app and the API agree on for a person, because `created_by` is serialized by
/// `UserSerializer` and the app knows its own user by email.
///
/// False when the uploader is unknown, so an unparsed row hides the action
/// rather than offering one that would 403.
bool canWriteDocument({
  required bool isAdmin,
  required String? myEmail,
  required String? uploaderEmail,
}) {
  if (isAdmin) return true;
  final me = myEmail?.trim().toLowerCase();
  final owner = uploaderEmail?.trim().toLowerCase();
  if (me == null || me.isEmpty || owner == null || owner.isEmpty) return false;
  return me == owner;
}

/// A person a document is shared with.
class DocumentShare {
  const DocumentShare({required this.id, required this.name});

  /// A PROFILE id, which is what `shared_to` takes. Not the user id.
  final String id;
  final String name;

  factory DocumentShare.fromJson(Map<String, dynamic> json) {
    final details = json['user_details'] as Map<String, dynamic>?;
    final name = details?['name']?.toString() ?? '';
    final email = details?['email']?.toString() ?? '';
    return DocumentShare(
      id: json['id']?.toString() ?? '',
      name: name.trim().isNotEmpty
          ? name.trim()
          : (email.isNotEmpty ? email : 'Unnamed'),
    );
  }
}

/// A team a document is shared with.
class DocumentTeamShare {
  const DocumentTeamShare({
    required this.id,
    required this.name,
    this.memberCount = 0,
  });

  final String id;
  final String name;

  /// How many people the share actually reaches. A bare team name does not say.
  final int memberCount;

  factory DocumentTeamShare.fromJson(Map<String, dynamic> json) =>
      DocumentTeamShare(
        id: json['id']?.toString() ?? '',
        name: json['name']?.toString() ?? '',
        memberCount: (json['member_count'] as num?)?.toInt() ?? 0,
      );
}

/// One document, from a `DocumentSerializer` row.
///
/// Named `CrmDocument` rather than `Document` so it cannot be confused with
/// the several `Document` types Flutter and its packages already carry.
class CrmDocument {
  const CrmDocument({
    required this.id,
    required this.title,
    required this.documentFile,
    required this.status,
    this.sharedTo = const [],
    this.teams = const [],
    this.sizeBytes,
    this.createdAt,
    this.uploaderName = 'Unknown',
    this.uploaderEmail,
  });

  final String id;
  final String title;

  /// A stored path, displayed and never turned into a URL here. Building a
  /// media URL client-side is how a private file becomes a public one; the
  /// server decides who gets the bytes. Download through
  /// `ApiConfig.documentDownload(id)`, which is gated by the same read
  /// predicate as the record.
  final String documentFile;

  final String status;
  final List<DocumentShare> sharedTo;
  final List<DocumentTeamShare> teams;
  final int? sizeBytes;
  final DateTime? createdAt;
  final String uploaderName;

  /// From `created_by`, a `UserSerializer` row, so this is the USER's email.
  final String? uploaderEmail;

  bool get isArchived => status == 'inactive';

  /// Whether there is anything to download. A row with no file still lists,
  /// so the action has to be offered conditionally.
  bool get hasFile => documentFile.trim().isNotEmpty;
  DocumentKind get kind => documentKind(documentFile);
  String get fileName => documentFileName(documentFile);

  factory CrmDocument.fromJson(Map<String, dynamic> json) {
    final createdBy = json['created_by'] as Map<String, dynamic>?;
    final name = createdBy?['name']?.toString() ?? '';
    final email = createdBy?['email']?.toString();
    return CrmDocument(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      documentFile: json['document_file']?.toString() ?? '',
      status: json['status']?.toString() ?? 'active',
      sharedTo: (json['shared_to'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(DocumentShare.fromJson)
          .toList(),
      teams: (json['teams'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(DocumentTeamShare.fromJson)
          .toList(),
      sizeBytes: (json['size_bytes'] as num?)?.toInt(),
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
      uploaderName: name.trim().isNotEmpty
          ? name.trim()
          : (email != null && email.isNotEmpty ? email : 'Unknown'),
      uploaderEmail: email,
    );
  }
}

/// The header numbers, computed over every row rather than one page. There is
/// no summary endpoint.
class DocumentTotals {
  const DocumentTotals({
    this.count = 0,
    this.active = 0,
    this.archived = 0,
    this.unshared = 0,
  });

  final int count;
  final int active;
  final int archived;

  /// Given to nobody and no team, so reachable only by whoever uploaded it and
  /// by an admin. Not an error, so the screen states it without alarm.
  final int unshared;
}

DocumentTotals documentTotals(List<CrmDocument> docs) => DocumentTotals(
  count: docs.length,
  active: docs.where((d) => d.status == 'active').length,
  archived: docs.where((d) => d.status == 'inactive').length,
  unshared: docs.where((d) => d.sharedTo.isEmpty && d.teams.isEmpty).length,
);

/// The one rule the write serializer enforces that a person can hit by hand.
///
/// `DocumentCreateSerializer` makes `title` required and refuses a title
/// already used in the org, case-insensitively. The duplicate check needs the
/// server, so only the required part is mirrored: an empty title otherwise
/// comes back as a field error rather than something readable.
String? validateDocumentTitle(String title) =>
    title.trim().isEmpty ? 'Give the document a title.' : null;
