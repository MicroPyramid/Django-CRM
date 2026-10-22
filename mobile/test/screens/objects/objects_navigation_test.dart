import 'package:bottle_crm/data/models/custom_object.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/custom_objects_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/settings/more_screen.dart';
import 'package:bottle_crm/screens/settings/settings_hub_screen.dart';
import 'package:bottle_crm/widgets/common/app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

class _FakeObjects extends CustomObjectsNotifier {
  _FakeObjects(this.answer);

  final CustomObjectsAnswer? answer;

  @override
  Future<CustomObjectsAnswer?> build() async => answer;
}

class _FailsOnce extends CustomObjectsNotifier {
  _FailsOnce(this.builds);

  final List<int> builds;

  @override
  Future<CustomObjectsAnswer?> build() async {
    builds.add(builds.length);
    if (builds.length == 1) throw Exception('timeout');
    return const CustomObjectsAnswer(
      hasCustomObjects: true,
      objects: [_property],
    );
  }
}

class _AlwaysFails extends CustomObjectsNotifier {
  _AlwaysFails(this.onBuild);

  final void Function() onBuild;

  @override
  Future<CustomObjectsAnswer?> build() async {
    onBuild();
    throw Exception('502');
  }
}

const _property = ObjectSummary(
  key: 'property',
  label: 'Property',
  labelPlural: 'Properties',
);

Widget _app(Widget home, CustomObjectsAnswer? answer, {bool admin = false}) =>
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        customObjectsProvider.overrideWith(() => _FakeObjects(answer)),
        isOrgAdminProvider.overrideWithValue(admin),
      ],
      child: MaterialApp(home: home),
    );

Future<void> _scrollTo(WidgetTester tester, Finder finder) async {
  tester
      .state<ScrollableState>(find.byType(Scrollable).first)
      .position
      .jumpTo(0);
  await tester.pump();
  await tester.scrollUntilVisible(
    finder,
    200,
    scrollable: find.byType(Scrollable).first,
  );
}

