import 'package:bottle_crm/screens/tasks/task_form_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Tapping a day in the task calendar and then "Add a task" used to open the
/// form with no date, so the user picked the day they had just tapped.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Widget host(DateTime? due) => ProviderScope(
    child: MaterialApp(home: TaskFormScreen(initialDueDate: due)),
  );

  testWidgets('a new task with no starting day still asks for one', (
    tester,
  ) async {
    await tester.pumpWidget(host(null));
    await tester.pumpAndSettle();

    expect(find.text('Add Due Date'), findsOneWidget);
  });

  testWidgets('a new task opens on the day it was started from', (
    tester,
  ) async {
    await tester.pumpWidget(host(DateTime(2026, 5, 11)));
    await tester.pumpAndSettle();

    expect(find.text('Due Date'), findsOneWidget);
    expect(find.text('May 11, 2026'), findsOneWidget);
  });
}
