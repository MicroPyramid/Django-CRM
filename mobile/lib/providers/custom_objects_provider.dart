import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/api_envelope.dart';
import '../data/models/custom_field_definition.dart';
import '../data/models/custom_object.dart';
import '../data/models/lookup_models.dart';
import '../services/api_service.dart';
import 'auth_provider.dart';

/// What `GET /api/objects/` says about the org. `null` means the server has no
/// custom objects (a self-hosted install answers 404). Any other failure is an
/// error state, so a timeout never reads as "no custom objects".
class CustomObjectsNotifier extends AsyncNotifier<CustomObjectsAnswer?> {
  @override
  Future<CustomObjectsAnswer?> build() async {
    ref.watch(selectedOrgProvider.select((o) => o?.id));
    final response = await ApiService().get(ApiConfig.objects);
    if (response.statusCode == 404) return null;
    final data = response.data;
    if (!response.success || data == null) {
      throw Exception(response.message ?? 'Could not load custom objects');
    }
    return CustomObjectsAnswer.fromJson(data);
  }
}

// No automatic retry: a failure shows as an error at once, and it is asked
// again only when the user opens More or taps Retry.
final customObjectsProvider =
    AsyncNotifierProvider<CustomObjectsNotifier, CustomObjectsAnswer?>(
      CustomObjectsNotifier.new,
      retry: (_, _) => null,
    );

/// The only way to read the answer for display. Riverpod keeps the previous
/// value through a reload and a failed load, which after an org switch or a
/// sign-out is another org's (or another user's) objects, so both read null.
CustomObjectsAnswer? shownCustomObjects(AsyncValue<CustomObjectsAnswer?> v) =>
    v.hasError || v.isLoading ? null : v.value;

/// The last load failed and nothing is asking again yet.
bool customObjectsFailed(AsyncValue<CustomObjectsAnswer?> v) =>
    v.hasError && !v.isLoading;

/// Asks again after a failure. Called when the user opens More, never from a
/// build, so a failing server is never asked in a loop.
void retryFailedCustomObjects(WidgetRef ref) {
  if (customObjectsFailed(ref.read(customObjectsProvider))) {
    ref.invalidate(customObjectsProvider);
  }
}

final objectDefinitionProvider = FutureProvider.autoDispose
    .family<ObjectDefinition?, String>((ref, key) async {
      if (!ApiConfig.isObjectKey(key)) return null;
      final response = await ApiService().get(ApiConfig.object(key));
      if (response.statusCode == 404) return null;
      final data = response.data;
      if (!response.success || data == null) {
        throw Exception(response.message ?? 'Failed to load this object');
      }
      return ObjectDefinition.fromJson(data);
    }, retry: (_, _) => null);

final objectsSettingsProvider =
    FutureProvider.autoDispose<CustomObjectsAnswer?>((ref) async {
      final response = await ApiService().get(
        ApiConfig.objects,
        queryParams: {'include_archived': 'true'},
      );
      final data = response.data;
      if (!response.success || data == null) return null;
      return CustomObjectsAnswer.fromJson(data);
    });

class ObjectSettingsData {
  final ObjectSummary summary;
  final List<ObjectField> fields;

  const ObjectSettingsData({required this.summary, this.fields = const []});
}

/// The object and every field it has, turned-off ones included for admins.
final objectSettingsProvider = FutureProvider.autoDispose
    .family<ObjectSettingsData, String>((ref, key) async {
      final api = ApiService();
      final results = await Future.wait([
        api.get(ApiConfig.object(key)),
        api.get(ApiConfig.objectFields(key)),
      ]);
      final object = results[0];
      final fields = results[1];
      if (!object.success || object.data == null) {
        throw Exception(object.message ?? 'Failed to load this object');
      }
      if (!fields.success || fields.data == null) {
        throw Exception(fields.message ?? 'Failed to load its fields');
      }
      return ObjectSettingsData(
        summary: ObjectSummary.fromJson(object.data!),
        fields: listFromEnvelope(fields.data!, const [
          'fields',
        ]).map(ObjectField.fromJson).toList(),
      );
    }, retry: (_, _) => null);

const int objectRecordsPageSize = 20;

