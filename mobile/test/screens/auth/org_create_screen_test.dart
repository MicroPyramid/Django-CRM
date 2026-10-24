import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/org_app.dart';
import 'package:bottle_crm/data/models/org_settings.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/org_apps_provider.dart';
import 'package:bottle_crm/providers/settings_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/auth/org_create_screen.dart';
import 'package:bottle_crm/screens/auth/org_selection_screen.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../support/apps_fixtures.dart';

/// Mobile could not create an organization at all, while the org picker's empty
/// state told people to "create a new organization" and gave them nowhere to do
/// it. A user who signed in before anyone had invited them reached a screen
/// whose only working control was Sign Out.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('the picker offers a way out', () {
    testWidgets('a user with no organizations is given the action', (
      tester,
    ) async {
      await tester.pumpWidget(
        _host(const OrgSelectionScreen(), orgs: const []),
      );
      await tester.pump();

      expect(find.text('Create an organization'), findsOneWidget);
    });

    testWidgets('so is a user who already belongs to one', (tester) async {
      await tester.pumpWidget(
        _host(
          const OrgSelectionScreen(),
          orgs: const [Organization(id: 'org-1', name: 'Acme', role: 'ADMIN')],
        ),
      );
      await tester.pump();

      // Belonging to one org does not mean you cannot start another, which is
      // what the web has always allowed from the same screen.
      expect(find.text('Create an organization'), findsOneWidget);
      expect(find.text('Acme'), findsOneWidget);
    });
  });

  group('the create form', () {
    testWidgets('will not submit a blank name', (tester) async {
      await tester.pumpWidget(_host(const OrgCreateScreen()));
      await tester.pump();

      await tester.tap(find.text('Create organization'));
      await tester.pump();

      expect(find.text('Give the organization a name'), findsOneWidget);
    });

    testWidgets('refuses the characters the server refuses', (tester) async {
      await tester.pumpWidget(_host(const OrgCreateScreen()));
      await tester.pump();

      await tester.enterText(find.byType(TextFormField), 'Acme & Sons #1');
      await tester.tap(find.text('Create organization'));
      await tester.pump();

      // The server's `validate_name` is the rule that decides; this only saves
      // the round trip.
      expect(
        find.text('Letters, numbers, spaces, hyphens and dots only'),
        findsOneWidget,
      );
    });

    testWidgets('back after typing a name asks first', (tester) async {
      final router = GoRouter(
        initialLocation: '/picker',
        routes: [
          GoRoute(path: '/picker', builder: (_, _) => const Text('the picker')),
          GoRoute(path: '/new', builder: (_, _) => const OrgCreateScreen()),
        ],
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [authProvider.overrideWith(() => _FakeAuth(const []))],
          child: MaterialApp.router(routerConfig: router),
        ),
      );
      await tester.pumpAndSettle();
      router.push('/new');
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextFormField), 'Acme Inc.');
      tester.state<NavigatorState>(find.byType(Navigator).last).maybePop();
      await tester.pumpAndSettle();

      expect(find.text('Discard changes?'), findsOneWidget);
      expect(find.text('the picker'), findsNothing);
    });

    testWidgets('a created organization opens the import welcome, not the '
        'dashboard', (tester) async {
      final router = GoRouter(
        initialLocation: AppRoutes.orgCreate,
        routes: [
          GoRoute(
            path: AppRoutes.orgCreate,
            builder: (_, _) => const OrgCreateScreen(),
          ),
          GoRoute(
            path: AppRoutes.importWelcome,
            builder: (_, _) => const Text('the welcome screen'),
          ),
          GoRoute(
            path: AppRoutes.dashboard,
            builder: (_, _) => const Text('the dashboard'),
          ),
        ],
      );
      await tester.pumpWidget(
        ProviderScope(
          overrides: [authProvider.overrideWith(_CreatingAuth.new)],
          child: MaterialApp.router(routerConfig: router),
        ),
      );
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextFormField), 'Acme Inc.');
      await tester.tap(find.text('Create organization'));
      await tester.pumpAndSettle();

      // The web's org/new sends a new workspace to /welcome the same way.
      expect(find.text('the welcome screen'), findsOneWidget);
      expect(find.text('the dashboard'), findsNothing);
    });

    testWidgets('accepts an ordinary name', (tester) async {
      await tester.pumpWidget(_host(const OrgCreateScreen()));
      await tester.pump();

      await tester.enterText(find.byType(TextFormField), 'Acme Inc.');
      await tester.tap(find.text('Create organization'));
      await tester.pump();

      // The control: a validator that rejected everything would pass both
      // tests above.
      expect(find.text('Give the organization a name'), findsNothing);
      expect(
        find.text('Letters, numbers, spaces, hyphens and dots only'),
        findsNothing,
      );
    });
  });

  group('the industry choice', () {
    testWidgets('offers the packs the server lists, and a way to skip', (
      tester,
    ) async {
      await tester.pumpWidget(_creating(apps: _apps()));
      await tester.pumpAndSettle();

      expect(find.text('What kind of business is this?'), findsOneWidget);
      expect(find.text('Skip for now'), findsOneWidget);
      expect(find.text('Professional services'), findsOneWidget);
      expect(find.text('Real estate'), findsOneWidget);
    });

    testWidgets('is left out when the pack list is empty', (tester) async {
      await tester.pumpWidget(
        _creating(apps: _apps(), packs: () async => const []),
      );
      await tester.pumpAndSettle();

      expect(find.text('What kind of business is this?'), findsNothing);
    });

    testWidgets('is left out when the pack list fails to load', (tester) async {
      await tester.pumpWidget(
        _creating(apps: _apps(), packs: () async => throw Exception('offline')),
      );
      await tester.pumpAndSettle();

      expect(find.text('What kind of business is this?'), findsNothing);
      // The form itself still works without it.
      expect(find.text('Create organization'), findsOneWidget);
    });

    testWidgets('the chosen app is installed on the new organization', (
      tester,
    ) async {
      final apps = _apps();
      await tester.pumpWidget(_creating(apps: apps));
      await tester.pumpAndSettle();

      await _create(tester, pick: 'Real estate');

      expect(apps.signupInstalls, ['real-estate']);
      expect(find.text('the welcome screen'), findsOneWidget);
    });

    testWidgets('skipping installs nothing', (tester) async {
      final apps = _apps();
      await tester.pumpWidget(_creating(apps: apps));
      await tester.pumpAndSettle();

      await _create(tester);

      expect(apps.signupInstalls, isEmpty);
      expect(find.text('the welcome screen'), findsOneWidget);
    });

    testWidgets('an app that will not install still leaves the organization '
        'created, and says so', (tester) async {
      final apps = _apps(error: 'Only admins can install an app.');
      await tester.pumpWidget(_creating(apps: apps));
      await tester.pumpAndSettle();

      await _create(tester, pick: 'Professional services');

      expect(apps.signupInstalls, ['professional-services']);
      expect(find.text('the welcome screen'), findsOneWidget);
      expect(
        find.textContaining('the industry setup did not install'),
        findsOneWidget,
      );
    });

    testWidgets('a create the server refuses installs no app', (tester) async {
      final apps = _apps();
      await tester.pumpWidget(_creating(apps: apps, createFails: true));
      await tester.pumpAndSettle();

      await _create(tester, pick: 'Real estate');

      expect(apps.signupInstalls, isEmpty);
      expect(find.text('That name is taken.'), findsOneWidget);
      expect(find.text('the welcome screen'), findsNothing);
    });
  });
}

