import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/profile.dart';
import 'package:bottle_crm/providers/profile_provider.dart';
import 'package:bottle_crm/screens/settings/profile_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// The profile screen is an edit form too, and it had the same hole as the
/// other five: back threw the edits away without asking. Its rule differs from
/// theirs, because the fields only exist while edit mode is on.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Future<void> openProfile(WidgetTester tester) async {
    final router = GoRouter(
      initialLocation: '/more',
      routes: [
        GoRoute(path: '/more', builder: (_, _) => const Text('the more sheet')),
        GoRoute(path: '/profile', builder: (_, _) => const ProfileScreen()),
      ],
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [profileProvider.overrideWith(() => _FakeProfile())],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();
    router.push('/profile');
    await tester.pumpAndSettle();
  }

  Future<void> pressBack(WidgetTester tester) async {
    tester.state<NavigatorState>(find.byType(Navigator).last).maybePop();
    await tester.pumpAndSettle();
  }

  testWidgets('back after changing the name asks first', (tester) async {
    await openProfile(tester);

    await tester.tap(find.byTooltip('Edit profile'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).first, 'Ada King');
    await pressBack(tester);

    expect(find.text('Discard changes?'), findsOneWidget);
    expect(find.text('the more sheet'), findsNothing);
  });

  testWidgets('back while just reading leaves straight away', (tester) async {
    await openProfile(tester);

    await pressBack(tester);

    // The control. Most visits to this screen only look at it, and prompting
    // those would train people to dismiss the dialog without reading it.
    expect(find.text('Discard changes?'), findsNothing);
    expect(find.text('the more sheet'), findsOneWidget);
  });

  testWidgets('opening edit and changing nothing is not a change', (
    tester,
  ) async {
    await openProfile(tester);

    await tester.tap(find.byTooltip('Edit profile'));
    await tester.pumpAndSettle();
    await pressBack(tester);

    // The fields are pre-filled from the saved profile, so being in edit mode
    // is not by itself something to lose.
    expect(find.text('Discard changes?'), findsNothing);
    expect(find.text('the more sheet'), findsOneWidget);
  });
}

class _FakeProfile extends ProfileNotifier {
  @override
  Future<Profile> build() async => const Profile(
    id: 'p1',
    user: AuthUser(id: 'u1', email: 'user@example.com', name: 'Ada Lovelace'),
    phone: '+1 555 0100',
  );
}
