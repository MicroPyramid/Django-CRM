import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/api_envelope.dart';
import '../data/models/lead_source.dart';
import '../services/api_service.dart';

/// The org's lead sources. Every member reads them; every write is admin-only
/// server-side, so the settings screen hiding its controls is UX.
class LeadSourcesNotifier extends AsyncNotifier<LeadSourcesAnswer> {
  final ApiService _api = ApiService();

  @override
  Future<LeadSourcesAnswer> build() => _fetch();

  Future<LeadSourcesAnswer> _fetch() async {
    final response = await _api.get(ApiConfig.leadSources);
    // The list is not tied to Leads, so a 404 only ever means a server
    // older than it, which validates against the fixed values.
    if (response.statusCode == 404) return const LeadSourcesAnswer.legacy();
    final data = response.data;
    if (!response.success || data == null) {
      throw Exception(response.message ?? 'Could not load the lead sources.');
    }
    final sources = listFromEnvelope(data, const [
      'sources',
    ]).map(LeadSource.fromJson).toList();
    sources.sort((a, b) => a.order.compareTo(b.order));
    return LeadSourcesAnswer(sources: sources);
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  /// Each write returns null on success, else the sentence to show.
  Future<String?> add(String label) =>
      _write(_api.post(ApiConfig.leadSources, {'label': label.trim()}));

  Future<String?> rename(String id, String label) =>
      _write(_api.patch(ApiConfig.leadSource(id), {'label': label.trim()}));

  Future<String?> setActive(String id, bool active) =>
      _write(_api.patch(ApiConfig.leadSource(id), {'is_active': active}));

  /// Moves one source a place and posts every key in the new order.
  Future<String?> move(String key, int step) async {
    final held = state.value;
    if (held == null) return 'The sources are still loading.';
    final keys = held.sources.map((s) => s.key).toList();
    final at = keys.indexOf(key);
    final to = at + step;
    if (at < 0 || to < 0 || to >= keys.length) {
      return 'That source cannot move further.';
    }
    keys.insert(to, keys.removeAt(at));
    return _write(_api.post(ApiConfig.leadSourcesOrder, {'keys': keys}));
  }

  Future<String?> _write(
    Future<ApiResponse<Map<String, dynamic>>> request,
  ) async {
    final response = await request;
    if (response.statusCode == 403) {
      return 'Only an admin can change lead sources.';
    }
    if (!response.success) {
      return response.message ?? 'Could not save the lead sources.';
    }
    await refresh();
    return null;
  }
}

// No automatic retry: a failure shows at once and is asked again on demand.
final leadSourcesProvider =
    AsyncNotifierProvider<LeadSourcesNotifier, LeadSourcesAnswer>(
      LeadSourcesNotifier.new,
      retry: (_, _) => null,
    );

/// The only way to read the list for display: Riverpod keeps the previous
/// value through a reload and a failed load, which after an org switch is
/// another org's.
LeadSourcesAnswer? shownLeadSources(AsyncValue<LeadSourcesAnswer> v) =>
    v.isLoading || v.hasError ? null : v.value;

/// The list for a picker that is opening, from a tap: waits for a load in
/// flight and asks again after a failure. Null when it still cannot be had.
Future<LeadSourcesAnswer?> leadSourcesForPicker(WidgetRef ref) async {
  final v = ref.read(leadSourcesProvider);
  if (v.hasError && !v.isLoading) ref.invalidate(leadSourcesProvider);
  try {
    return await ref.read(leadSourcesProvider.future);
  } catch (_) {
    return null;
  }
}