class ObjectRecordsData {
  final List<ObjectRecord> records;
  final int count;
  final String query;

  const ObjectRecordsData({
    this.records = const [],
    this.count = 0,
    this.query = '',
  });

  bool get hasMore => records.length < count;
}

class ObjectRecordsNotifier extends AsyncNotifier<ObjectRecordsData> {
  ObjectRecordsNotifier(this.key);

  final String key;
  String _query = '';
  // Bumped whenever the list is replaced, so a page fetched for an older list
  // is dropped instead of appended.
  int _generation = 0;
  int? _pagingGeneration;

  @override
  Future<ObjectRecordsData> build() => _fetch(query: '', offset: 0);

  Future<ObjectRecordsData> _fetch({
    required String query,
    required int offset,
  }) async {
    final response = await ApiService().get(
      ApiConfig.objectRecords(key),
      queryParams: {
        'limit': '$objectRecordsPageSize',
        if (offset > 0) 'offset': '$offset',
        if (query.isNotEmpty) 'q': query,
      },
    );
    final data = response.data;
    if (!response.success || data == null) {
      throw Exception(response.message ?? 'Failed to load records');
    }
    final records = listFromEnvelope(data, const [
      'results',
    ]).map(ObjectRecord.fromJson).toList();
    return ObjectRecordsData(
      records: records,
      count: data['count'] as int? ?? records.length,
      query: query,
    );
  }

  Future<void> setQuery(String query) async {
    _query = query.trim();
    final generation = ++_generation;
    state = const AsyncLoading();
    final next = await AsyncValue.guard(() => _fetch(query: _query, offset: 0));
    if (!ref.mounted || generation != _generation) return;
    state = next;
  }

  Future<void> refresh() async {
    final generation = ++_generation;
    final next = await AsyncValue.guard(() => _fetch(query: _query, offset: 0));
    if (!ref.mounted || generation != _generation) return;
    state = next;
  }

  Future<void> loadMore() async {
    final current = state.value;
    if (current == null || !current.hasMore || state.isLoading) return;
    if (_pagingGeneration == _generation) return;
    final generation = _generation;
    _pagingGeneration = generation;
    try {
      final next = await AsyncValue.guard(
        () => _fetch(query: current.query, offset: current.records.length),
      );
      final page = next.value;
      if (!ref.mounted || page == null || generation != _generation) return;
      state = AsyncData(
        ObjectRecordsData(
          records: [...current.records, ...page.records],
          count: page.count,
          query: current.query,
        ),
      );
    } finally {
      if (_pagingGeneration == generation) _pagingGeneration = null;
    }
  }
}

final objectRecordsProvider = AsyncNotifierProvider.autoDispose
    .family<ObjectRecordsNotifier, ObjectRecordsData, String>(
      ObjectRecordsNotifier.new,
      retry: (_, _) => null,
    );

const int linkSearchLimit = 20;

class CustomObjectsApi {
  CustomObjectsApi([ApiService? api]) : _api = api ?? ApiService();

  final ApiService _api;

  Future<ApiResponse<Map<String, dynamic>>> fetchRecord(
    String key,
    String id,
  ) => _api.get(ApiConfig.objectRecord(key, id));

  Future<ApiResponse<Map<String, dynamic>>> createRecord(
    String key,
    Map<String, dynamic> body,
  ) => _api.post(ApiConfig.objectRecords(key), body);

  Future<ApiResponse<Map<String, dynamic>>> updateRecord(
    String key,
    String id,
    Map<String, dynamic> body,
  ) => _api.patch(ApiConfig.objectRecord(key, id), body);

  Future<ApiResponse<Map<String, dynamic>>> deleteRecord(
    String key,
    String id,
  ) => _api.delete(ApiConfig.objectRecord(key, id));

  Future<ApiResponse<Map<String, dynamic>>> deleteAttachment(
    String key,
    String id,
    String attachmentId,
  ) => _api.delete(ApiConfig.objectRecordAttachment(key, id, attachmentId));

  Future<ApiResponse<Map<String, dynamic>>> createObject(
    Map<String, dynamic> body,
  ) => _api.post(ApiConfig.objects, body);

