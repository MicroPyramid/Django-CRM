import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/api_envelope.dart';
import '../data/models/custom_field_definition.dart';
import '../data/models/macro.dart';
import '../services/api_service.dart';

/// The org settings cluster.
///
/// Custom fields is the first of the cluster's pages to reach the phone. The
/// rest (routing, escalation, inbound email, ticket approvals, macros, tags,
/// business hours, reopen rules) share the same shape, so they will land
/// beside this rather than in files of their own.
///
/// Every write here is admin-only server-side. The screens hide the controls
/// from everyone else, which is UX: `CustomFieldDefinitionListCreateView.post`
/// and `CustomFieldDefinitionDetailView.put`/`.delete` each call
/// `is_org_admin` first and answer 403, so hiding a button is not what keeps a
/// member out.

/// The server's own message where there is one. These endpoints refuse for
/// reasons a user can act on ("Admin access required", "key must be a
/// lowercase slug starting with a letter").
String _message(dynamic response) {
  final errors = response.data?['errors'];
  if (errors is Map) {
    for (final value in errors.values) {
      if (value is List && value.isNotEmpty) return value.first.toString();
      if (value is String && value.trim().isNotEmpty) return value;
    }
  }
  if (errors is String && errors.trim().isNotEmpty) return errors;
  final detail = response.data?['message'];
  if (detail is String && detail.trim().isNotEmpty) return detail;
  final raw = response.message as String?;
  return (raw == null || raw.trim().isEmpty) ? 'Something went wrong' : raw;
}

/// The definition list plus the counts the settings screen shows above it.
class CustomFieldsState {
  const CustomFieldsState({
    this.fields = const [],
    this.count = 0,
    this.active = 0,
    this.modelsExtended = 0,
    this.requiredWithGaps = 0,
  });

  final List<CustomFieldDefinition> fields;

  /// From the server's `totals` block, which is computed over the org's whole
  /// definition set rather than the rows on screen. Recomputing these from
  /// `fields` would give the same answer today and quietly diverge the moment
  /// the list is filtered.
  final int count;
  final int active;
  final int modelsExtended;

  /// Required fields that some records have no value for. The banner exists
  /// because marking a field required binds writes from that point on and
  /// backfills nothing.
  final int requiredWithGaps;

  /// Fields grouped by the record type they extend, since "what do we collect
  /// on a ticket" is how anyone looks for one. Groups are ordered by the
  /// target's display name; fields inside a group by `display_order`, then
  /// label, matching the order the record forms render them in.
  List<MapEntry<String, List<CustomFieldDefinition>>> get grouped {
    final byTarget = <String, List<CustomFieldDefinition>>{};
    for (final field in fields) {
      byTarget.putIfAbsent(field.targetModel, () => []).add(field);
    }
    final entries = byTarget.entries.toList()
      ..sort(
        (a, b) => customFieldTargetLabel(
          a.key,
        ).compareTo(customFieldTargetLabel(b.key)),
      );
    for (final entry in entries) {
      entry.value.sort((a, b) {
        final byOrder = a.displayOrder.compareTo(b.displayOrder);
        return byOrder != 0 ? byOrder : a.label.compareTo(b.label);
      });
    }
    return entries;
  }
}

class CustomFieldsNotifier extends AsyncNotifier<CustomFieldsState> {
  final ApiService _api = ApiService();