Widget _host(Widget screen, {List<Organization> orgs = const []}) =>
    ProviderScope(
      overrides: [
        authProvider.overrideWith(() => _FakeAuth(orgs)),
        orgPacksProvider.overrideWith((ref) async => const <VerticalPack>[]),
      ],
      child: MaterialApp(home: screen),
    );

const _packs = [
  VerticalPack(
    id: 'professional-services',
    name: 'Professional services',
    description: 'Agencies, consultancies and accounting firms.',
  ),
  VerticalPack(id: 'real-estate', name: 'Real estate'),
];

/// The create screen under a router, so a finished create lands somewhere
/// assertable. [apps] records which apps were installed.
Widget _creating({
  required FakeOrgApps apps,
  Future<List<VerticalPack>> Function()? packs,
  bool createFails = false,
}) {
  final router = GoRouter(
    initialLocation: AppRoutes.orgCreate,
    routes: [
      GoRoute(
        path: AppRoutes.orgCreate,
        builder: (_, _) => const OrgCreateScreen(),
      ),
      // A Scaffold like the real welcome screen's, so a snackbar raised on
      // the way there has somewhere to show.
      GoRoute(
        path: AppRoutes.importWelcome,
        builder: (_, _) => const Scaffold(body: Text('the welcome screen')),
      ),
    ],
  );
  return ProviderScope(
    overrides: [
      authProvider.overrideWith(
        createFails ? _RefusingAuth.new : _CreatingAuth.new,
      ),
      orgPacksProvider.overrideWith(
        (ref) => packs == null ? Future.value(_packs) : packs(),
      ),
      orgAppsProvider.overrideWith(() => apps),
    ],
    child: MaterialApp.router(routerConfig: router),
  );
}

Future<void> _create(WidgetTester tester, {String? pick}) async {
  await tester.enterText(find.byType(TextFormField), 'Acme Inc.');
  if (pick != null) {
    await tester.ensureVisible(find.text(pick));
    await tester.pumpAndSettle();
    await tester.tap(find.text(pick));
    await tester.pump();
  }
  await tester.ensureVisible(find.text('Create organization'));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Create organization'));
  await tester.pumpAndSettle();
}

class _FakeAuth extends AuthNotifier {
  _FakeAuth(this.orgs);

  final List<Organization> orgs;

  @override
  AuthState build() => AuthState(
    user: const AuthUser(id: 'user-1', email: 'user@example.com'),
    organizations: orgs,
    selectedOrganization: orgs.isEmpty ? null : orgs.first,
    isAuthenticated: true,
  );
}

/// A create that succeeds, as `AuthService.createOrganization` does once the
/// server has made the org and selected it.
class _CreatingAuth extends _FakeAuth {
  _CreatingAuth() : super(const []);

  @override
  Future<String?> createOrganization(String name, {String? timezone}) async =>
      null;
}

class _RefusingAuth extends _FakeAuth {
  _RefusingAuth() : super(const []);

  @override
  Future<String?> createOrganization(String name, {String? timezone}) async =>
      'That name is taken.';
}

/// [error] makes every install fail with it.
FakeOrgApps _apps({String? error}) =>
    FakeOrgApps(() async => const OrgAppsAnswer(), error: error);