  Future<ApiResponse<Map<String, dynamic>>> updateObject(
    String key,
    Map<String, dynamic> body,
  ) => _api.patch(ApiConfig.object(key), body);

  Future<ApiResponse<Map<String, dynamic>>> deleteObject(String key) =>
      _api.delete(ApiConfig.object(key));

  Future<ApiResponse<Map<String, dynamic>>> createField(
    String key,
    Map<String, dynamic> body,
  ) => _api.post(ApiConfig.objectFields(key), body);

  Future<ApiResponse<Map<String, dynamic>>> updateField(
    String key,
    String fieldKey,
    Map<String, dynamic> body,
  ) => _api.patch(ApiConfig.objectField(key, fieldKey), body);

  Future<ApiResponse<Map<String, dynamic>>> turnOffField(
    String key,
    String fieldKey,
  ) => _api.delete(ApiConfig.objectField(key, fieldKey));

  Future<ApiResponse<Map<String, dynamic>>> addRelated(
    String to,
    String id,
    String record,
    String field,
  ) => _api.post(ApiConfig.objectsRelated, {
    'to': to,
    'id': id,
    'record': record,
    'field': field,
  });

  Future<ApiResponse<Map<String, dynamic>>> removeRelated(
    String to,
    String id,
    String record,
    String field,
  ) => _api.delete(
    Uri.parse(ApiConfig.objectsRelated)
        .replace(
          queryParameters: {
            'to': to,
            'id': id,
            'record': record,
            'field': field,
          },
        )
        .toString(),
  );

  /// Built-in kinds are searched through their community list endpoints and
  /// read the way the matching lookup in `lookup_provider.dart` reads them.
  /// A failed request throws, so it never reads as "no matches".
  Future<List<LinkedRecord>> searchTargets(String target, String query) async {
    final spec = _searchSpec(target);
    if (spec == null) return const [];
    final response = await _api.get(
      spec.url,
      queryParams: {spec.param: query, 'limit': '$linkSearchLimit'},
    );
    final data = response.data;
    if (!response.success || data == null) {
      throw Exception(response.message ?? 'Could not search');
    }
    return [
      for (final row in listFromEnvelope(
        data,
        spec.paths,
      ).take(linkSearchLimit))
        LinkedRecord(
          id: row['id']?.toString() ?? '',
          object: target,
          name: spec.label(row),
        ),
    ];
  }
}

class _SearchSpec {
  const _SearchSpec(this.url, this.paths, this.label, {this.param = 'search'});

  final String url;
  final List<String> paths;
  final String Function(Map<String, dynamic> row) label;
  final String param;
}

String _name(Map<String, dynamic> row) =>
    EntityLookup.fromJson(row, labelKeys: const ['name']).label;

_SearchSpec? _searchSpec(String target) {
  switch (target) {
    case 'lead':
      return _SearchSpec(
        ApiConfig.leads,
        const ['open_leads.open_leads'],
        (row) => EntityLookup.person(
          row,
          fallbackKeys: const ['email', 'company_name'],
        ).label,
      );
    case 'contact':
      return _SearchSpec(ApiConfig.contacts, const [
        'results',
        'contacts',
      ], (row) => ContactLookup.fromJson(row).fullName);
    case 'account':
      return _SearchSpec(ApiConfig.accounts, const [
        'active_accounts.open_accounts',
        'accounts',
        'results',
      ], _name);
    case 'deal':
      return _SearchSpec(ApiConfig.opportunities, const [
        'opportunities',
      ], _name);
    case 'ticket':
      return _SearchSpec(ApiConfig.tickets, const ['cases'], _name);
    case 'task':
      return _SearchSpec(ApiConfig.tasks, const [
        'tasks',
        'results',
      ], (row) => EntityLookup.fromJson(row, labelKeys: const ['title']).label);
  }
  if (target.startsWith('obj:')) {
    final key = target.substring(4);
    try {
      return _SearchSpec(
        ApiConfig.objectRecords(key),
        const ['results'],
        _name,
        param: 'q',
      );
    } on ArgumentError {
      return null;
    }
  }
  return null;
}

final customObjectsApiProvider = Provider<CustomObjectsApi>(
  (ref) => CustomObjectsApi(),
);

