import 'package:bottle_crm/widgets/forms/unsaved_changes.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// Three form screens already carried a discard prompt and it fired on none of
/// them, because `canPop` was computed during `build` and typing into a field
/// never rebuilds its parent. The prompt was correct and simply unreachable.
///
/// So the test that matters is the one that types and then presses back
/// WITHOUT any rebuild in between. Against the old code it walks straight out
/// of the form.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  /// Opens the form the way the app does: pushed on top of a list, so there is
  /// somewhere to go back to. The form never calls setState when its field
  /// changes, which is what every real form here does.
  Future<void> openForm(
    WidgetTester tester, {
    required TextEditingController controller,
    bool isSaving = false,
  }) async {
    final router = GoRouter(
      initialLocation: '/list',
      routes: [
        GoRoute(path: '/list', builder: (_, _) => const Text('the list')),
        GoRoute(
          path: '/form',
          builder: (_, _) => UnsavedChangesGuard(
            hasUnsavedChanges: () => controller.text.isNotEmpty,
            isSaving: isSaving,
            child: Scaffold(body: TextField(controller: controller)),
          ),
        ),
      ],
    );
    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.pumpAndSettle();
    router.push('/form');
    await tester.pumpAndSettle();
  }

  /// What the OS back gesture does. `maybePop` is the call that consults
  /// PopScope, which a direct `pop` bypasses.
  Future<void> pressBack(WidgetTester tester) async {
    final navigator = tester.state<NavigatorState>(find.byType(Navigator).last);
    navigator.maybePop();
    await tester.pumpAndSettle();
  }

  testWidgets('back after typing asks before throwing the work away', (
    tester,
  ) async {
    final controller = TextEditingController();
    await openForm(tester, controller: controller);

    await tester.enterText(
      find.byType(TextField),
      'Important Deal I do not Want to lose',
    );
    await pressBack(tester);

    expect(find.text('Discard changes?'), findsOneWidget);
    expect(find.text('the list'), findsNothing);
  });

  testWidgets('back on an untouched form leaves without a prompt', (
    tester,
  ) async {
    final controller = TextEditingController();
    await openForm(tester, controller: controller);

    await pressBack(tester);

    // The control. A guard that always prompted would pass the test above.
    expect(find.text('Discard changes?'), findsNothing);
    expect(find.text('the list'), findsOneWidget);
  });

  testWidgets('Cancel keeps the form and the typing', (tester) async {
    final controller = TextEditingController();
    await openForm(tester, controller: controller);
    await tester.enterText(find.byType(TextField), 'half-written note');
    await pressBack(tester);

    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    expect(find.text('the list'), findsNothing);
    expect(controller.text, 'half-written note');
  });

  testWidgets('Discard leaves', (tester) async {
    final controller = TextEditingController();
    await openForm(tester, controller: controller);
    await tester.enterText(find.byType(TextField), 'half-written note');
    await pressBack(tester);

    await tester.tap(find.text('Discard'));
    await tester.pumpAndSettle();

    expect(find.text('the list'), findsOneWidget);
  });

  testWidgets('dismissing the prompt keeps the form, it does not leave', (
    tester,
  ) async {
    final controller = TextEditingController();
    await openForm(tester, controller: controller);
    await tester.enterText(find.byType(TextField), 'half-written note');
    await pressBack(tester);

    // Tapping the scrim returns null, which must read as "keep", never as
    // "discard".
    await tester.tapAt(const Offset(20, 20));
    await tester.pumpAndSettle();

    expect(find.text('the list'), findsNothing);
  });

  testWidgets('back does nothing while a save is in flight', (tester) async {
    final controller = TextEditingController(text: 'already typed');
    await openForm(tester, controller: controller, isSaving: true);

    await pressBack(tester);

    // Popping here would orphan the request and leave the user unsure whether
    // the record was created.
    expect(find.text('Discard changes?'), findsNothing);
    expect(find.text('the list'), findsNothing);
  });
}