  @override
  Future<CustomFieldsState> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  /// No `active_only`, because this is the screen that turns a field back on
  /// and cannot offer that for a row it never fetched. No `include_counts`
  /// either: `records_missing_value` is the number this page is here to show,
  /// so it is the one caller that wants the scan.
  Future<CustomFieldsState> _fetch() async {
    final response = await _api.get(ApiConfig.customFieldDefinitions);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load custom fields');
    }
    final body = response.data!;
    final fields = listFromEnvelope(body, const [
      'definitions',
    ]).map(CustomFieldDefinition.fromJson).toList(growable: false);
    final totals = body['totals'];
    return CustomFieldsState(
      fields: fields,
      count: _int(totals, 'count', fields.length),
      active: _int(totals, 'active', fields.where((f) => f.isActive).length),
      modelsExtended: _int(
        totals,
        'models_extended',
        fields
            .where((f) => f.isActive)
            .map((f) => f.targetModel)
            .toSet()
            .length,
      ),
      requiredWithGaps: _int(
        totals,
        'required_with_gaps',
        fields.where((f) => f.isRequired && f.recordsMissingValue > 0).length,
      ),
    );
  }

  Future<String?> createField(Map<String, dynamic> payload) async {
    final response = await _api.post(ApiConfig.customFieldDefinitions, payload);
    if (!response.success) return _message(response);
    await refresh();
    return null;
  }

  Future<String?> updateField(String id, Map<String, dynamic> payload) async {
    final response = await _api.put(ApiConfig.customField(id), payload);
    if (!response.success) return _message(response);
    await refresh();
    return null;
  }

  /// Turn a field off. `DELETE` is a soft delete server-side: it flips
  /// `is_active` and leaves every stored value readable, which is why nothing
  /// on the screen calls this Delete.
  Future<String?> deactivateField(String id) async {
    final response = await _api.delete(ApiConfig.customField(id));
    if (!response.success) return _message(response);
    await refresh();
    return null;
  }

  /// Turn a field back on. There is no reactivate endpoint, so this is the
  /// same PUT carrying only `is_active`. See [customFieldActivatePayload] for
  /// why it must not reuse the edit body.
  Future<String?> activateField(String id) =>
      updateField(id, customFieldActivatePayload());
}

final customFieldsProvider =
    AsyncNotifierProvider<CustomFieldsNotifier, CustomFieldsState>(
      CustomFieldsNotifier.new,
    );

// ---------------------------------------------------------------------------
// Macros, the saved replies
// ---------------------------------------------------------------------------

/// The macros visible to the caller, plus the placeholder reference.
///
/// Visibility is the server's decision: `_visible_qs` returns every org macro
/// plus the caller's own personal ones, so nothing here filters rows. A
/// stranger's personal macro never arrives.
class MacrosState {
  const MacrosState({
    this.macros = const [],
    this.placeholders = const [],
    this.orgCount = 0,
    this.personalCount = 0,
    this.inactiveCount = 0,
    this.brokenCount = 0,
  });

  final List<Macro> macros;

  /// `{token, resolves}` pairs from `SUPPORTED_PLACEHOLDERS`. Server-owned, so
  /// the reference the form shows is exactly what the renderer expands.
  final List<MacroPlaceholder> placeholders;

  final int orgCount;
  final int personalCount;
  final int inactiveCount;

  /// Macros carrying a `%token%` the renderer does not know. Those render
  /// literally into a customer reply, which is why they are counted.
  final int brokenCount;
}

class MacroPlaceholder {
  const MacroPlaceholder({required this.token, required this.resolves});

  final String token;
  final String resolves;
}

class MacrosNotifier extends AsyncNotifier<MacrosState> {
  final ApiService _api = ApiService();

