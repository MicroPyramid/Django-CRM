import 'package:bottle_crm/data/models/org_module.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/org_modules_provider.dart';
import 'package:flutter_riverpod/misc.dart' show Override;

const _groups = {
  'deals': 'sell',
  'leads': 'sell',
  'goals': 'sell',
  'tasks': 'serve',
  'tickets': 'serve',
  'knowledge_base': 'serve',
  'documents': 'serve',
  'invoices': 'bill',
  'timesheet': 'bill',
};

const _needs = {'goals': 'deals', 'timesheet': 'tickets'};

/// The nine modules in default order. [off] lists the keys whose own switch is
/// off; a module whose need is off is unavailable even when its switch is on.
OrgModulesAnswer modulesAnswer({
  List<String> off = const [],
  bool canEdit = true,
  Map<String, String> labels = const {},
}) {
  bool own(String k) => !off.contains(k);
  bool available(String k) {
    final need = _needs[k];
    return own(k) && (need == null || available(need));
  }

  return OrgModulesAnswer(
    canEdit: canEdit,
    modules: [
      for (final k in _groups.keys)
        OrgModule(
          key: k,
          label: labels[k] ?? defaultModuleLabels[k]!,
          group: _groups[k]!,
          covers: 'Covers $k.',
          stops: 'Stops $k.',
          enabled: own(k),
          available: available(k),
          needs: _needs[k],
        ),
    ],
  );
}

class FakeOrgModules extends OrgModulesNotifier {
  FakeOrgModules(this.answer, {this.refusals = const []});

  final Future<OrgModulesAnswer?> Function() answer;
  final List<String> refusals;
  final List<({List<String> off, List<String> order})> saved = [];

  @override
  Future<OrgModulesAnswer?> build() => answer();

  @override
  Future<List<String>> save({
    required List<String> off,
    required List<String> order,
  }) async {
    saved.add((off: off, order: order));
    return refusals;
  }
}

List<Override> modulesOverrides(FakeOrgModules fake, {bool admin = true}) => [
  isOrgAdminProvider.overrideWithValue(admin),
  selectedOrgProvider.overrideWithValue(null),
  orgModulesProvider.overrideWith(() => fake),
];
