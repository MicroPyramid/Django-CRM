import 'custom_field_definition.dart' show customFieldTargets;

/// An industry app's state in this org.
enum AppStatus {
  notInstalled('not_installed'),
  installed('installed'),
  removed('removed');

  const AppStatus(this.value);

  final String value;

  static AppStatus fromString(Object? value) => AppStatus.values.firstWhere(
    (s) => s.value == value,
    orElse: () => AppStatus.notInstalled,
  );
}

/// What an admin can do to an app. [value] is the URL segment and the
/// preview's `?action=`.
enum AppAction {
  install('install'),
  upgrade('upgrade'),
  remove('remove');

  const AppAction(this.value);

  final String value;

  static AppAction fromString(Object? value, AppAction fallback) => AppAction
      .values
      .firstWhere((a) => a.value == value, orElse: () => fallback);
}

String _str(Object? v) => v == null ? '' : v.toString();

/// One row of `GET /api/apps/`. Manifests store `version` as a number or a
/// string, so both versions are kept as text.
class OrgApp {
  const OrgApp({
    required this.id,
    required this.name,
    this.description = '',
    this.version = '',
    this.status = AppStatus.notInstalled,
    this.installedVersion,
    this.updateAvailable = false,
    this.skippedModules = const [],
    this.installedAt,
    this.installedByName,
  });

  final String id;
  final String name;
  final String description;
  final String version;
  final AppStatus status;
  final String? installedVersion;
  final bool updateAvailable;

  /// Module keys whose parts were skipped because the module was off.
  final List<String> skippedModules;

  final DateTime? installedAt;
  final String? installedByName;

  factory OrgApp.fromJson(Map<String, dynamic> json) {
    final skipped = json['skipped_modules'];
    final by = json['installed_by_details'];
    final byName = by is Map ? _str(by['name']).trim() : '';
    final installed = json['installed_version'];
    return OrgApp(
      id: _str(json['id']),
      name: _str(json['name']),
      description: _str(json['description']),
      version: _str(json['version']),
      status: AppStatus.fromString(json['status']),
      installedVersion: installed == null ? null : _str(installed),
      updateAvailable: json['update_available'] == true,
      skippedModules: [
        if (skipped is List)
          for (final key in skipped)
            if (key is String && key.isNotEmpty) key,
      ],
      installedAt: DateTime.tryParse(_str(json['installed_at'])),
      installedByName: byName.isEmpty ? null : byName,
    );
  }

  /// The actions offered, in button order. The server sets
  /// `update_available` for a newer version and for a skipped module that is
  /// now on.
  List<AppAction> get actions {
    if (status != AppStatus.installed) return const [AppAction.install];
    return [if (updateAvailable) AppAction.upgrade, AppAction.remove];
  }
}

/// `GET /api/apps/`, tagged with the org it was asked for.
class OrgAppsAnswer {
  const OrgAppsAnswer({this.orgId, this.apps = const []});

  final String? orgId;
  final List<OrgApp> apps;

  factory OrgAppsAnswer.fromJson(Map<String, dynamic> json, {String? orgId}) {
    final rows = json['apps'];
    return OrgAppsAnswer(
      orgId: orgId,
      apps: [
        if (rows is List)
          for (final r in rows)
            if (r is Map && _str(r['id']).isNotEmpty)
              OrgApp.fromJson(Map<String, dynamic>.from(r)),
      ],
    );
  }

  /// This answer with [app] in place of the row of the same id.
  OrgAppsAnswer withApp(OrgApp app) => OrgAppsAnswer(
    orgId: orgId,
    apps: [for (final a in apps) a.id == app.id ? app : a],
  );
}

/// One line of a preview: what happens to one wording key, field, pipeline,
/// stage, tag, source or product.
class AppPreviewItem {
  const AppPreviewItem({
    required this.type,
    required this.label,
    required this.effect,
    this.target,
  });

  final String type;
  final String label;
  final String effect;
  final String? target;

