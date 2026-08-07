import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/deals_provider.dart';
import 'package:bottle_crm/screens/deals/deals_list_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// The filter sheet puts a TextButton straight into a Row. Themed buttons
/// carry `minimumSize: Size(infinity, h)`, a Row does not bound its non-flex
/// children on the main axis, and the whole sheet then fails to lay out and
/// paints nothing.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('the deals filter sheet lays out', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith(() => _FakeAuth()),
          dealsProvider.overrideWith(() => _FakeDeals()),
        ],
        child: MaterialApp(
          theme: AppTheme.light,
          home: const DealsListScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Filters'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('Filter deals'), findsOneWidget);
    expect(find.text('Reset'), findsOneWidget);
  });
}

class _FakeDeals extends DealsNotifier {
  @override
  Future<DealsListData> build() async => const DealsListData(deals: []);
  @override
  Future<void> refresh({String? search, String? stage}) async {}
  @override
  Future<void> loadMore({String? search, String? stage}) async {}
}

class _FakeAuth extends AuthNotifier {
  @override
  AuthState build() {
    const org = Organization(
      id: 'org-1',
      name: 'Test Org',
      currencySymbol: r'$',
    );
    return AuthState(
      user: const AuthUser(id: 'user-1', email: 'user@example.com'),
      organizations: [org],
      selectedOrganization: org,
      isAuthenticated: true,
    );
  }
}
