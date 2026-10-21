import 'attachment.dart';
import 'custom_field_definition.dart';

Map<String, dynamic> _map(dynamic v) =>
    v is Map ? Map<String, dynamic>.from(v) : <String, dynamic>{};

List<Map<String, dynamic>> _maps(dynamic v) => v is List
    ? [
        for (final e in v)
          if (e is Map) _map(e),
      ]
    : const [];

String _str(dynamic v, [String fallback = '']) => v?.toString() ?? fallback;

DateTime? _date(dynamic v) => v is String ? DateTime.tryParse(v) : null;

const objectsTurnedOffNotice =
    'Creating and editing is turned off for this organization.';
const objectsLoadFailedNotice =
    'Custom objects could not be loaded. Try again.';

/// Whether a stored custom field value has anything to show.
bool hasFieldValue(dynamic v) =>
    v != null &&
    (v is! String || v.trim().isNotEmpty) &&
    (v is! List || v.isNotEmpty);

/// A stored custom field value as the user reads it. A dropdown shows its
/// option label, or the stored value itself when the option is gone.
String displayValue(ObjectField field, dynamic raw) {
  if (!hasFieldValue(raw)) return 'None';
  if (raw is bool || field.fieldType == 'checkbox') {
    return raw == true ? 'Yes' : 'No';
  }
  if (raw is List) return raw.map((e) => e.toString()).join(', ');
  final text = raw.toString();
  if (field.fieldType == 'dropdown') {
    for (final o in field.options) {
      if (o.value == text) return o.label;
    }
  }
  return text;
}

/// The answer of `GET /api/objects/`. Absent routes (a 404) never reach here.
class CustomObjectsAnswer {
  final bool hasCustomObjects;
  final List<ObjectSummary> objects;
  final List<LinkTarget> linkTargets;

  const CustomObjectsAnswer({
    this.hasCustomObjects = false,
    this.objects = const [],
    this.linkTargets = const [],
  });

  bool get offered => hasCustomObjects || objects.isNotEmpty;

  factory CustomObjectsAnswer.fromJson(Map<String, dynamic> json) =>
      CustomObjectsAnswer(
        hasCustomObjects: json['has_custom_objects'] == true,
        objects: _maps(json['objects']).map(ObjectSummary.fromJson).toList(),
        linkTargets: _maps(
          json['link_targets'],
        ).map(LinkTarget.fromJson).toList(),
      );
}

class ObjectSummary {
  final String key;
  final String label;
  final String labelPlural;
  final String nameLabel;
  final String description;
  final String recordAccess;
  final bool isActive;

  const ObjectSummary({
    required this.key,
    required this.label,
    required this.labelPlural,
    this.nameLabel = 'Name',
    this.description = '',
    this.recordAccess = 'everyone',
    this.isActive = true,
  });

