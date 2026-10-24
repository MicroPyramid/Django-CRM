import 'package:bottle_crm/data/models/org_app.dart';
import 'package:bottle_crm/providers/org_apps_provider.dart';

/// The four apps as `GET /api/apps/` lists them for an org that installed
/// Real Estate at version 1, now at 2, with its invoice parts skipped.
OrgAppsAnswer appsAnswer({List<String> skipped = const ['invoices']}) =>
    OrgAppsAnswer.fromJson({
      'apps': [
        {
          'id': 'professional-services',
          'name': 'Professional Services',
          'description': 'Agencies, consultancies and accounting firms.',
          'version': 1,
          'status': 'not_installed',
          'installed_version': null,
          'update_available': false,
          'skipped_modules': [],
          'installed_at': null,
          'installed_by_details': null,
        },
        {
          'id': 'real-estate',
          'name': 'Real Estate',
          'description': 'Brokers, agencies and developers.',
          'version': 2,
          'status': 'installed',
          'installed_version': 1,
          'update_available': true,
          'skipped_modules': skipped,
          'installed_at': '2026-10-02T09:00:00Z',
          'installed_by_details': {'id': 'p1', 'name': 'Ana Admin'},
        },
        {
          'id': 'education-admissions',
          'name': 'Education Admissions',
          'description': 'Coaching centres, institutes and colleges.',
          'version': 1,
          'status': 'removed',
          'installed_version': 1,
          'update_available': false,
          'skipped_modules': [],
          'installed_at': '2026-09-01T09:00:00Z',
          'installed_by_details': null,
        },
        {
          'id': 'events-weddings',
          'name': 'Events and Weddings',
          'description': 'Planners, agencies and venues.',
          'version': 1,
          'status': 'not_installed',
          'installed_version': null,
          'update_available': false,
          'skipped_modules': [],
          'installed_at': null,
          'installed_by_details': null,
        },
      ],
    });

/// A preview listing one of each item type the contract names.
AppPreview previewFor(AppAction action) => AppPreview.fromJson({
  'action': action.value,
  'items': [
    {
      'type': 'product',
      'target': null,
      'label': 'Site visit package',
      'effect': 'add',
    },
    {
      'type': 'field',
      'target': 'lead',
      'label': 'Budget (max)',
      'effect': 'add',
    },
    {
      'type': 'wording',
      'target': null,
      'label': 'Deals will be called Listings',
      'effect': 'keep',
    },
    {
      'type': 'field',
      'target': 'lead',
      'label': 'Preferred location',
      'effect': 'keep',
    },
    {
      'type': 'pipeline',
      'target': 'lead',
      'label': 'Property enquiries',
      'effect': 'add',
    },
    {
      'type': 'stage',
      'target': 'lead',
      'label': 'Site visit done',
      'effect': 'add_by_hand',
    },
    {'type': 'tag', 'target': null, 'label': 'Hot buyer', 'effect': 'add'},
    {
      'type': 'source',
      'target': null,
      'label': 'Property portal',
      'effect': 'skipped_module',
    },
  ],
  'sample_data': {'offered': true, 'default_on': true, 'records': 58},
}, action);

/// Records every call. [answer] is what the list loads as; null is an older
/// server's 404. [error] makes every write fail with it.
class FakeOrgApps extends OrgAppsNotifier {
  FakeOrgApps(this.answer, {this.error, this.previewOf = previewFor});

  final Future<OrgAppsAnswer?> Function() answer;
  final String? error;
  final AppPreview Function(AppAction action) previewOf;

  final previews = <(String, AppAction)>[];
  final installs = <(String, bool)>[];
  final upgrades = <String>[];
  final removals = <String>[];
  final signupInstalls = <String>[];
  var cleared = 0;
  var builds = 0;

  @override
  Future<OrgAppsAnswer?> build() {
    builds++;
    return answer();
  }

  @override
  Future<({AppPreview? preview, String? error})> preview(
    String appId,
    AppAction action,
  ) async {
    previews.add((appId, action));
    return (preview: previewOf(action), error: null);
  }

  @override
  Future<String?> install(String appId, {required bool sampleData}) async {
    installs.add((appId, sampleData));
    return error;
  }

  @override
  Future<String?> upgrade(String appId) async {
    upgrades.add(appId);
    return error;
  }

  @override
  Future<String?> remove(String appId) async {
    removals.add(appId);
    return error;
  }

  @override
  Future<String?> installAtSignup(String appId) async {
    signupInstalls.add(appId);
    return error;
  }

  @override
  Future<({String? error, int deleted, int retained})> clearSampleData() async {
    cleared++;
    return (error: error, deleted: 12, retained: 1);
  }
}
