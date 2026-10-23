import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/models/org_module.dart';
import '../services/api_service.dart';
import 'auth_provider.dart';

/// What `GET /api/org/modules/` says about the org. `null` means an older API
/// (a 404), where every module is on. Any other failure is an error state.
class OrgModulesNotifier extends AsyncNotifier<OrgModulesAnswer?> {
  String? _orgId;

  @override
  Future<OrgModulesAnswer?> build() async {
    final orgId = ref.watch(selectedOrgProvider.select((o) => o?.id));
    _orgId = orgId;
    final response = await ApiService().get(ApiConfig.orgModules);
    if (response.statusCode == 404) return null;
    final data = response.data;
    if (!response.success || data == null) {
      throw Exception(response.message ?? 'Could not load modules');
    }
    return OrgModulesAnswer.fromJson(data, orgId: orgId);
  }

  /// Saves the whole off list and order. Returns the server's refusals, or
  /// an empty list once saved.
  Future<List<String>> save({
    required List<String> off,
    required List<String> order,
  }) async {
    final orgId = _orgId;
    final response = await ApiService().put(ApiConfig.orgModules, {
      'off': off,
      'order': order,
    });
    final data = response.data;
    if (response.success && data != null) {
      if (ref.mounted && _orgId == orgId) {
        state = AsyncData(OrgModulesAnswer.fromJson(data, orgId: orgId));
      }
      return const [];
    }
    if (response.statusCode == 400 && data != null) {
      final messages = <String>[
        for (final field in const ['off', 'order'])
          if (data[field] is List)
            for (final m in data[field] as List) m.toString(),
      ];
      if (messages.isNotEmpty) return messages;
    }
    return [response.message ?? 'Could not save the modules.'];
  }
}

// No automatic retry: a failure shows as an error at once and reads as on.
final orgModulesProvider =
    AsyncNotifierProvider<OrgModulesNotifier, OrgModulesAnswer?>(
      OrgModulesNotifier.new,
      retry: (_, _) => null,
    );

/// The one rule for "on". With no answer for the selected org (never loaded,
/// an older API, another org's answer, a key with no row) everything is on.
/// A reload or a failed reload keeps the last answer for this org in force.
bool moduleIsOn(
  AsyncValue<OrgModulesAnswer?> value,
  String? orgId,
  String key,
) {
  final answer = value.value;
  if (answer == null || answer.orgId != orgId) return true;
  return answer.isOn(key);
}

/// The answer for the selected org, else null.
final shownModulesProvider = Provider<OrgModulesAnswer?>((ref) {
  final orgId = ref.watch(selectedOrgProvider.select((o) => o?.id));
  final value = ref.watch(orgModulesProvider);
  final answer = value.value;
  return answer != null && answer.orgId == orgId ? answer : null;
});

final moduleOnProvider = Provider.family<bool, String>((ref, key) {
  final orgId = ref.watch(selectedOrgProvider.select((o) => o?.id));
  return moduleIsOn(ref.watch(orgModulesProvider), orgId, key);
});

final productsOnProvider = Provider<bool>((ref) {
  final orgId = ref.watch(selectedOrgProvider.select((o) => o?.id));
  final value = ref.watch(orgModulesProvider);
  return moduleIsOn(value, orgId, 'deals') ||
      moduleIsOn(value, orgId, 'invoices');
});

/// Reloads the module list when any request is answered `module_off`, unless
/// a reload is already running. Watched once from the app root.
final moduleOffListenerProvider = Provider<void>((ref) {
  final api = ApiService();
  api.setModuleOffCallback((_) {
    if (ref.read(orgModulesProvider).isLoading) return;
    ref.invalidate(orgModulesProvider);
  });
  ref.onDispose(() => api.setModuleOffCallback(null));
});

/// Ask again for the module list unless a request for it is already running,
/// so opening More in quick succession sends one request, not three.
void reloadOrgModulesIfIdle(WidgetRef ref) {
  if (ref.read(orgModulesProvider).isLoading) return;
  ref.invalidate(orgModulesProvider);
}
