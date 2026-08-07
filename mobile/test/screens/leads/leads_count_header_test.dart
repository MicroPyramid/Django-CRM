import 'dart:async';

import 'package:bottle_crm/providers/leads_provider.dart';
import 'package:bottle_crm/screens/leads/leads_list_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// The header stated a number before it had one. For the whole of a slow load,
/// and for the whole of a failed one, the screen read "0 leads" over a spinner,
/// which is indistinguishable from an org with no leads. It took a minute to
/// tell an offline phone from an empty list, and I misread it myself.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Future<void> pump(
    WidgetTester tester,
    LeadsNotifier Function() notifier,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [leadsProvider.overrideWith(notifier)],
        child: const MaterialApp(home: LeadsListScreen()),
      ),
    );
    await tester.pump();
  }

  testWidgets('while the first page is in flight it does not claim zero', (
    tester,
  ) async {
    await pump(tester, _StillLoading.new);

    expect(find.text('0 leads'), findsNothing);
    expect(find.text('Loading'), findsOneWidget);
  });

  testWidgets('once the page lands it states the real count', (tester) async {
    await pump(tester, () => _Loaded(7));
    await tester.pump();

    // The control. A header that always said "Loading" would pass the test
    // above and tell nobody anything.
    expect(find.text('7 leads'), findsOneWidget);
    expect(find.text('Loading'), findsNothing);
  });

  testWidgets('an org that really has none still says so', (tester) async {
    await pump(tester, () => _Loaded(0));
    await tester.pump();

    // "0 leads" is the right answer here, and the fix must not have made it
    // unreachable.
    expect(find.text('0 leads'), findsOneWidget);
  });
}

class _StillLoading extends LeadsNotifier {
  @override
  Future<LeadsListData> build() => Completer<LeadsListData>().future;
}

class _Loaded extends LeadsNotifier {
  _Loaded(this.total);

  final int total;

  @override
  Future<LeadsListData> build() async =>
      LeadsListData(totalCount: total, hasMore: false);
}
