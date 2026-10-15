import 'dart:convert';

import 'package:bottle_crm/data/models/account_statement.dart';
import 'package:bottle_crm/providers/account_statement_provider.dart';
import 'package:bottle_crm/screens/invoices/invoice_format.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// Account statements (#810): what the phone reads from
/// `GET /api/invoices/statements/<account>/`, and how it asks for it.
const _account = '11111111-2222-3333-4444-555555555555';

Map<String, dynamic> statementJson() => {
  'account': {'id': _account, 'name': 'Acme'},
  'start_date': '2026-10-01',
  'end_date': '2026-10-31',
  'currencies': [
    {
      'currency': 'USD',
      'opening_balance': '60.00',
      'invoiced': '250.00',
      'paid': '100.00',
      'cancelled': '0.00',
      'closing_balance': '210.00',
      'entries': [
        {
          'date': '2026-10-05',
          'kind': 'invoice',
          'invoice_id': 'inv-1',
          'invoice_number': 'INV-1',
          'description': 'Build',
          'amount': '250.00',
          'balance': '310.00',
        },
        {
          'date': '2026-10-20',
          'kind': 'payment',
          'invoice_id': 'inv-1',
          'invoice_number': 'INV-1',
          'description': 'Payment (Bank Transfer)',
          'amount': '-100.00',
          'balance': '210.00',
        },
      ],
    },
  ],
};

/// A JWT that decodes but is not signed, so `ApiService` sends it as is.
String _token() {
  String seg(Map<String, dynamic> m) =>
      base64Url.encode(utf8.encode(jsonEncode(m))).replaceAll('=', '');
  final exp = DateTime.now().add(const Duration(hours: 1));
  return '${seg({'alg': 'HS256'})}.'
      '${seg({'exp': exp.millisecondsSinceEpoch ~/ 1000})}.sig';
}

void main() {
  group('AccountStatement.fromJson', () {
    test('reads each currency, its balances and its entries in order', () {
      final statement = AccountStatement.fromJson(statementJson());

      expect(statement.accountName, 'Acme');
      expect(
        (statement.startDate, statement.endDate),
        ('2026-10-01', '2026-10-31'),
      );
      final usd = statement.sections.single;
      expect(usd.currency, 'USD');
      expect(
        (usd.openingBalance, usd.invoiced, usd.paid, usd.closingBalance),
        (60.0, 250.0, 100.0, 210.0),
      );
      expect(
        [for (final e in usd.entries) (e.kind, e.amount, e.balance)],
        [('invoice', 250.0, 310.0), ('payment', -100.0, 210.0)],
      );
      expect(usd.entries.first.invoiceId, 'inv-1');
      expect(usd.entries.first.invoiceNumber, 'INV-1');
    });

    test('a period with nothing billed or owed has no sections', () {
      final statement = AccountStatement.fromJson({
        ...statementJson(),
        'currencies': <dynamic>[],
      });
      expect(statement.sections, isEmpty);
    });
  });

  group('previousMonth', () {
    test('is the whole calendar month before the one a date falls in', () {
      expect(previousMonth('2026-10-15'), (
        start: '2026-09-01',
        end: '2026-09-30',
      ));
    });

    test('crosses a year and knows a leap February', () {
      expect(previousMonth('2026-01-05'), (
        start: '2025-12-01',
        end: '2025-12-31',
      ));
      expect(previousMonth('2024-03-31'), (
        start: '2024-02-01',
        end: '2024-02-29',
      ));
    });
  });

  group('money', () {
    test('puts the sign before the symbol', () {
      expect(money(-100, '\$'), '-\$100.00');
      expect(money(250.5, '\$'), '\$250.50');
    });
  });

  group('accountStatementProvider', () {
    late List<Uri> asked;

    void answer(int status, Object body) {
      asked = [];
      ApiService().setAccessToken(_token());
      ApiService().setClientForTesting(
        MockClient((request) async {
          asked.add(request.url);
          return http.Response(jsonEncode(body), status);
        }),
      );
    }

    tearDown(() {
      ApiService().clearAuth();
      ApiService().setClientForTesting(http.Client());
    });

    Future<AccountStatement> read(StatementRequest request) {
      final container = ProviderContainer();
      addTearDown(container.dispose);
      // Listened to, as a screen would: an auto-dispose provider nobody
      // watches is disposed before a slow answer (a 403 retries) lands.
      container.listen(accountStatementProvider(request), (_, _) {});
      return container.read(accountStatementProvider(request).future);
    }

    test('asks for the account and the period', () async {
      answer(200, statementJson());
      final statement = await read((
        accountId: _account,
        start: '2026-10-01',
        end: '2026-10-31',
      ));
      expect(statement.sections.single.closingBalance, 210.0);
      expect(asked.single.path, '/api/invoices/statements/$_account/');
      expect(asked.single.queryParameters, {
        'start_date': '2026-10-01',
        'end_date': '2026-10-31',
      });
    });

    test(
      'sends no dates when none were picked, so the API default applies',
      () async {
        answer(200, statementJson());
        await read((accountId: _account, start: null, end: null));
        expect(asked.single.queryParameters, isEmpty);
      },
    );

    test('a member is told it is for admins', () async {
      answer(403, {
        'error': true,
        'message': 'Only an administrator can view account statements.',
      });
      await expectLater(
        read((accountId: _account, start: null, end: null)),
        throwsA(
          isA<StatementRefusal>()
              .having((e) => e.forbidden, 'forbidden', isTrue)
              .having(
                (e) => e.message,
                'message',
                'Only an administrator can view account statements.',
              ),
        ),
      );
    });

    test("a refused period carries the API's sentence", () async {
      answer(400, {
        'end_date': ['A statement can cover at most 366 days.'],
      });
      await expectLater(
        read((accountId: _account, start: '2026-01-01', end: '2027-06-01')),
        throwsA(
          isA<StatementRefusal>()
              .having((e) => e.forbidden, 'forbidden', isFalse)
              .having(
                (e) => e.message,
                'message',
                contains('A statement can cover at most 366 days.'),
              ),
        ),
      );
    });
  });
}
