import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/screens/auth/org_create_screen.dart';
import 'package:bottle_crm/screens/auth/org_selection_screen.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

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
}

Widget _host(Widget screen, {List<Organization> orgs = const []}) =>
    ProviderScope(
      overrides: [authProvider.overrideWith(() => _FakeAuth(orgs))],
      child: MaterialApp(home: screen),
    );

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
