import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/models.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/tasks_provider.dart';
import 'package:bottle_crm/screens/tasks/tasks_list_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Both tests here cover the same real session: a member whose only two tasks
/// were completed. The API returned both, and the screen said "All caught up!
/// No pending tasks", because the gate that decides whether to render any
/// group at all counted four of the five groups.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('TasksListScreen', () {
    testWidgets('renders completed tasks when they are all the user has', (
      tester,
    ) async {
      final notifier = _FakeTasksNotifier(
        TasksListData(
          tasks: [_task(id: 'task-done', title: 'Finished work')],
          totalCount: 1,
          hasMore: false,
        ),
      );

      await tester.pumpWidget(_testApp(notifier));
      await tester.pumpAndSettle();

      expect(find.text('All caught up!'), findsNothing);
      expect(find.text('Completed'), findsOneWidget);
      expect(find.text('Finished work'), findsOneWidget);
    });

    testWidgets('still shows the empty state when there are no tasks at all', (
      tester,
    ) async {
      final notifier = _FakeTasksNotifier(const TasksListData(hasMore: false));

      await tester.pumpWidget(_testApp(notifier));
      await tester.pumpAndSettle();

      expect(find.text('All caught up!'), findsOneWidget);
    });

    testWidgets('a completed task builds its row without tripping the '
        'Dismissible assertion', (tester) async {
      // TaskRow used to pass a secondaryBackground with a null background for
      // any task it could not offer "complete" on, which Flutter asserts
      // against. The list view never rendered such a row because of the gate
      // above, so the two defects hid each other.
      final notifier = _FakeTasksNotifier(
        TasksListData(
          tasks: [_task(id: 'task-done', title: 'Finished work')],
          totalCount: 1,
          hasMore: false,
        ),
      );

      await tester.pumpWidget(_testApp(notifier));
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      expect(find.byType(Dismissible), findsOneWidget);
    });
  });
}

Widget _testApp(_FakeTasksNotifier notifier) {
  return ProviderScope(
    overrides: [
      authProvider.overrideWith(() => _FakeAuthNotifier()),
      tasksProvider.overrideWith(() => notifier),
    ],
    child: MaterialApp(theme: AppTheme.light, home: const TasksListScreen()),
  );
}

Task _task({required String id, required String title}) {
  return Task(
    id: id,
    title: title,
    status: TaskStatus.completed,
    priority: Priority.low,
    dueDate: DateTime(2026, 5, 15),
    createdAt: DateTime(2026, 5, 1),
  );
}

class _FakeTasksNotifier extends TasksNotifier {
  _FakeTasksNotifier(this.initialData);

  final TasksListData initialData;

  @override
  Future<TasksListData> build() async => initialData;

  @override
  Future<void> refresh() async {}

  @override
  Future<void> loadMore() async {}
}

class _FakeAuthNotifier extends AuthNotifier {
  @override
  AuthState build() {
    const org = Organization(
      id: 'org-1',
      name: 'Test Org',
      role: 'USER',
      currencySymbol: r'$',
    );

    return AuthState(
      user: const AuthUser(id: 'user-1', email: 'member@example.com'),
      organizations: [org],
      selectedOrganization: org,
      isAuthenticated: true,
    );
  }
}
