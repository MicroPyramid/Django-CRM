import '../data/models/org_module.dart';

/// The modules a route needs: all of [keys], or any one of them when [any].
class ModuleNeed {
  final List<String> keys;
  final bool any;

  const ModuleNeed(this.keys, {this.any = false});
}

const _leads = ModuleNeed(['leads']);
const _deals = ModuleNeed(['deals']);
const _goals = ModuleNeed(['goals']);
const _tasks = ModuleNeed(['tasks']);
const _tickets = ModuleNeed(['tickets']);
const _knowledgeBase = ModuleNeed(['knowledge_base']);
const _timesheet = ModuleNeed(['timesheet']);
const _invoices = ModuleNeed(['invoices']);
const _products = ModuleNeed(['invoices', 'deals'], any: true);
const _documents = ModuleNeed(['documents']);

/// Route prefixes by module. A route not under any of them is core. A `:param`
/// segment matches any one segment; the longest matching prefix wins.
const _needs = <String, ModuleNeed>{
  '/leads': _leads,
  '/more/settings/lead-pipelines': _leads,
  '/deals': _deals,
  '/more/settings/deal-pipelines': _deals,
  '/goals': _goals,
  '/tasks': _tasks,
  '/more/profile/calendar-feed': _tasks,
  '/tickets': _tickets,
  '/more/settings/routing': _tickets,
  '/more/settings/escalation': _tickets,
  '/more/settings/business-hours': _tickets,
  '/more/settings/reopen': _tickets,
  '/more/settings/macros': _tickets,
  '/more/settings/inbound-email': _tickets,
  '/more/settings/ticket-approvals': _tickets,
  '/solutions': _knowledgeBase,
  '/more/settings/help-center': _knowledgeBase,
  '/timesheet': _timesheet,
  '/invoices': _invoices,
  '/accounts/:id/statement': _invoices,
  '/invoices/products': _products,
  '/documents': _documents,
};

List<String> _segments(String path) => [
  for (final s in path.split('?').first.split('/'))
    if (s.isNotEmpty) s,
];

/// The module need of a route, by the longest whole-segment prefix of [path].
/// Null for a core route.
ModuleNeed? needFor(String path) {
  final given = _segments(path);
  ModuleNeed? best;
  var bestLength = 0;
  for (final entry in _needs.entries) {
    final prefix = _segments(entry.key);
    if (prefix.length <= bestLength || prefix.length > given.length) continue;
    var matches = true;
    for (var i = 0; i < prefix.length; i++) {
      if (!prefix[i].startsWith(':') && prefix[i] != given[i]) {
        matches = false;
        break;
      }
    }
    if (matches) {
      best = entry.value;
      bestLength = prefix.length;
    }
  }
  return best;
}

/// The module that refuses [need]: the first off key of an all-need, or the
/// first key of an any-need when none is on. Null when the need is met or
/// there is no answer (everything is on).
String? refusedModule(ModuleNeed need, OrgModulesAnswer? modules) {
  if (modules == null) return null;
  if (need.any) {
    return need.keys.any(modules.isOn) ? null : need.keys.first;
  }
  for (final key in need.keys) {
    if (!modules.isOn(key)) return key;
  }
  return null;
}
