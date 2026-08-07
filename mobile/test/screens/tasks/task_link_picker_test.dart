import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/lookup_models.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/screens/tasks/task_form_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// "Link to a lead" read the leads *list* provider, which holds one page of
/// whatever the leads screen last fetched under whatever filter it last
/// applied. Open a fresh app, create a task, tap Lead: nothing, under the
/// heading "Nothing to pick" and the advice "Open this section on the web or
/// create one first". The org had twenty leads.
///
/// The picker now reads a lookup of its own and, because it watches rather than
/// reads, can tell the three states apart.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Future<void> openLeadPicker(
    WidgetTester tester,
    AsyncValue<List<EntityLookup>> leads,
  ) async {
    final router = GoRouter(
      initialLocation: '/new',
      routes: [
        GoRoute(path: '/new', builder: (_, _) => const TaskFormScreen()),
      ],
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [leadEntityOptionsProvider.overrideWithValue(leads)],
        child: MaterialApp.router(theme: AppTheme.light, routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();

    // The Linked Record row sits below the fold on a test-sized screen.
    await tester.ensureVisible(find.text('Not linked'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Not linked'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Lead'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
  }

  testWidgets('a lookup still in flight shows loading, not an empty org', (
    tester,
  ) async {
    await openLeadPicker(tester, const AsyncValue.loading());

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.textContaining('No Leads yet'), findsNothing);
  });

  testWidgets('leads that loaded are offered by name', (tester) async {
    await openLeadPicker(
      tester,
      const AsyncValue.data([
        EntityLookup(id: 'l1', label: 'Jill Shaffer'),
        EntityLookup(id: 'l2', label: 'Cruz Group'),
      ]),
    );

    expect(find.text('Jill Shaffer'), findsOneWidget);
    expect(find.text('Cruz Group'), findsOneWidget);
  });

  testWidgets('picking one puts it on the form', (tester) async {
    await openLeadPicker(
      tester,
      const AsyncValue.data([EntityLookup(id: 'l1', label: 'Jill Shaffer')]),
    );

    await tester.tap(find.text('Jill Shaffer'));
    await tester.pumpAndSettle();

    expect(find.text('Lead: Jill Shaffer'), findsOneWidget);
  });

  testWidgets('an org with no leads is told that, and nothing else', (
    tester,
  ) async {
    await openLeadPicker(tester, const AsyncValue.data([]));

    expect(find.text('No leads yet'), findsOneWidget);
    // The old copy sent people to the web for a list that was simply not
    // fetched yet. An org with no leads has nothing to open there either.
    expect(find.textContaining('on the web'), findsNothing);
  });

  testWidgets('a failed lookup says so instead of claiming the org is empty', (
    tester,
  ) async {
    await openLeadPicker(
      tester,
      AsyncValue.error(Exception('offline'), StackTrace.empty),
    );

    expect(find.text('Could not load leads'), findsOneWidget);
    expect(find.text('No leads yet'), findsNothing);
  });
}
