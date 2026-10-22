import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/screens/settings/automation/automation_rule_screen.dart';
import 'package:bottle_crm/screens/settings/automation/automation_runs_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../../support/automation_fixtures.dart';

/// The rule editor and the run history at an 11-inch tablet in portrait,
/// with the system font at 1.3: the other direction from the phone checks.
void main() {
  Future<void> pumpTablet(WidgetTester tester, Widget screen) async {
    tester.view.devicePixelRatio = 2.0;
    tester.view.physicalSize = const Size(834 * 2, 1112 * 2);
    tester.platformDispatcher.textScaleFactorTestValue = 1.3;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.pumpWidget(
      ProviderScope(
        key: UniqueKey(),
        overrides: automationOverrides(),
        child: MaterialApp.router(
          theme: AppTheme.light,
          routerConfig: GoRouter(
            initialLocation: '/here',
            routes: [GoRoute(path: '/here', builder: (_, _) => screen)],
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> dragThrough(WidgetTester tester, Finder scrollable) async {
    for (var i = 0; i < 6; i++) {
      await tester.drag(scrollable, const Offset(0, -500));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    }
  }

  void expectThumbSized(WidgetTester tester, Finder target) {
    final size = tester.getSize(target);
    expect(size.width, greaterThanOrEqualTo(44), reason: '$target');
    expect(size.height, greaterThanOrEqualTo(44), reason: '$target');
  }

  testWidgets('a rule with three actions and a long name', (tester) async {
    await pumpTablet(tester, const AutomationRuleScreen(ruleId: autoRuleId));
    expect(tester.takeException(), isNull);
    expect(find.text(longRuleName), findsWidgets);
    expectThumbSized(tester, find.byTooltip('Remove condition 1'));
    await dragThrough(tester, find.byType(SingleChildScrollView).first);
    expect(find.textContaining('3. Assign in turn to'), findsOneWidget);
    expectThumbSized(tester, find.byTooltip('Move action 3 up'));
    expectThumbSized(tester, find.widgetWithText(FilledButton, 'Save'));
  });

  testWidgets('a new rule', (tester) async {
    await pumpTablet(tester, const AutomationRuleScreen());
    expect(tester.takeException(), isNull);
    await dragThrough(tester, find.byType(SingleChildScrollView).first);
    expect(find.text('Add at least one action.'), findsOneWidget);
  });

  testWidgets('the run history with every run opened', (tester) async {
    await pumpTablet(tester, const AutomationRunsScreen(ruleId: autoRuleId));
    expect(tester.takeException(), isNull);
    for (final status in ['Done', 'Failed']) {
      await tester.scrollUntilVisible(
        find.text(status),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.tap(find.text(status).first);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    }
    expect(find.text('Undone'), findsOneWidget);
    expect(find.text('Skipped'), findsWidgets);
    await dragThrough(tester, find.byType(Scrollable).first);
    expect(find.text('<b>Bold</b> [open](javascript:x)'), findsOneWidget);
    expectThumbSized(tester, find.widgetWithText(OutlinedButton, 'Older'));
  });
}
