import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/screens/settings/modules_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../support/modules_fixtures.dart';

/// The Modules screen at an 11-inch tablet in portrait, with the system font
/// at 1.3: the other direction from the phone checks.
void main() {
  Future<void> pumpTablet(WidgetTester tester, {bool refuse = false}) async {
    tester.view.devicePixelRatio = 2.0;
    tester.view.physicalSize = const Size(834 * 2, 1112 * 2);
    tester.platformDispatcher.textScaleFactorTestValue = 1.3;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.pumpWidget(
      ProviderScope(
        key: UniqueKey(),
        overrides: modulesOverrides(
          FakeOrgModules(
            () async => modulesAnswer(
              off: ['tasks', 'documents'],
              labels: {'deals': 'Opportunities, quotes and renewals pipes'},
            ),
            refusals: refuse
                ? [
                    'Tickets still receives submissions from 2 published web '
                        'forms. Unpublish them first.',
                    'Tickets still has a mailbox. Switch it off first.',
                    'Leads still receives submissions from 1 web form.',
                  ]
                : const [],
          ),
        ),
        child: MaterialApp(theme: AppTheme.light, home: const ModulesScreen()),
      ),
    );
    await tester.pumpAndSettle();
  }

  void expectThumbSized(WidgetTester tester, Finder target) {
    for (final element in target.evaluate()) {
      final size = tester.getSize(find.byElementPredicate((e) => e == element));
      expect(size.width, greaterThanOrEqualTo(44), reason: '$target');
      expect(size.height, greaterThanOrEqualTo(44), reason: '$target');
    }
  }

  Future<void> dragThrough(WidgetTester tester) async {
    for (var i = 0; i < 8; i++) {
      await tester.drag(find.byType(Scrollable).first, const Offset(0, -500));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    }
  }

  testWidgets('every control is at least 44 by 44', (tester) async {
    await pumpTablet(tester);
    expect(tester.takeException(), isNull);
    expect(find.text('Opportunities, quotes and renewals pipes'), findsWidgets);
    expectThumbSized(tester, find.byType(Switch));
    expectThumbSized(tester, find.byTooltip('Move up'));
    expectThumbSized(tester, find.byTooltip('Move down'));
    await dragThrough(tester);
    expectThumbSized(tester, find.byType(Switch));
  });

  testWidgets('three refusal messages and their links fit', (tester) async {
    await pumpTablet(tester, refuse: true);
    await tester.tap(find.byType(Switch).at(1));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Switch off').last);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.textContaining('mailbox'), findsOneWidget);
    expectThumbSized(tester, find.widgetWithText(OutlinedButton, 'Web forms'));
    await dragThrough(tester);
  });
}
