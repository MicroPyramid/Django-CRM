import 'dart:async';

import 'package:bottle_crm/data/models/account.dart';
import 'package:bottle_crm/data/models/account_statement.dart';
import 'package:bottle_crm/providers/account_statement_provider.dart';
import 'package:bottle_crm/providers/accounts_provider.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/duplicates_provider.dart';
import 'package:bottle_crm/screens/accounts/account_detail_screen.dart';
import 'package:bottle_crm/screens/accounts/account_statement_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// The account statement screen (#810) at a 390px phone, and the account
/// screen's way into it, which only admins are offered.
const _usd = StatementSection(
  currency: 'USD',
  openingBalance: 60,
  invoiced: 250,
  paid: 100,
  cancelled: 0,
  closingBalance: 210,
  entries: [
    StatementEntry(
      date: '2026-10-05',
      kind: 'invoice',
      invoiceId: 'inv-1',
      invoiceNumber: 'INV-20261005-0001',
      description: 'Website rebuild, phase two of the migration',
      amount: 250,
      balance: 310,
    ),
    StatementEntry(
      date: '2026-10-20',
      kind: 'payment',
      invoiceId: 'inv-1',
      invoiceNumber: 'INV-20261005-0001',
      description: 'Payment (Bank Transfer, ref TX-4471-ACME-OCTOBER)',
      amount: -100,
      balance: 210,
    ),
  ],
);

const _eur = StatementSection(
  currency: 'EUR',
  openingBalance: 0,
  invoiced: 0,
  paid: 40,
  cancelled: 0,
  closingBalance: -40,
  entries: [
    StatementEntry(
      date: '2026-10-08',
      kind: 'payment',
      invoiceId: 'inv-2',
      invoiceNumber: 'INV-20260902-0004',
      description: 'Payment (Cash)',
      amount: -40,
      balance: -40,
    ),
  ],
);

const _october = AccountStatement(
  accountId: 'a1',
  accountName: 'Northwind Traders and Distribution',
  startDate: '2026-10-01',
  endDate: '2026-10-31',
  sections: [_eur, _usd],
);

void _usePhone(WidgetTester tester, double textScale) {
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  tester.platformDispatcher.textScaleFactorTestValue = textScale;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
}

class _NoDuplicates extends DuplicatesApi {
  @override
  Future<RecordDuplicates> forRecord(DuplicateModule module, String id) async =>
      const RecordDuplicates();
}

class _Accounts extends AccountsNotifier {
  @override
  Future<AccountsListData> build() async => const AccountsListData();
  @override
  Future<Account?> getAccount(String id, {void Function()? onNotFound}) async =>
      Account.fromJson({'id': id, 'name': 'Northwind'}, canDelete: false);
}

void main() {
  /// Every period the screen asked for, in order.
  late List<StatementRequest> asked;

  Future<void> pump(
    WidgetTester tester,
    FutureOr<AccountStatement> Function(StatementRequest) answer, {
    double textScale = 1.0,
  }) async {
    asked = [];
    _usePhone(tester, textScale);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          accountStatementProvider.overrideWith((ref, request) async {
            asked.add(request);
            return answer(request);
          }),
        ],
        child: const MaterialApp(home: AccountStatementScreen(accountId: 'a1')),
      ),
    );
    await tester.pumpAndSettle();
  }

  for (final scale in [1.0, 1.3]) {
    testWidgets('lays out each currency at a phone width, text scale $scale', (
      tester,
    ) async {
      await pump(tester, (_) => _october, textScale: scale);
      expect(tester.takeException(), isNull);

      // First load asks for the server's default period.
      expect(asked.first, (accountId: 'a1', start: null, end: null));
      expect(find.text('1 Oct 2026 to 31 Oct 2026'), findsOneWidget);
      expect(find.byTooltip('Save PDF'), findsOneWidget);
      expect(find.text('In EUR'), findsOneWidget);
      // A credit balance is said in words, not as a negative amount due.
      expect(find.text('In credit'), findsOneWidget);
      expect(find.text('€40.00'), findsWidgets);

      // The list builds what is on screen; scroll to the USD half.
      Future<void> reach(Finder finder) => tester.scrollUntilVisible(
        finder,
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await reach(find.text('In USD'));
      await reach(find.text('Balance due'));
      // A payment takes money off: the sign goes before the symbol.
      await reach(find.text('-\$100.00'));
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('a member is told it is for admins, with no retry', (
    tester,
  ) async {
    await pump(
      tester,
      (_) => throw const StatementRefusal(
        403,
        'Only an administrator can view account statements.',
      ),
    );
    expect(find.text('Statements are for administrators'), findsOneWidget);
    expect(find.text('Retry'), findsNothing);
    expect(find.byTooltip('Save PDF'), findsNothing);
  });

  testWidgets('a refused period says why and keeps the period controls', (
    tester,
  ) async {
    await pump(
      tester,
      (request) => request.start == null
          ? _october
          : throw const StatementRefusal(
              400,
              'End date: A statement can cover at most 366 days.',
            ),
    );
    await tester.tap(find.text('Previous month'));
    await tester.pumpAndSettle();

    expect(find.textContaining('at most 366 days'), findsOneWidget);
    expect(find.text('Change period'), findsOneWidget);
    expect(find.text('This month'), findsOneWidget);
  });

  testWidgets('Previous month asks for the month before the one shown', (
    tester,
  ) async {
    await pump(tester, (_) => _october);
    await tester.tap(find.text('Previous month'));
    await tester.pumpAndSettle();
    expect(asked.last, (
      accountId: 'a1',
      start: '2026-09-01',
      end: '2026-09-30',
    ));

    await tester.tap(find.text('This month'));
    await tester.pumpAndSettle();
    expect(asked.last, (accountId: 'a1', start: null, end: null));
  });

  testWidgets('an empty period says so', (tester) async {
    await pump(
      tester,
      (_) => const AccountStatement(
        accountId: 'a1',
        accountName: 'Northwind',
        startDate: '2026-10-01',
        endDate: '2026-10-31',
        sections: [],
      ),
    );
    expect(
      find.text(
        'Nothing was billed or paid in this period, and nothing is owed.',
      ),
      findsOneWidget,
    );
  });

  for (final admin in [true, false]) {
    testWidgets('the account screen offers a statement: admin=$admin', (
      tester,
    ) async {
      _usePhone(tester, 1.3);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            accountsProvider.overrideWith(_Accounts.new),
            duplicatesApiProvider.overrideWithValue(_NoDuplicates()),
            isOrgAdminProvider.overrideWithValue(admin),
          ],
          child: const MaterialApp(home: AccountDetailScreen(accountId: 'a1')),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(
        find.byTooltip('Statement'),
        admin ? findsOneWidget : findsNothing,
      );
    });
  }
}
