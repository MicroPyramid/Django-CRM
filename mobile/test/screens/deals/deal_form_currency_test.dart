import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/screens/deals/deal_form_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// A new deal takes its currency from the org, and the org record the client
/// stores was arriving without one, so every deal an org booked defaulted to
/// dollars however it actually trades. The client half was already right; it
/// was reading a field no endpoint sent.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Widget host(String? orgCurrency) => ProviderScope(
    overrides: [authProvider.overrideWith(() => _FakeAuth(orgCurrency))],
    child: MaterialApp(theme: AppTheme.light, home: const DealFormScreen()),
  );

  testWidgets('a new deal opens in the currency the org trades in', (
    tester,
  ) async {
    await tester.pumpWidget(host('EUR'));
    await tester.pump();

    expect(find.text('EUR'), findsOneWidget);
    expect(find.text('€'), findsOneWidget);
  });

  testWidgets('an org that never set one still gets a usable default', (
    tester,
  ) async {
    await tester.pumpWidget(host(null));
    await tester.pump();

    expect(find.text('USD'), findsOneWidget);
  });
}

class _FakeAuth extends AuthNotifier {
  _FakeAuth(this.orgCurrency);

  final String? orgCurrency;

  @override
  AuthState build() {
    final org = Organization(
      id: 'org-1',
      name: 'Test Org',
      role: 'ADMIN',
      defaultCurrency: orgCurrency,
    );
    return AuthState(
      user: const AuthUser(id: 'user-1', email: 'user@example.com'),
      organizations: [org],
      selectedOrganization: org,
      isAuthenticated: true,
    );
  }
}