  factory ObjectSummary.fromJson(Map<String, dynamic> json) {
    final label = _str(json['label']);
    return ObjectSummary(
      key: _str(json['key']),
      label: label,
      labelPlural: _str(json['label_plural'], label),
      nameLabel: _str(json['name_label'], 'Name'),
      description: _str(json['description']),
      recordAccess: _str(json['record_access'], 'everyone'),
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}

class LinkTarget {
  final String key;
  final String label;
  final String labelPlural;

  const LinkTarget({
    required this.key,
    required this.label,
    required this.labelPlural,
  });

  factory LinkTarget.fromJson(Map<String, dynamic> json) {
    final label = _str(json['label']);
    return LinkTarget(
      key: _str(json['key']),
      label: label,
      labelPlural: _str(json['label_plural'], label),
    );
  }
}

class ObjectField {
  final String key;
  final String label;
  final String fieldType;
  final List<CustomFieldOption> options;
  final bool isRequired;
  final int displayOrder;
  final bool isActive;
  final String? target;
  final bool? many;

  const ObjectField({
    required this.key,
    required this.label,
    required this.fieldType,
    this.options = const [],
    this.isRequired = false,
    this.displayOrder = 0,
    this.isActive = true,
    this.target,
    this.many,
  });

  bool get isLink => fieldType == 'link';

  factory ObjectField.fromJson(Map<String, dynamic> json) {
    final options = <CustomFieldOption>[];
    for (final o in _maps(json['options'])) {
      final value = _str(o['value']);
      if (value.isEmpty) continue;
      options.add(
        CustomFieldOption(value: value, label: _str(o['label'], value)),
      );
    }
    return ObjectField(
      key: _str(json['key']),
      label: _str(json['label']),
      fieldType: _str(json['field_type'], 'text'),
      options: options,
      isRequired: json['is_required'] as bool? ?? false,
      displayOrder: json['display_order'] as int? ?? 0,
      isActive: json['is_active'] as bool? ?? true,
      target: json['target'] as String?,
      many: json['many'] as bool?,
    );
  }

  /// The id is empty: a field is addressed by its key, never by id.
  CustomFieldDefinition toDefinition(String objectKey) => CustomFieldDefinition(
    id: '',
    targetModel: 'obj:$objectKey',
    key: key,
    label: label,
    fieldType: CustomFieldType.fromString(fieldType),
    options: options,
    isRequired: isRequired,
    displayOrder: displayOrder,
    isActive: isActive,
  );
}

class ObjectDefinition {
  final ObjectSummary summary;
  final List<ObjectField> fields;

  const ObjectDefinition({required this.summary, this.fields = const []});

  List<ObjectField> _ordered(bool Function(ObjectField f) test) {
    final out = fields.where((f) => f.isActive && test(f)).toList();
    out.sort((a, b) => a.displayOrder.compareTo(b.displayOrder));
    return out;
  }

  List<ObjectField> get customFields => _ordered((f) => !f.isLink);
  List<ObjectField> get linkFields => _ordered((f) => f.isLink);

  factory ObjectDefinition.fromJson(Map<String, dynamic> json) =>
      ObjectDefinition(
        summary: ObjectSummary.fromJson(json),
        fields: _maps(json['fields']).map(ObjectField.fromJson).toList(),
      );
}

class PersonRef {
  final String id;
  final String name;
  final String email;

  const PersonRef({required this.id, this.name = '', this.email = ''});

  factory PersonRef.fromJson(Map<String, dynamic> json) => PersonRef(
    id: _str(json['id']),
    name: _str(json['name']),
    email: _str(json['email']),
  );
}

class LinkedRecord {
  final String id;
  final String object;
  final String name;

  const LinkedRecord({required this.id, required this.object, this.name = ''});

  factory LinkedRecord.fromJson(Map<String, dynamic> json) => LinkedRecord(
    id: _str(json['id']),
    object: _str(json['object']),
    name: _str(json['name']),
  );
}

class LinkValue {
  final bool many;
  final List<LinkedRecord> records;
  final int hidden;

  const LinkValue({this.many = true, this.records = const [], this.hidden = 0});

  /// A one-record field holding a link the caller cannot open is never sent.
  bool get readOnly => !many && hidden > 0;

  factory LinkValue.fromJson(Map<String, dynamic> json) => LinkValue(
    many: json['many'] as bool? ?? true,
    records: _maps(json['records']).map(LinkedRecord.fromJson).toList(),
    hidden: json['hidden'] as int? ?? 0,
  );
}

class RecordAttachment {
  static const photoExtensions = {'jpg', 'jpeg', 'png', 'webp', 'gif'};

  final String id;
  final String fileName;
  final bool isImage;
  final PersonRef? createdBy;
  final DateTime? createdAt;
  final bool canDelete;

  const RecordAttachment({
    required this.id,
    required this.fileName,
    this.isImage = false,
    this.createdBy,
    this.createdAt,
    this.canDelete = false,
  });

  bool get isPhoto {
    if (!isImage) return false;
    final dot = fileName.lastIndexOf('.');
    if (dot < 0) return false;
    return photoExtensions.contains(fileName.substring(dot + 1).toLowerCase());
  }

  /// A record's file is always fetched by id. The name stands in for
  /// `filePath` only so `hasFile` is true; it is never read as a path.
  Attachment toAttachment() => Attachment(
    id: id,
    fileName: fileName,
    filePath: fileName,
    createdAt: createdAt,
    createdBy: createdBy == null
        ? null
        : (createdBy!.email.isNotEmpty ? createdBy!.email : createdBy!.name),
  );

  factory RecordAttachment.fromJson(Map<String, dynamic> json) {
    final cb = json['created_by'];
    return RecordAttachment(
      id: _str(json['id']),
      fileName: _str(json['file_name'], 'Attachment'),
      isImage: json['is_image'] == true,
      createdBy: cb is Map ? PersonRef.fromJson(_map(cb)) : null,
      createdAt: _date(json['created_at']),
      canDelete: json['can_delete'] == true,
    );
  }
}

class ObjectRecord {
  final String id;
  final String name;
  final Map<String, dynamic> customFields;
  final List<PersonRef> assignedTo;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final Map<String, LinkValue> links;
  final PersonRef? createdBy;
  final bool canEdit;
  final bool canDelete;
  final List<RecordAttachment> attachments;

  const ObjectRecord({
    required this.id,
    required this.name,
    this.customFields = const {},
    this.assignedTo = const [],
    this.createdAt,
    this.updatedAt,
    this.links = const {},
    this.createdBy,
    this.canEdit = false,
    this.canDelete = false,
    this.attachments = const [],
  });

  factory ObjectRecord.fromJson(Map<String, dynamic> json) {
    final cb = json['created_by'];
    return ObjectRecord(
      id: _str(json['id']),
      name: _str(json['name']),
      customFields: _map(json['custom_fields']),
      assignedTo: _maps(json['assigned_to']).map(PersonRef.fromJson).toList(),
      createdAt: _date(json['created_at']),
      updatedAt: _date(json['updated_at']),
      links: {
        for (final e in _map(json['links']).entries)
          e.key: LinkValue.fromJson(_map(e.value)),
      },
      createdBy: cb is Map ? PersonRef.fromJson(_map(cb)) : null,
      canEdit: json['can_edit'] == true,
      canDelete: json['can_delete'] == true,
      attachments: _maps(
        json['attachments'],
      ).map(RecordAttachment.fromJson).toList(),
    );
  }
}

class RelatedRecordRef {
  final String id;
  final String name;

  const RelatedRecordRef({required this.id, this.name = ''});

  factory RelatedRecordRef.fromJson(Map<String, dynamic> json) =>
      RelatedRecordRef(id: _str(json['id']), name: _str(json['name']));
}

class RelatedGroup {
  final String objectKey;
  final String objectLabel;
  final String fieldKey;
  final String fieldLabel;
  final List<RelatedRecordRef> records;

  const RelatedGroup({
    required this.objectKey,
    required this.objectLabel,
    required this.fieldKey,
    required this.fieldLabel,
    this.records = const [],
  });

  factory RelatedGroup.fromJson(Map<String, dynamic> json) {
    final object = _map(json['object']);
    final field = _map(json['field']);
    return RelatedGroup(
      objectKey: _str(object['key']),
      objectLabel: _str(object['label']),
      fieldKey: _str(field['key']),
      fieldLabel: _str(field['label']),
      records: _maps(json['records']).map(RelatedRecordRef.fromJson).toList(),
    );
  }
}

class RelatedLinkField {
  final String objectKey;
  final String objectLabel;
  final String fieldKey;
  final String fieldLabel;

  const RelatedLinkField({
    required this.objectKey,
    required this.objectLabel,
    required this.fieldKey,
    required this.fieldLabel,
  });

  factory RelatedLinkField.fromJson(Map<String, dynamic> json) {
    final object = _map(json['object']);
    final field = _map(json['field']);
    return RelatedLinkField(
      objectKey: _str(object['key']),
      objectLabel: _str(object['label']),
      fieldKey: _str(field['key']),
      fieldLabel: _str(field['label']),
    );
  }
}

class RelatedAnswer {
  final List<RelatedGroup> groups;
  final bool canEdit;
  final List<RelatedLinkField> linkFields;

  const RelatedAnswer({
    this.groups = const [],
    this.canEdit = false,
    this.linkFields = const [],
  });

  /// A record can be taken out of a group only where the caller may edit and
  /// the field is one of the many-record fields the server listed.
  bool removable(RelatedGroup g) =>
      canEdit &&
      linkFields.any(
        (f) => f.objectKey == g.objectKey && f.fieldKey == g.fieldKey,
      );

  bool get showsNothing => groups.isEmpty && linkFields.isEmpty;

  factory RelatedAnswer.fromJson(Map<String, dynamic> json) => RelatedAnswer(
    groups: _maps(json['groups']).map(RelatedGroup.fromJson).toList(),
    canEdit: json['can_edit'] == true,
    linkFields: _maps(
      json['link_fields'],
    ).map(RelatedLinkField.fromJson).toList(),
  );
}

/// Latin letters that decompose to a base letter plus a combining mark, which
/// the web's `normalize('NFKD')` strips.
const _accentGroups = {
  'a': 'àáâãäåāăą',
  'c': 'çćĉċč',
  'd': 'ďđ',
  'e': 'èéêëēĕėęě',
  'g': 'ĝğġģ',
  'i': 'ìíîïĩīĭįı',
  'l': 'ĺļľł',
  'n': 'ñńņň',
  'o': 'òóôõöøōŏő',
  'r': 'ŕŗř',
  's': 'śŝşš',
  't': 'ţť',
  'u': 'ùúûüũūŭůűų',
  'y': 'ýÿ',
  'z': 'źżž',
};

final _accentMap = {
  for (final e in _accentGroups.entries)
    for (final r in e.value.runes) String.fromCharCode(r): e.key,
};

/// The web's `suggestKey`: accents stripped, runs of anything but a-z0-9
/// become one underscore, the leading non-letters and trailing underscore go.
String suggestObjectKey(String label, int max) {
  final buf = StringBuffer();
  for (final r in label.toLowerCase().runes) {
    final ch = String.fromCharCode(r);
    buf.write(_accentMap[ch] ?? ch);
  }
  var s = buf
      .toString()
      .replaceAll(RegExp(r'[^a-z0-9]+'), '_')
      .replaceFirst(RegExp(r'^[^a-z]+'), '');
  if (s.length > max) s = s.substring(0, max);
  return s.replaceFirst(RegExp(r'_+$'), '');
}