final relatedProvider = FutureProvider.autoDispose
    .family<RelatedAnswer?, ({String to, String id})>((ref, arg) async {
      final answer = shownCustomObjects(ref.watch(customObjectsProvider));
      if (answer == null || answer.objects.isEmpty) return null;
      final response = await ApiService().get(
        ApiConfig.objectsRelated,
        queryParams: {'to': arg.to, 'id': arg.id},
      );
      final data = response.data;
      if (!response.success || data == null) return null;
      return RelatedAnswer.fromJson(data);
    });

final linkTargetSearchProvider = FutureProvider.autoDispose
    .family<List<LinkedRecord>, ({String target, String query})>(
      (ref, arg) => ref
          .watch(customObjectsApiProvider)
          .searchTargets(arg.target, arg.query),
      retry: (_, _) => null,
    );

final attachmentBytesProvider = FutureProvider.autoDispose
    .family<Uint8List?, String>((ref, id) async {
      final response = await ApiService().getBytes(
        ApiConfig.attachmentDownload(id),
      );
      return response.success ? response.data : null;
    });

dynamic _blankToNull(dynamic v) => v is String && v.trim().isEmpty ? null : v;

bool _sameSet(Iterable<String> a, Iterable<String> b) {
  final x = a.toSet();
  final y = b.toSet();
  return x.length == y.length && x.containsAll(y);
}

/// What to send for a save. A new record sends what it has; an edit sends only
/// what changed, since the server merges, so an untouched field is never
/// rewritten (and a hidden link held by a one-record field is never sent).
Map<String, dynamic> recordWriteBody({
  required ObjectDefinition definition,
  required String name,
  required Map<String, dynamic> customFields,
  required Map<String, List<String>> links,
  required List<String> assignees,
  ObjectRecord? original,
}) {
  final body = <String, dynamic>{'name': name};

  final customKeys = {for (final f in definition.customFields) f.key};
  final linkKeys = {for (final f in definition.linkFields) f.key};

  final custom = <String, dynamic>{};
  for (final e in customFields.entries) {
    if (!customKeys.contains(e.key)) continue;
    final next = _blankToNull(e.value);
    if (original == null) {
      if (next != null) custom[e.key] = next;
    } else if (next != _blankToNull(original.customFields[e.key])) {
      custom[e.key] = next;
    }
  }
  if (custom.isNotEmpty) body['custom_fields'] = custom;

  final changedLinks = <String, List<String>>{};
  for (final e in links.entries) {
    if (!linkKeys.contains(e.key)) continue;
    if (original == null) {
      if (e.value.isNotEmpty) changedLinks[e.key] = e.value;
      continue;
    }
    final held = original.links[e.key];
    if (held != null && held.readOnly) continue;
    final before = held?.records.map((r) => r.id) ?? const <String>[];
    if (!_sameSet(before, e.value)) changedLinks[e.key] = e.value;
  }
  if (changedLinks.isNotEmpty) body['links'] = changedLinks;

  final sendAssignees = original == null
      ? assignees.isNotEmpty
      : !_sameSet(original.assignedTo.map((p) => p.id), assignees);
  if (sendAssignees) body['assigned_to'] = assignees;
  return body;
}

String _messageText(dynamic v) {
  if (v is List) return v.map((m) => m.toString()).join(' ');
  return v?.toString() ?? '';
}

/// One `<label>: <message>` line per refused field.
String recordWriteError(
  ApiResponse<dynamic> response,
  ObjectDefinition definition,
) {
  final data = response.data;
  if (data is Map) {
    final labels = {for (final f in definition.fields) f.key: f.label};
    final lines = <String>[];

    void add(String label, dynamic v) {
      final text = _messageText(v);
      if (text.isNotEmpty) lines.add('$label: $text');
    }

    if (data['name'] != null) add(definition.summary.nameLabel, data['name']);
    if (data['assigned_to'] != null) add('Assigned to', data['assigned_to']);
    for (final section in const ['custom_fields', 'links']) {
      final nested = data[section];
      if (nested is! Map) continue;
      for (final e in nested.entries) {
        final key = e.key.toString();
        if (key == '_size') {
          final text = _messageText(e.value);
          if (text.isNotEmpty) lines.add(text);
        } else {
          add(labels[key] ?? key, e.value);
        }
      }
    }
    if (lines.isNotEmpty) return lines.join('\n');
    final detail = _messageText(data['detail']);
    if (detail.isNotEmpty) return detail;
  }
  return response.message ?? 'Could not save that record.';
}