  factory AppPreviewItem.fromJson(Map<String, dynamic> json) {
    final target = _str(json['target']);
    return AppPreviewItem(
      type: _str(json['type']),
      label: _str(json['label']),
      effect: _str(json['effect']),
      target: target.isEmpty ? null : target,
    );
  }
}

/// A preview's items of one type, under the title the sheet shows.
typedef AppPreviewGroup = ({String title, List<AppPreviewItem> items});

const _typeOrder = [
  'wording',
  'field',
  'pipeline',
  'stage',
  'tag',
  'source',
  'product',
];

const _typeTitles = {
  'wording': 'Wording',
  'field': 'Fields',
  'pipeline': 'Pipelines',
  'stage': 'Stages',
  'tag': 'Tags',
  'source': 'Lead sources',
  'product': 'Products',
};

/// `GET /api/apps/<id>/preview/?action=`: what an action would do, and
/// whether sample records may come with an install.
class AppPreview {
  const AppPreview({
    required this.action,
    this.items = const [],
    this.sampleOffered = false,
    this.sampleDefaultOn = false,
    this.sampleRecords = 0,
  });

  final AppAction action;
  final List<AppPreviewItem> items;
  final bool sampleOffered;
  final bool sampleDefaultOn;
  final int sampleRecords;

  factory AppPreview.fromJson(Map<String, dynamic> json, AppAction asked) {
    final rows = json['items'];
    final sample = json['sample_data'];
    return AppPreview(
      action: AppAction.fromString(json['action'], asked),
      items: [
        if (rows is List)
          for (final r in rows)
            if (r is Map) AppPreviewItem.fromJson(Map<String, dynamic>.from(r)),
      ],
      sampleOffered: sample is Map && sample['offered'] == true,
      sampleDefaultOn: sample is Map && sample['default_on'] == true,
      sampleRecords: sample is Map && sample['records'] is num
          ? (sample['records'] as num).toInt()
          : 0,
    );
  }

  /// The items grouped by type in a fixed order, served order within a group.
  /// A type this build does not know follows the known ones, titled by type.
  List<AppPreviewGroup> get groups {
    final byType = <String, List<AppPreviewItem>>{};
    for (final item in items) {
      byType.putIfAbsent(item.type, () => []).add(item);
    }
    final types = [
      ..._typeOrder.where(byType.containsKey),
      ...byType.keys.where((t) => !_typeOrder.contains(t)),
    ];
    return [
      for (final t in types)
        (title: _typeTitles[t] ?? _sentence(t), items: byType[t]!),
    ];
  }

  /// Stages new to a pipeline the org already has, which an update leaves
  /// for the admin to add.
  bool get hasHandWork => items.any((i) => i.effect == 'add_by_hand');
}

/// The short word beside a preview row.
String appEffectLabel(String effect) => switch (effect) {
  'add' => 'New',
  'keep' => 'Kept',
  'turn_off' => 'Turned off',
  'turn_on' => 'Back on',
  'restore_wording' => 'Back to default',
  'skipped_module' => 'Module off',
  'add_by_hand' => 'Add by hand',
  _ => _sentence(effect),
};

const _targetLabels = {
  'lead': 'Leads',
  'contact': 'Contacts',
  'account': 'Accounts',
  'deal': 'Deals',
  'opportunity': 'Deals',
  'ticket': 'Tickets',
  'case': 'Tickets',
  'task': 'Tasks',
  'invoice': 'Invoices',
  'estimate': 'Estimates',
  'recurring_invoice': 'Recurring invoices',
  'recurringinvoice': 'Recurring invoices',
};

/// "Leads" for `lead` or `Lead`; an unknown target reads as itself.
String appTargetLabel(String target) =>
    customFieldTargets[target] ??
    _targetLabels[target.toLowerCase()] ??
    _sentence(target);

String _sentence(String raw) {
  final text = raw.replaceAll('_', ' ').trim();
  return text.isEmpty ? text : '${text[0].toUpperCase()}${text.substring(1)}';
}