  @override
  Future<MacrosState> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  /// Unfiltered on purpose. The reply-box picker asks for `?active=true`, but
  /// this screen is the one that turns a macro back on and cannot offer that
  /// for a row it never fetched.
  Future<MacrosState> _fetch() async {
    final response = await _api.get(ApiConfig.macros);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load saved replies');
    }
    final body = response.data!;
    final macros = listFromEnvelope(body, const [
      'results',
    ]).map(Macro.fromJson).toList(growable: false);
    final totals = body['totals'];
    final rawPlaceholders = body['placeholders'];
    return MacrosState(
      macros: macros,
      placeholders: rawPlaceholders is List
          ? [
              for (final p in rawPlaceholders)
                if (p is Map)
                  MacroPlaceholder(
                    token: p['token']?.toString() ?? '',
                    resolves: p['resolves']?.toString() ?? '',
                  ),
            ]
          : const [],
      orgCount: _int(totals, 'org', macros.where((m) => !m.isPersonal).length),
      personalCount: _int(
        totals,
        'personal',
        macros.where((m) => m.isPersonal).length,
      ),
      inactiveCount: _int(
        totals,
        'inactive',
        macros.where((m) => !m.isActive).length,
      ),
      brokenCount: _int(
        totals,
        'with_unknown_placeholders',
        macros.where((m) => m.unknownPlaceholders.isNotEmpty).length,
      ),
    );
  }

  Future<String?> createMacro(Map<String, dynamic> payload) async {
    final response = await _api.post(ApiConfig.macros, payload);
    if (!response.success) return _macroMessage(response);
    await refresh();
    return null;
  }

  /// PATCH, not PUT. `MacroDetailView.put` runs the serializer with
  /// `partial=False` and `MacroSerializer` requires both `title` and `body`,
  /// so a PUT missing either is a 400 for no reason the user could see.
  Future<String?> updateMacro(String id, Map<String, dynamic> payload) async {
    final response = await _api.patch(ApiConfig.macro(id), payload);
    if (!response.success) return _macroMessage(response);
    await refresh();
    return null;
  }

  /// Turn an org macro off, or delete a personal one for good. One endpoint;
  /// which happens is the row's scope, decided server-side.
  Future<String?> removeMacro(String id) async {
    final response = await _api.delete(ApiConfig.macro(id));
    if (!response.success) return _macroMessage(response);
    await refresh();
    return null;
  }

  Future<String?> activateMacro(String id) =>
      updateMacro(id, macroActivatePayload());
}

final macrosProvider = AsyncNotifierProvider<MacrosNotifier, MacrosState>(
  MacrosNotifier.new,
);

/// The active macros, for the reply box.
///
/// A separate read from [macrosProvider] rather than a filter over it: the
/// picker wants `?active=true` server-side and must not pull the turned-off
/// rows onto a ticket screen at all, and the two are opened from different
/// places at different times.
final activeMacrosProvider = FutureProvider<List<Macro>>((ref) async {
  final url = Uri.parse(
    ApiConfig.macros,
  ).replace(queryParameters: {'active': 'true'}).toString();
  final response = await ApiService().get(url);
  if (!response.success || response.data == null) {
    throw Exception(response.message ?? 'Failed to load saved replies');
  }
  return listFromEnvelope(response.data!, const [
    'results',
  ]).map(Macro.fromJson).toList(growable: false);
});

/// Expand a macro against a ticket and return the text to insert.
///
/// Server-side substitution: `render_macro` owns the supported token set, and
/// an unknown token is left literal so the agent sees it rather than sending a
/// reply with a silent hole in it. Returns the message on failure instead of
/// throwing, matching the write methods above.
Future<({String? text, String? error})> renderMacro({
  required String macroId,
  required String ticketId,
}) async {
  final response = await ApiService().post(ApiConfig.macroRender(macroId), {
    'case_id': ticketId,
  });
  if (!response.success) {
    return (text: null, error: _macroMessage(response));
  }
  final rendered = response.data?['rendered_body'];
  if (rendered is! String) {
    return (text: null, error: 'The saved reply came back empty.');
  }
  return (text: rendered, error: null);
}

/// The macro endpoints answer `{"error": "..."}` and `{"detail": "..."}` where
/// the rest of the app answers `{"errors": ...}`, so [_message] alone would
/// miss both. The wording matters here: "Only admins can manage org-scope
/// macros" is the difference between a bug and a rule.
String _macroMessage(dynamic response) {
  final error = response.data?['error'];
  if (error is String && error.trim().isNotEmpty) return error;
  final detail = response.data?['detail'];
  if (detail is String && detail.trim().isNotEmpty) return detail;
  return _message(response);
}

int _int(dynamic totals, String key, int fallback) {
  if (totals is Map && totals[key] is int) return totals[key] as int;
  return fallback;
}
