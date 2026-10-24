import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/models/org_app.dart';
import '../services/api_service.dart';
import 'auth_provider.dart';
import 'invoice_extras_provider.dart';
import 'lead_pipelines_provider.dart';
import 'lead_sources_provider.dart';
import 'lookup_provider.dart';
import 'org_modules_provider.dart';
import 'settings_provider.dart';

/// What `GET /api/apps/` says about the org. `null` means an older API (a
/// 404), which hides the apps section and nothing else. Any other failure is
/// an error state. Modelled on [OrgModulesNotifier].
class OrgAppsNotifier extends AsyncNotifier<OrgAppsAnswer?> {
  String? _orgId;

  @override
  Future<OrgAppsAnswer?> build() async {
    final orgId = ref.watch(selectedOrgProvider.select((o) => o?.id));
    _orgId = orgId;
    final response = await ApiService().get(ApiConfig.apps);
    if (response.statusCode == 404) return null;
    final data = response.data;
    if (!response.success || data == null) {
      throw Exception(response.message ?? 'Could not load apps');
    }
    return OrgAppsAnswer.fromJson(data, orgId: orgId);
  }

  /// What [action] would do to [appId]. The server writes nothing for this.
  Future<({AppPreview? preview, String? error})> preview(
    String appId,
    AppAction action,
  ) async {
    final response = await ApiService().get(
      ApiConfig.appPreview(appId, action.value),
    );
    final data = response.data;
    if (!response.success || data == null) {
      return (preview: null, error: _message(response));
    }
    return (preview: AppPreview.fromJson(data, action), error: null);
  }

  /// Each returns null once done, or the server's reason.
  Future<String?> install(String appId, {required bool sampleData}) =>
      _act(ApiConfig.appInstall(appId), {'sample_data': sampleData});

  Future<String?> upgrade(String appId) =>
      _act(ApiConfig.appUpgrade(appId), const {});

  Future<String?> remove(String appId) =>
      _act(ApiConfig.appRemove(appId), const {});

  /// The install signup makes, with sample records as the pack choice always
  /// gave. A server without apps answers 404, and there the pack apply it
  /// replaced does the same job.
  Future<String?> installAtSignup(String appId) async {
    final response = await ApiService().post(ApiConfig.appInstall(appId), {
      'sample_data': true,
    });
    if (response.statusCode == 404) {
      final legacy = await ApiService().post(
        ApiConfig.packApply(appId),
        const {},
      );
      return legacy.success ? null : _message(legacy);
    }
    if (!response.success) return _message(response);
    _applied(response.data);
    return null;
  }

  /// Deletes the demo records apps created, and nothing else.
  ///
  /// `retained` counts sample records kept because real work has since been
  /// attached to them: a normal outcome, not a partial failure.
  Future<({String? error, int deleted, int retained})> clearSampleData() async {
    final response = await ApiService().delete(ApiConfig.packSampleData);
    final data = response.data;
    if (!response.success || data == null) {
      return (error: _message(response), deleted: 0, retained: 0);
    }
    var retained = 0;
    final byType = data['retained_by_type'];
    if (byType is Map) {
      for (final value in byType.values) {
        if (value is num) retained += value.round();
      }
    }
    return (
      error: null,
      deleted: (data['deleted'] as num?)?.round() ?? 0,
      retained: retained,
    );
  }

  Future<String?> _act(String url, Map<String, dynamic> body) async {
    final response = await ApiService().post(url, body);
    if (!response.success) return _message(response);
    _applied(response.data);
    return null;
  }

  /// Puts the answered app in place, or asks again when there is no list
  /// for this org yet, so a list still loading cannot land stale. Then drops
  /// the settings an app adds to or turns off.
  void _applied(Map<String, dynamic>? data) {
    if (!ref.mounted) return;
    final app = data?['app'];
    final current = state.value;
    if (app is Map<String, dynamic> &&
        current != null &&
        current.orgId == _orgId &&
        !state.isLoading) {
      state = AsyncData(current.withApp(OrgApp.fromJson(app)));
    } else {
      ref.invalidateSelf();
    }
    ref.invalidate(orgModulesProvider);
    ref.invalidate(customFieldDefinitionsProvider);
    ref.invalidate(customFieldsProvider);
    ref.invalidate(leadPipelinesProvider);
    ref.invalidate(leadSourcesProvider);
    ref.invalidate(tagsLookupProvider);
    ref.invalidate(tagSettingsProvider);
    ref.invalidate(productsProvider);
  }
}

/// The pack views refuse with a bare `{"error": "..."}`; everything else
/// reads through the service's own message.
String _message(ApiResponse<Map<String, dynamic>> response) {
  final error = response.data?['error'];
  if (error is String && error.trim().isNotEmpty) return error;
  final raw = response.message;
  return (raw == null || raw.trim().isEmpty) ? 'Something went wrong' : raw;
}

// No automatic retry, as with the modules list.
final orgAppsProvider = AsyncNotifierProvider<OrgAppsNotifier, OrgAppsAnswer?>(
  OrgAppsNotifier.new,
  retry: (_, _) => null,
);

/// The answer for the selected org, else null: an older API, a failed or
/// unfinished load, or another org's answer.
final shownAppsProvider = Provider<OrgAppsAnswer?>((ref) {
  final orgId = ref.watch(selectedOrgProvider.select((o) => o?.id));
  final answer = ref.watch(orgAppsProvider).value;
  return answer != null && answer.orgId == orgId ? answer : null;
});