void main() {
  testWidgets('More lists each active object', (tester) async {
    await tester.pumpWidget(
      _app(
        const MoreScreen(),
        const CustomObjectsAnswer(
          hasCustomObjects: true,
          objects: [
            _property,
            ObjectSummary(
              key: 'old',
              label: 'Old',
              labelPlural: 'Olds',
              isActive: false,
            ),
          ],
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('OBJECTS'), findsOneWidget);
    expect(find.text('Properties'), findsOneWidget);
    expect(find.text('Olds'), findsNothing);
  });

  Future<ProviderContainer> erroredContainer(
    CustomObjectsNotifier Function() notifier,
  ) async {
    final container = ProviderContainer(
      overrides: [
        customObjectsProvider.overrideWith(notifier),
        isOrgAdminProvider.overrideWithValue(false),
      ],
    );
    addTearDown(container.dispose);
    container.listen(customObjectsProvider, (_, _) {});
    await expectLater(
      container.read(customObjectsProvider.future),
      throwsException,
    );
    return container;
  }

  Future<void> openMore(
    WidgetTester tester,
    ProviderContainer container,
  ) async {
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(home: MoreScreen()),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('More asks again once after a failed answer, not per rebuild', (
    tester,
  ) async {
    final builds = <int>[];
    final container = await erroredContainer(() => _FailsOnce(builds));
    expect(builds, hasLength(1));

    await openMore(tester, container);
    expect(builds, hasLength(2));
    expect(find.text('Properties'), findsOneWidget);

    await tester.pump(const Duration(seconds: 1));
    await tester.pumpAndSettle();
    expect(builds, hasLength(2));
  });

  testWidgets(
    'More shows nothing and asks once while the answer stays failed',
    (tester) async {
      var builds = 0;
      final container = await erroredContainer(
        () => _AlwaysFails(() => builds++),
      );
      await openMore(tester, container);
      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();

      expect(find.text('OBJECTS'), findsNothing);
      expect(builds, 2);
    },
  );

  testWidgets(
    'switching to More asks again for a failed answer on every switch, not per rebuild',
    (tester) async {
      var builds = 0;
      final container = await erroredContainer(
        () => _AlwaysFails(() => builds++),
      );
      final router = GoRouter(
        initialLocation: '/b0',
        routes: [
          StatefulShellRoute.indexedStack(
            builder: (context, state, shell) =>
                AppShell(navigationShell: shell),
            branches: [
              for (var i = 0; i < 5; i++)
                StatefulShellBranch(
                  routes: [
                    GoRoute(
                      path: '/b$i',
                      builder: (_, _) => Scaffold(body: Text('branch $i')),
                    ),
                  ],
                ),
              StatefulShellBranch(
                routes: [
                  GoRoute(
                    path: AppRoutes.more,
                    builder: (_, _) => const MoreScreen(),
                  ),
                ],
              ),
            ],
          ),
        ],
      );
      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp.router(routerConfig: router),
        ),
      );
      await tester.pumpAndSettle();
      expect(builds, 1);

      Future<void> switchToMore() async {
        await tester.tap(find.text('More'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        expect(find.text('Organization settings'), findsOneWidget);
      }

      await switchToMore();
      expect(builds, 2, reason: 'the first visit asks once, not twice');

      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();
      expect(builds, 2);

      await tester.tap(find.text('Home'));
      await tester.pumpAndSettle();
      expect(find.text('branch 0'), findsOneWidget);
      expect(builds, 2);

      await switchToMore();
      expect(builds, 3, reason: 'More was kept alive and never asked again');

      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();
      expect(builds, 3);
    },
  );

  testWidgets('More shows no objects when the server has none', (tester) async {
    await tester.pumpWidget(_app(const MoreScreen(), null));
    await tester.pumpAndSettle();
    expect(find.text('OBJECTS'), findsNothing);

    await tester.pumpWidget(
      _app(const MoreScreen(), const CustomObjectsAnswer()),
    );
    await tester.pumpAndSettle();
    expect(find.text('OBJECTS'), findsNothing);
  });

  testWidgets(
    'the hub shows Objects to an admin with writes on and no objects',
    (tester) async {
      await tester.pumpWidget(
        _app(
          const SettingsHubScreen(),
          const CustomObjectsAnswer(hasCustomObjects: true),
          admin: true,
        ),
      );
      await tester.pumpAndSettle();
      await _scrollTo(tester, find.text('Objects'));
      expect(find.text('Objects'), findsOneWidget);
    },
  );

  testWidgets('the hub hides Objects from a member until an object exists', (
    tester,
  ) async {
    await tester.pumpWidget(
      _app(
        const SettingsHubScreen(),
        const CustomObjectsAnswer(hasCustomObjects: true),
      ),
    );
    await tester.pumpAndSettle();
    await _scrollTo(tester, find.text('Help center'));
    expect(find.text('Objects'), findsNothing);

    await tester.pumpWidget(
      _app(
        const SettingsHubScreen(),
        const CustomObjectsAnswer(hasCustomObjects: true, objects: [_property]),
      ),
    );
    await tester.pumpAndSettle();
    await _scrollTo(tester, find.text('Objects'));
    expect(find.text('Objects'), findsOneWidget);

    await tester.pumpWidget(_app(const SettingsHubScreen(), null, admin: true));
    await tester.pumpAndSettle();
    await _scrollTo(tester, find.text('Help center'));
    expect(find.text('Objects'), findsNothing);
  });

  test('links each kind to its screen', () {
    expect(linkedRecordRoute('lead', 'a1'), '/leads/a1');
    expect(linkedRecordRoute('contact', 'a1'), '/contacts/a1');
    expect(linkedRecordRoute('account', 'a1'), '/accounts/a1');
    expect(linkedRecordRoute('deal', 'a1'), '/deals/a1');
    expect(linkedRecordRoute('ticket', 'a1'), '/tickets/a1');
    expect(linkedRecordRoute('task', 'a1'), '/tasks/a1');
    expect(
      linkedRecordRoute('obj:property', 'a1'),
      AppRoutes.objectRecord('property', 'a1'),
    );
    expect(linkedRecordRoute('invoice', 'a1'), isNull);
    for (final bad in ['obj:', 'obj:Bad Key', 'obj:../x', 'obj:a/b']) {
      expect(linkedRecordRoute(bad, 'a1'), isNull, reason: bad);
    }
  });

  test('object routes are built under /more/objects', () {
    expect(AppRoutes.objectRecords('property'), '/more/objects/property');
    expect(
      AppRoutes.objectRecordCreate('property'),
      '/more/objects/property/new',
    );
    expect(AppRoutes.objectRecord('property', 'x'), '/more/objects/property/x');
    expect(
      AppRoutes.objectRecordEdit('property', 'x'),
      '/more/objects/property/x/edit',
    );
    expect(AppRoutes.settingsObjects, '/more/settings/objects');
    expect(
      AppRoutes.settingsObject('property'),
      '/more/settings/objects/property',
    );
  });
}
