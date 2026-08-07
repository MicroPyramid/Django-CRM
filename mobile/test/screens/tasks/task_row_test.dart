import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/models.dart';
import 'package:bottle_crm/widgets/cards/task_row.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// `Dismissible` asserts `secondaryBackground == null || background != null`,
/// because [background] is the fallback pane for both drag directions. A row
/// with no complete affordance used to supply only the secondary pane, which
/// threw for every completed task. The list view masked it by never rendering
/// such a row; the task calendar did not, and red-screened on any date holding
/// one.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Widget host(Task task) => MaterialApp(
    theme: AppTheme.light,
    home: Scaffold(
      body: TaskRow(task: task, onDelete: () {}, onToggle: () {}),
    ),
  );

  Task task({required TaskStatus status}) => Task(
    id: 'task-1',
    title: 'A task',
    status: status,
    priority: Priority.low,
    dueDate: DateTime(2026, 5, 15),
    createdAt: DateTime(2026, 5, 1),
  );

  testWidgets('a completed task renders', (tester) async {
    await tester.pumpWidget(host(task(status: TaskStatus.completed)));

    expect(tester.takeException(), isNull);
    expect(find.text('A task'), findsOneWidget);

    // One pane, and it must be the one Dismissible falls back to.
    final dismissible = tester.widget<Dismissible>(find.byType(Dismissible));
    expect(dismissible.background, isNotNull);
    expect(dismissible.secondaryBackground, isNull);
    expect(dismissible.direction, DismissDirection.endToStart);
  });

  testWidgets('an open task keeps both swipe panes', (tester) async {
    await tester.pumpWidget(host(task(status: TaskStatus.inProgress)));

    expect(tester.takeException(), isNull);

    final dismissible = tester.widget<Dismissible>(find.byType(Dismissible));
    expect(dismissible.background, isNotNull);
    expect(dismissible.secondaryBackground, isNotNull);
    expect(dismissible.direction, DismissDirection.horizontal);
  });
}
