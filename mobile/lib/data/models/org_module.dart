const defaultModuleLabels = {
  'deals': 'Pipeline',
  'leads': 'Leads',
  'goals': 'Goals',
  'tasks': 'Tasks',
  'tickets': 'Tickets',
  'knowledge_base': 'Knowledge base',
  'documents': 'Documents',
  'invoices': 'Invoices',
  'timesheet': 'Timesheet',
};

const moduleGroups = ['sell', 'serve', 'bill'];

String _str(dynamic v, [String fallback = '']) => v is String ? v : fallback;

/// One row of `GET /api/org/modules/`.
class OrgModule {
  final String key;
  final String label;
  final String group;
  final String covers;
  final String stops;
  final bool enabled;
  final bool available;
  final String? needs;

  const OrgModule({
    required this.key,
    required this.label,
    required this.group,
    this.covers = '',
    this.stops = '',
    this.enabled = true,
    this.available = true,
    this.needs,
  });

  factory OrgModule.fromJson(Map<String, dynamic> json) {
    final key = _str(json['key']);
    final enabled = json['enabled'] is bool ? json['enabled'] as bool : true;
    final need = json['needs'];
    return OrgModule(
      key: key,
      label: _str(json['label'], defaultModuleLabels[key] ?? key),
      group: _str(json['group']),
      covers: _str(json['covers']),
      stops: _str(json['stops']),
      enabled: enabled,
      available: json['available'] is bool
          ? json['available'] as bool
          : enabled,
      needs: need is String && need.isNotEmpty ? need : null,
    );
  }
}

/// The answer of `GET /api/org/modules/`, tagged with the org it was asked for.
class OrgModulesAnswer {
  final String? orgId;
  final List<OrgModule> modules;
  final bool canEdit;

  const OrgModulesAnswer({
    this.orgId,
    this.modules = const [],
    this.canEdit = false,
  });

  factory OrgModulesAnswer.fromJson(
    Map<String, dynamic> json, {
    String? orgId,
  }) {
    final rows = json['modules'];
    return OrgModulesAnswer(
      orgId: orgId,
      modules: [
        if (rows is List)
          for (final r in rows)
            if (r is Map &&
                r['key'] is String &&
                (r['key'] as String).isNotEmpty)
              OrgModule.fromJson(Map<String, dynamic>.from(r)),
      ],
      canEdit: json['can_edit'] == true,
    );
  }

  OrgModule? _row(String key) {
    for (final m in modules) {
      if (m.key == key) return m;
    }
    return null;
  }

  /// A module with no row reads as on.
  bool isOn(String key) => _row(key)?.available ?? true;

  bool get productsOn => isOn('deals') || isOn('invoices');

  String labelOf(String key) =>
      _row(key)?.label ?? defaultModuleLabels[key] ?? key;

  /// The `PUT` body that flips one module's own switch and keeps the order
  /// as served. Null for a key with no row.
  ({List<String> off, List<String> order})? switchBody(String key, bool on) {
    if (_row(key) == null) return null;
    return (
      off: [
        for (final m in modules)
          if (m.key == key ? !on : !m.enabled) m.key,
      ],
      order: [for (final m in modules) m.key],
    );
  }

  /// The `PUT` body after moving one module a place `up` or `down` within its
  /// group. Null at the ends, for an unknown key or for any other direction.
  ({List<String> off, List<String> order})? moveBody(
    String key,
    String direction,
  ) {
    if (direction != 'up' && direction != 'down') return null;
    final at = modules.indexWhere((m) => m.key == key);
    if (at < 0) return null;
    final group = modules[at].group;
    final step = direction == 'up' ? -1 : 1;
    var to = at + step;
    while (to >= 0 && to < modules.length && modules[to].group != group) {
      to += step;
    }
    if (to < 0 || to >= modules.length) return null;
    final order = [for (final m in modules) m.key];
    order[at] = modules[to].key;
    order[to] = key;
    return (
      off: [
        for (final m in modules)
          if (!m.enabled) m.key,
      ],
      order: order,
    );
  }
}
