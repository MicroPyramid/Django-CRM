// SalesPro CRM Widget Test

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mobile/main.dart';

void main() {
  testWidgets('SalesPro app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(
      const ProviderScope(
        child: SalesProApp(),
      ),
    );

    // Wait for splash screen animation
    await tester.pump(const Duration(seconds: 1));

    // Verify that the app starts
    expect(find.byType(SalesProApp), findsOneWidget);
  });
}
