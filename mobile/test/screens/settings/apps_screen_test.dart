import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/automation.dart';
import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/data/models/org_app.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/screens/settings/apps_screen.dart';
import 'package:bottle_crm/screens/settings/settings_hub_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../support/apps_fixtures.dart';
import '../../support/modules_fixtures.dart';

class _NoObjects extends CustomObjectsNotifier {
  @override
  Future<CustomObjectsAnswer?> build() async => null;
}

class _NoRules extends AutomationRulesNotifier {
  @override
  Future<AutomationRulesAnswer> build() async =>
      const AutomationRulesAnswer(rules: []);
}

/// Settings › Apps: the industry apps above the modules, each action
/// previewed in a sheet before it runs, and a server without `/api/apps/`
/// left with the modules page it had.
void main() {
  Future<FakeOrgApps> pump(
    WidgetTester tester, {
    OrgAppsAnswer? apps,
    bool oldServer = false,
    bool failApps = false,
    List<String> off = const [],
    bool admin = true,
    String? error,
    Widget home = const AppsScreen(),
  }) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(600, 4000);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final fake = FakeOrgApps(() async {
      if (failApps) throw Exception('boom');
      return oldServer ? null : (apps ?? appsAnswer());
    }, error: error);
    await tester.pumpWidget(
      ProviderScope(
        key: UniqueKey(),
        overrides: [
          ...modulesOverrides(
            FakeOrgModules(() async => modulesAnswer(off: off)),
            admin: admin,
            apps: fake,
          ),
          customObjectsProvider.overrideWith(_NoObjects.new),
          automationRulesProvider.overrideWith(_NoRules.new),
        ],
        child: MaterialApp(theme: AppTheme.light, home: home),
      ),
    );
    await tester.pumpAndSettle();
    return fake;
  }

  Finder cardOf(String name) => find
      .ancestor(of: find.text(name), matching: find.byType(Container))
      .first;

  Finder buttonIn(String name, String label) =>
      find.descendant(of: cardOf(name), matching: find.text(label));

  testWidgets('the apps sit above the modules, under the title Apps', (
    tester,
  ) async {
    await pump(tester);
    expect(find.text('Apps'), findsOneWidget);
    final apps = tester.getTopLeft(find.text('Industry apps')).dy;
    final modules = tester.getTopLeft(find.text('Modules')).dy;
    final sample = tester.getTopLeft(find.text('Clear sample data')).dy;
    expect(apps, lessThan(modules));
    expect(modules, lessThan(sample));
    expect(
      tester.getTopLeft(find.text('Events and Weddings')).dy,
      lessThan(modules),
    );
    expect(find.text('SELL'), findsOneWidget);
  });

  testWidgets('each app says where it stands and offers what it can', (
    tester,
  ) async {
    await pump(tester, off: ['invoices']);
    expect(buttonIn('Professional Services', 'Install'), findsOneWidget);
    expect(buttonIn('Real Estate', 'Update'), findsOneWidget);
    expect(buttonIn('Real Estate', 'Remove'), findsOneWidget);
    expect(buttonIn('Real Estate', 'Installed'), findsOneWidget);
    expect(
      find.text(
        'Version 1 installed by Ana Admin on 2 Oct 2026. Version 2 is '
        'available.',
      ),
      findsOneWidget,
    );
    expect(
      find.text(
        'Parts for Invoices were skipped because that module was off. '
        'Switch it on below, then update to add them.',
      ),
      findsOneWidget,
    );
    expect(buttonIn('Education Admissions', 'Removed'), findsOneWidget);
    expect(buttonIn('Education Admissions', 'Install'), findsOneWidget);
    expect(buttonIn('Education Admissions', 'Remove'), findsNothing);
  });

  testWidgets('skipped modules alone do not offer an update', (tester) async {
    final current = OrgAppsAnswer(
      apps: [
        OrgApp.fromJson({
          'id': 'real-estate',
          'name': 'Real Estate',
          'version': 2,
          'status': 'installed',
          'installed_version': 2,
          'update_available': false,
          'skipped_modules': ['invoices'],
        }),
      ],
    );
    await pump(tester, apps: current);
    expect(find.textContaining('Update adds them now.'), findsNothing);
    expect(buttonIn('Real Estate', 'Update'), findsNothing);
    expect(buttonIn('Real Estate', 'Remove'), findsOneWidget);
  });

  testWidgets('a same-version update says what it adds', (tester) async {
    final current = OrgAppsAnswer(
      apps: [
        OrgApp.fromJson({
          'id': 'real-estate',
          'name': 'Real Estate',
          'version': 2,
          'status': 'installed',
          'installed_version': 2,
          'update_available': true,
          'skipped_modules': ['invoices'],
        }),
      ],
    );
    await pump(tester, apps: current);
    expect(
      find.textContaining(
        'An update adds the parts skipped while a module was off.',
      ),
      findsOneWidget,
    );
    expect(find.textContaining('Version 2 is available'), findsNothing);
    expect(buttonIn('Real Estate', 'Update'), findsOneWidget);
  });

  testWidgets('switching a module on re-reads the apps', (tester) async {
    final fake = await pump(tester, off: ['invoices']);
    final before = fake.builds;
    await tester.tap(
      find.descendant(
        of: find
            .ancestor(
              of: find.text('Invoices'),
              matching: find.byType(Container),
            )
            .first,
        matching: find.byType(Switch),
      ),
    );
    await tester.pumpAndSettle();
    expect(fake.builds, greaterThan(before));
  });

  testWidgets('install previews what it adds, grouped, and installs with '
      'sample records on by default', (tester) async {
    final fake = await pump(tester);
    await tester.tap(buttonIn('Professional Services', 'Install'));
    await tester.pumpAndSettle();

    expect(fake.previews, [('professional-services', AppAction.install)]);
    expect(find.text('Install Professional Services?'), findsOneWidget);
    final titles = [
      'WORDING',
      'FIELDS',
      'PIPELINES',
      'STAGES',
      'TAGS',
      'LEAD SOURCES',
      'PRODUCTS',
    ];
    final ys = [for (final t in titles) tester.getTopLeft(find.text(t)).dy];
    expect(ys, [...ys]..sort());
    expect(find.text('Budget (max)'), findsOneWidget);
    expect(find.text('Leads'), findsWidgets);
    expect(find.text('Kept'), findsNWidgets(2));
    expect(find.text('Module off'), findsOneWidget);
    expect(find.textContaining('58 example records'), findsOneWidget);
    expect(
      tester.widget<SwitchListTile>(find.byType(SwitchListTile)).value,
      isTrue,
    );

    await tester.tap(find.widgetWithText(FilledButton, 'Install').last);
    await tester.pumpAndSettle();
    expect(fake.installs, [('professional-services', true)]);
    expect(find.text('Professional Services installed.'), findsOneWidget);
  });

  testWidgets('sample records can be left out of an install', (tester) async {
    final fake = await pump(tester);
    await tester.tap(buttonIn('Professional Services', 'Install'));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(SwitchListTile));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Install').last);
    await tester.pumpAndSettle();
    expect(fake.installs, [('professional-services', false)]);
  });

  testWidgets('Cancel on the preview changes nothing', (tester) async {
    final fake = await pump(tester);
    await tester.tap(buttonIn('Professional Services', 'Install'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(fake.installs, isEmpty);
    expect(find.text('Install Professional Services?'), findsNothing);
  });

  testWidgets('update lists the additions and names the stages to add by '
      'hand', (tester) async {
    final fake = await pump(tester);
    await tester.tap(buttonIn('Real Estate', 'Update'));
    await tester.pumpAndSettle();
    expect(find.text('Update Real Estate?'), findsOneWidget);
    expect(find.text('Add by hand'), findsOneWidget);
    expect(find.textContaining('Stages marked Add by hand'), findsOneWidget);
    // Sample records never come with an update.
    expect(find.byType(SwitchListTile), findsNothing);
    await tester.tap(find.widgetWithText(FilledButton, 'Update').last);
    await tester.pumpAndSettle();
    expect(fake.upgrades, ['real-estate']);
    expect(find.text('Real Estate updated.'), findsOneWidget);
  });

  testWidgets('remove says every record stays, and a refusal is shown', (
    tester,
  ) async {
    final fake = await pump(tester, error: 'Only an admin can remove apps.');
    await tester.tap(buttonIn('Real Estate', 'Remove'));
    await tester.pumpAndSettle();
    expect(find.text('Remove Real Estate?'), findsOneWidget);
    expect(find.textContaining('Every record stays'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, 'Remove'));
    await tester.pumpAndSettle();
    expect(fake.removals, ['real-estate']);
    expect(find.text('Only an admin can remove apps.'), findsOneWidget);
  });

  testWidgets('an empty preview says so', (tester) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(600, 4000);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final fake = FakeOrgApps(
      () async => appsAnswer(),
      previewOf: (action) => AppPreview(action: action),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...modulesOverrides(
            FakeOrgModules(() async => modulesAnswer()),
            apps: fake,
          ),
        ],
        child: MaterialApp(theme: AppTheme.light, home: const AppsScreen()),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(buttonIn('Professional Services', 'Install'));
    await tester.pumpAndSettle();
    expect(
      find.text('This organization already has everything this app sets up.'),
      findsOneWidget,
    );
    expect(find.byType(SwitchListTile), findsNothing);
  });

  testWidgets('clear sample data asks first and reports what it kept', (
    tester,
  ) async {
    final fake = await pump(tester);
    await tester.tap(find.text('Clear sample data'));
    await tester.pumpAndSettle();
    expect(find.text('Clear sample data?'), findsOneWidget);
    await tester.tap(find.text('Clear'));
    await tester.pumpAndSettle();
    expect(fake.cleared, 1);
    expect(find.textContaining('Deleted 12 sample records.'), findsOneWidget);
  });

  testWidgets('a 404 from /api/apps/ hides the apps section only', (
    tester,
  ) async {
    await pump(tester, oldServer: true);
    expect(find.text('Industry apps'), findsNothing);
    expect(find.text('Install'), findsNothing);
    expect(find.text('Modules'), findsOneWidget);
    expect(find.text('SELL'), findsOneWidget);
    expect(find.byType(Switch), findsWidgets);
    // Still reachable, below the modules.
    expect(
      tester.getTopLeft(find.text('Clear sample data')).dy,
      greaterThan(tester.getTopLeft(find.text('Timesheet')).dy),
    );
  });

  testWidgets('apps that fail to load offer a retry and leave the modules', (
    tester,
  ) async {
    await pump(tester, failApps: true);
    expect(find.text('Could not load the apps.'), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
    expect(find.text('SELL'), findsOneWidget);
  });

  testWidgets('a member is told, and offered nothing', (tester) async {
    final fake = await pump(tester, admin: false);
    expect(
      find.text('Only an organization admin can manage apps and modules.'),
      findsOneWidget,
    );
    expect(find.text('Install'), findsNothing);
    expect(fake.previews, isEmpty);
  });

  testWidgets('the hub names the row for what the server offers', (
    tester,
  ) async {
    await pump(tester, home: const SettingsHubScreen());
    expect(find.text('Apps'), findsOneWidget);
    expect(find.text('Modules'), findsNothing);

    await pump(tester, home: const SettingsHubScreen(), oldServer: true);
    expect(find.text('Modules'), findsOneWidget);
    expect(find.text('Apps'), findsNothing);

    await pump(tester, home: const SettingsHubScreen(), admin: false);
    expect(find.text('Apps'), findsNothing);
  });
}