/// The object settings write body, as the web's `readObjectForm` builds it.
/// An edit never carries the key; the name label is sent only when filled.
Map<String, dynamic> objectWriteBody({
  required bool creating,
  required String label,
  required String labelPlural,
  String key = '',
  String nameLabel = '',
  String description = '',
  String recordAccess = 'own',
}) {
  final body = <String, dynamic>{
    'label': label.trim(),
    'label_plural': labelPlural.trim(),
    'description': description.trim(),
    'record_access': recordAccess == 'everyone' ? 'everyone' : 'own',
  };
  if (creating) body['key'] = key.trim();
  if (nameLabel.trim().isNotEmpty) body['name_label'] = nameLabel.trim();
  return body;
}

/// Rows with a value keep it (records store it); a new row gets one from its
/// label, or `option_<n>` when the label has no Latin letters or digits.
List<Map<String, String>> _optionRows(List<CustomFieldOption> options) {
  final used = {
    for (final o in options)
      if (o.value.isNotEmpty) o.value,
  };
  var next = 1;
  final rows = <Map<String, String>>[];
  for (final o in options) {
    final label = o.label.trim();
    if (label.isEmpty) continue;
    var value = o.value;
    if (value.isEmpty) {
      value = slugifyOptionValue(label);
      while (value.isEmpty || used.contains(value)) {
        value = 'option_${next++}';
      }
      used.add(value);
    }
    rows.add({'value': value, 'label': label});
  }
  return rows;
}

/// The field write body, as the web's `readFieldForm` builds it. `fieldType`
/// says which shape applies on an edit too, but an edit never sends `key`,
/// `field_type`, `target` or `many`; a link never sends `options` or
/// `is_required`; `is_required` is an explicit bool.
Map<String, dynamic> fieldWriteBody({
  required bool creating,
  required String label,
  required String fieldType,
  String key = '',
  String target = '',
  bool many = false,
  bool isRequired = false,
  int? displayOrder,
  List<CustomFieldOption> options = const [],
}) {
  final isLink = fieldType == 'link';
  final body = <String, dynamic>{'label': label.trim()};
  if (creating) {
    body['key'] = key.trim();
    body['field_type'] = fieldType;
    if (isLink) {
      body['target'] = target;
      body['many'] = many;
    }
  }
  if (!isLink) body['is_required'] = isRequired;
  if (displayOrder != null) body['display_order'] = displayOrder;
  if (fieldType == 'dropdown') body['options'] = _optionRows(options);
  return body;
}

/// The names the object form shows for the keys it sends.
const objectFormLabels = {
  'key': 'Key',
  'label': 'Name (singular)',
  'label_plural': 'Name (plural)',
  'name_label': "What each record's name is called",
  'description': 'Description',
  'record_access': 'Who can see its records',
};

/// The names the field form shows for the keys it sends.
const fieldFormLabels = {
  'key': 'Key',
  'label': 'Label',
  'field_type': 'Type',
  'options': 'Options',
  'target': 'Links to',
  'many': 'How many',
  'is_required': 'Required',
  'display_order': 'Order',
};

/// What the server refused, as one readable line per field or its `detail`.
/// [labels] says what the form calls each key; unknown keys keep their name.
String settingsWriteError(
  ApiResponse<dynamic> response,
  String fallback, {
  Map<String, String> labels = const {},
}) {
  final data = response.data;
  if (data is Map) {
    final detail = _messageText(data['detail']);
    if (detail.isNotEmpty) return detail;
    final lines = [
      for (final e in data.entries)
        if (_messageText(e.value).isNotEmpty)
          '${labels[e.key] ?? e.key}: ${_messageText(e.value)}',
    ];
    if (lines.isNotEmpty) return lines.join('\n');
  }
  return response.message ?? fallback;
}
