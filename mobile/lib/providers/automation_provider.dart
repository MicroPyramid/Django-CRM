import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/models/automation.dart';
import '../services/api_service.dart';
import '../services/automation_text.dart';
import 'auth_provider.dart';

final automationCatalogueProvider =
    FutureProvider.autoDispose<AutomationCatalogue>((ref) async {
      ref.watch(selectedOrgProvider.select((o) => o?.id));
      final response = await ApiService().get(ApiConfig.automationCatalogue);
      final data = response.data;
      if (!response.success || data == null) {
        throw Exception(response.message ?? 'Could not load the catalogue');
      }
      return AutomationCatalogue.fromJson(data);
    }, retry: (_, _) => null);

class AutomationRulesNotifier extends AsyncNotifier<AutomationRulesAnswer> {
  @override
  Future<AutomationRulesAnswer> build() {
    ref.watch(selectedOrgProvider.select((o) => o?.id));
    return _fetch();
  }

  Future<AutomationRulesAnswer> _fetch() async {
    final response = await ApiService().get(ApiConfig.automationRules);
    final data = response.data;
    if (!response.success || data == null) {
      throw Exception(response.message ?? 'Could not load the rules');
    }
    return AutomationRulesAnswer.fromJson(data);
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  bool _moving = false;

  /// Moves one rule a place and posts every id in the new order. Null on
  /// success, else the message to show.
  Future<String?> move(String id, String direction) async {
    final held = shownAutomationRules(state);
    if (held == null) return 'The rules are still loading.';
    if (_moving) return 'A move is already in progress.';
    final step = switch (direction) {
      'up' => -1,
      'down' => 1,
      _ => null,
    };
    if (step == null) return 'Cannot move a rule $direction.';
    final ids = held.rules.map((r) => r.id).toList();
    final at = ids.indexOf(id);
    if (at < 0) return 'That rule is no longer in the list.';
    final to = at + step;
    if (to < 0 || to >= ids.length) return 'That rule cannot move further.';
    ids.insert(to, ids.removeAt(at));
    _moving = true;
    try {
      final response = await ApiService().post(ApiConfig.automationReorder, {
        'ids': ids,
      });
      if (!response.success) {
        return response.message ?? 'Could not change the order.';
      }
      await refresh();
      return null;
    } finally {
      _moving = false;
    }
  }
}

/// The only way to read the rules for display: Riverpod keeps the previous
/// value through a reload and a failed load, which after an org switch is
/// another org's.
AutomationRulesAnswer? shownAutomationRules(
  AsyncValue<AutomationRulesAnswer> v,
) => v.isLoading || v.hasError ? null : v.value;

final automationRulesProvider =
    AsyncNotifierProvider<AutomationRulesNotifier, AutomationRulesAnswer>(
      AutomationRulesNotifier.new,
      retry: (_, _) => null,
    );

final automationRuleProvider = FutureProvider.autoDispose
    .family<AutomationRule, String>((ref, id) async {
      ref.watch(selectedOrgProvider.select((o) => o?.id));
      final response = await ApiService().get(ApiConfig.automationRule(id));
      final data = response.data;
      if (!response.success || data == null) {
        throw Exception(response.message ?? 'Could not load the rule');
      }
      return AutomationRule.fromJson(data);
    }, retry: (_, _) => null);

final automationRunsProvider = FutureProvider.autoDispose
    .family<RunPage, ({String id, int offset})>((ref, key) async {
      ref.watch(selectedOrgProvider.select((o) => o?.id));
      final response = await ApiService().get(
        ApiConfig.automationRuleRuns(key.id, offset: key.offset),
      );
      final data = response.data;
      if (!response.success || data == null) {
        throw Exception(response.message ?? 'Could not load the runs');
      }
      return RunPage.fromJson(data, offset: key.offset);
    }, retry: (_, _) => null);

typedef RuleWrite = ({AutomationRule? rule, RuleErrors? errors});

/// The writes. After one succeeds the screen invalidates
/// [automationRulesProvider] and the rule's [automationRuleProvider].
class AutomationApi {
  AutomationApi([ApiService? api]) : _api = api ?? ApiService();

  final ApiService _api;

  RuleWrite _written(ApiResponse<Map<String, dynamic>> r) {
    final data = r.data;
    if (r.success && data != null) {
      return (rule: AutomationRule.fromJson(data), errors: null);
    }
    return (rule: null, errors: RuleErrors.fromResponse(r));
  }

  Future<RuleWrite> create(Map<String, dynamic> body) async =>
      _written(await _api.post(ApiConfig.automationRules, body));

  Future<RuleWrite> update(String id, Map<String, dynamic> body) async =>
      _written(await _api.patch(ApiConfig.automationRule(id), body));

  Future<String?> switchOff(String id) async {
    final r = await _api.patch(ApiConfig.automationRule(id), {
      'is_active': false,
    });
    return r.success ? null : (r.message ?? 'Could not switch the rule off.');
  }

  Future<String?> delete(String id) async {
    final r = await _api.delete(ApiConfig.automationRule(id));
    return r.success ? null : (r.message ?? 'Could not delete the rule.');
  }

  Future<({List<RunStep> steps, String? error})> tryRule(
    String id,
    String recordId,
  ) async {
    final r = await _api.post(ApiConfig.automationRuleTry(id), {
      'record_id': recordId,
    });
    if (r.statusCode == 404) {
      return (
        steps: <RunStep>[],
        error: 'That record does not exist, or you cannot open it.',
      );
    }
    final data = r.data;
    if (!r.success || data == null) {
      return (
        steps: <RunStep>[],
        error: r.message ?? 'Could not try the rule.',
      );
    }
    final raw = data['steps'];
    final steps = raw is List
        ? raw
              .whereType<Map>()
              .map((m) => RunStep.fromJson(Map<String, dynamic>.from(m)))
              .toList()
        : <RunStep>[];
    return (steps: steps, error: null);
  }
}

final automationApiProvider = Provider<AutomationApi>((ref) => AutomationApi());
