import 'package:bottle_crm/data/models/app_notification.dart';
import 'package:bottle_crm/data/models/invoice.dart';
import 'package:bottle_crm/data/models/time_entry.dart';
import 'package:bottle_crm/data/models/timesheet.dart';
import 'package:bottle_crm/data/models/estimate.dart';
import 'package:bottle_crm/data/models/product.dart';
import 'package:bottle_crm/data/models/recurring_invoice.dart';
import 'package:bottle_crm/providers/invoice_extras_provider.dart';
import 'package:bottle_crm/providers/invoices_provider.dart';
import 'package:bottle_crm/providers/notifications_provider.dart';
import 'package:bottle_crm/providers/timesheet_provider.dart';
import 'package:bottle_crm/screens/invoices/estimates_list_screen.dart';
import 'package:bottle_crm/screens/invoices/invoices_list_screen.dart';
import 'package:bottle_crm/screens/invoices/new_invoice_screen.dart';
import 'package:bottle_crm/screens/invoices/new_recurring_screen.dart';
import 'package:bottle_crm/screens/invoices/products_list_screen.dart';
import 'package:bottle_crm/screens/invoices/recurring_list_screen.dart';
import 'package:bottle_crm/screens/notifications/notifications_screen.dart';
import 'package:bottle_crm/screens/timesheet/timesheet_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// The newest screens, rendered at a real phone.
///
/// The workspace rule is that a screen is not done until it holds up at 390px,
/// and that this is verified by rendering rather than by reading the layout
/// code. The default test surface is 800x600, which is wider than any phone
/// and therefore proves nothing about one: a Row that overflows at 390 fits
/// comfortably at 800 and the test stays green.
///
/// Flutter reports an overflow as a thrown FlutterError, so
/// `tester.takeException()` returning null is the assertion. It is checked at
/// two text scales, because a phone with large text is where a Row that only
/// just fits stops fitting.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  /// An iPhone 15-ish logical viewport, the narrow end of what ships today.
  void usePhone(WidgetTester tester, {double textScale = 1.0}) {
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    tester.platformDispatcher.textScaleFactorTestValue = textScale;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  }

  /// The screen under a router that can answer a ticket push, so tapping a
  /// row lands somewhere assertable instead of throwing.
  Widget routed(Widget screen) => MaterialApp.router(
    routerConfig: GoRouter(
      initialLocation: '/here',
      routes: [
        GoRoute(path: '/here', builder: (_, _) => screen),
        GoRoute(
          path: '/tickets/:id',
          builder: (_, s) => Text('ticket ${s.pathParameters['id']}'),
        ),
      ],
    ),
  );

  Widget timesheetApp() => ProviderScope(
    overrides: [timesheetProvider.overrideWith(_FakeTimesheet.new)],
    child: routed(const TimesheetScreen()),
  );

  Widget notificationsApp() => ProviderScope(
    overrides: [notificationsProvider.overrideWith(_FakeNotifications.new)],
    child: routed(const NotificationsScreen()),
  );

  Widget invoicesApp({bool mixedCurrency = false}) => ProviderScope(
    overrides: [
      invoicesProvider.overrideWith(
        mixedCurrency ? _FakeMixedInvoices.new : _FakeInvoices.new,
      ),
    ],
    child: routed(const InvoicesListScreen()),
  );

  Widget estimatesApp() => ProviderScope(
    overrides: [estimatesProvider.overrideWith(_FakeEstimates.new)],
    child: routed(const EstimatesListScreen()),
  );

  Widget recurringApp() => ProviderScope(
    overrides: [recurringProvider.overrideWith(_FakeRecurring.new)],
    child: routed(const RecurringListScreen()),
  );

  /// The form with the pickers stubbed empty. It still has to lay out: an
  /// org with no accounts yet is a real state, and it is the one a new user
  /// hits first.
  Widget newInvoiceApp() => ProviderScope(
    overrides: [productsProvider.overrideWith(_FakeProducts.new)],
    child: routed(const NewInvoiceScreen()),
  );

  Widget newRecurringApp() => ProviderScope(
    overrides: [productsProvider.overrideWith(_FakeProducts.new)],
    child: routed(const NewRecurringScreen()),
  );

  Widget productsApp() => ProviderScope(
    overrides: [productsProvider.overrideWith(_FakeProducts.new)],
    child: routed(const ProductsListScreen()),
  );

  Future<void> pump(
    WidgetTester tester,
    Widget app, {
    double textScale = 1.0,
  }) async {
    usePhone(tester, textScale: textScale);
    await tester.pumpWidget(app);
    await tester.pumpAndSettle();
  }

  group('timesheet at 390px', () {
    testWidgets('renders a week without overflowing', (tester) async {
      await pump(tester, timesheetApp());

      expect(tester.takeException(), isNull);
    });

    testWidgets('still fits with the system font scaled up', (tester) async {
      await pump(tester, timesheetApp(), textScale: 1.5);

      expect(tester.takeException(), isNull);
    });

    testWidgets('draws the day nothing was logged on', (tester) async {
      await pump(tester, timesheetApp());

      // The whole reason this screen exists. A week that renders only the days
      // with entries makes a gap and a quiet day look identical.
      expect(find.text('Nothing logged'), findsOneWidget);
      // findRichText, because the day header is spans: the weekday and the
      // date share one Text so the row can ellipsize as a unit.
      expect(
        find.textContaining('Wednesday', findRichText: true),
        findsOneWidget,
      );
    });

    testWidgets('offers Stop on the running timer, thumb-sized', (
      tester,
    ) async {
      await pump(tester, timesheetApp());

      final stop = find.widgetWithText(FilledButton, 'Stop timer');
      expect(stop, findsOneWidget);
      // The primary action on this screen, so it has to be reachable rather
      // than merely present.
      expect(tester.getSize(stop).height, greaterThanOrEqualTo(44));
    });

    testWidgets('week navigation has 44px targets', (tester) async {
      await pump(tester, timesheetApp());

      for (final tip in ['Previous week', 'Next week']) {
        final size = tester.getSize(find.byTooltip(tip));
        expect(size.width, greaterThanOrEqualTo(44), reason: tip);
        expect(size.height, greaterThanOrEqualTo(44), reason: tip);
      }
    });
  });

  group('notifications at 390px', () {
    testWidgets('renders the feed without overflowing', (tester) async {
      await pump(tester, notificationsApp());

      expect(tester.takeException(), isNull);
    });

    testWidgets('still fits with the system font scaled up', (tester) async {
      await pump(tester, notificationsApp(), textScale: 1.5);

      expect(tester.takeException(), isNull);
    });

    testWidgets('opens unread and switches to all', (tester) async {
      await pump(tester, notificationsApp());

      expect(find.textContaining('mentioned you on'), findsOneWidget);
      expect(find.textContaining('sla breached'), findsNothing);

      await tester.tap(find.text('All'));
      await tester.pumpAndSettle();

      // The read row, which the unread filter was hiding.
      expect(find.textContaining('sla breached'), findsOneWidget);
    });

    testWidgets('a row with a resolvable link opens its ticket', (
      tester,
    ) async {
      await pump(tester, notificationsApp());

      await tester.tap(find.textContaining('mentioned you on'));
      await tester.pumpAndSettle();

      expect(find.text('ticket case-9'), findsOneWidget);
    });
  });

  group('invoices at 390px', () {
    testWidgets('renders the list without overflowing', (tester) async {
      await pump(tester, invoicesApp());

      expect(tester.takeException(), isNull);
    });

    testWidgets('still fits with the system font scaled up', (tester) async {
      // Where the web's seven-column table would have given up. A long account
      // name beside an amount, and "Partially paid" beside "912d late", are
      // both wider than they look at the default 800px test surface.
      await pump(tester, invoicesApp(), textScale: 1.5);

      expect(tester.takeException(), isNull);
    });

    testWidgets('offers Send only on the invoices the API would accept', (
      tester,
    ) async {
      await pump(tester, invoicesApp());

      // Draft gets Send, Overdue gets the reminder wording, and the paid one
      // gets neither: the API answers 400 on a paid invoice.
      expect(find.widgetWithText(OutlinedButton, 'Send'), findsOneWidget);
      expect(
        find.widgetWithText(OutlinedButton, 'Send a reminder'),
        findsOneWidget,
      );
      expect(find.byType(OutlinedButton), findsNWidgets(2));
    });

    testWidgets('the send button is thumb-sized', (tester) async {
      await pump(tester, invoicesApp());

      final send = find.widgetWithText(OutlinedButton, 'Send');
      expect(tester.getSize(send).height, greaterThanOrEqualTo(40));
    });

    testWidgets('a paid invoice shows no age, however old its due date', (
      tester,
    ) async {
      await pump(tester, invoicesApp());

      // INV-0003 is Paid with a due date in 2020. "d late" against it would be
      // wrong, and v1 printed exactly that.
      expect(find.textContaining('d late'), findsOneWidget);
    });

    testWidgets('one currency puts a symbol on the header figures', (
      tester,
    ) async {
      await pump(tester, invoicesApp());

      expect(find.textContaining('\$'), findsWidgets);
      expect(find.textContaining('more than one currency'), findsNothing);
    });

    testWidgets('two currencies drop the symbol and say why', (tester) async {
      await pump(tester, invoicesApp(mixedCurrency: true));

      // The server added USD to EUR. Stamping either symbol on the result
      // would make a wrong number look authoritative.
      expect(find.textContaining('more than one currency'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  });

  group('the sibling invoice pages at 390px', () {
    testWidgets('estimates render without overflowing', (tester) async {
      await pump(tester, estimatesApp());
      expect(tester.takeException(), isNull);
    });

    testWidgets('estimates fit with the system font scaled up', (tester) async {
      await pump(tester, estimatesApp(), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('a converted estimate offers the invoice, not a conversion', (
      tester,
    ) async {
      await pump(tester, estimatesApp());

      // One unconverted row offers it; the converted row offers the invoice.
      expect(
        find.widgetWithText(FilledButton, 'Raise an invoice'),
        findsOneWidget,
      );
      expect(
        find.widgetWithText(OutlinedButton, 'Open the invoice'),
        findsOneWidget,
      );
      expect(find.textContaining('billed INV-0009'), findsOneWidget);
    });

    testWidgets('recurring renders without overflowing', (tester) async {
      await pump(tester, recurringApp());
      expect(tester.takeException(), isNull);
    });

    testWidgets('recurring fits with the system font scaled up', (
      tester,
    ) async {
      await pump(tester, recurringApp(), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('a paused schedule shows no next run date', (tester) async {
      await pump(tester, recurringApp());

      // The running one does; the paused one keeps the date on its row but
      // must not print it, or it promises an invoice that is not coming.
      expect(find.textContaining('next '), findsOneWidget);
      expect(find.text('Pause'), findsOneWidget);
      expect(find.text('Resume'), findsOneWidget);
    });

    testWidgets('a custom cadence shows its interval', (tester) async {
      await pump(tester, recurringApp());
      expect(find.text('Every 10 days'), findsOneWidget);
    });

    testWidgets('products render without overflowing', (tester) async {
      await pump(tester, productsApp());
      expect(tester.takeException(), isNull);
    });

    testWidgets('products fit with the system font scaled up', (tester) async {
      await pump(tester, productsApp(), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('a non-admin sees no product write buttons', (tester) async {
      // isOrgAdminProvider is false with no signed-in profile, which is the
      // state this test runs in. The server refuses these writes with a 403,
      // so offering them would be offering a guaranteed failure.
      await pump(tester, productsApp());

      expect(find.widgetWithText(OutlinedButton, 'Edit'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Delete'), findsNothing);
      expect(find.byTooltip('New product'), findsNothing);
    });

    testWidgets('a retired product still shows what it was billed on', (
      tester,
    ) async {
      await pump(tester, productsApp());

      expect(find.text('Retired'), findsOneWidget);
      expect(find.textContaining('on 12 invoices'), findsOneWidget);
    });
  });

  group('the new invoice form at 390px', () {
    testWidgets('renders without overflowing', (tester) async {
      await pump(tester, newInvoiceApp());
      expect(tester.takeException(), isNull);
    });

    testWidgets('fits with the system font scaled up', (tester) async {
      // The densest form in the app: two dropdowns, a date field beside a
      // terms dropdown, and a pinned total bar with a button on it.
      await pump(tester, newInvoiceApp(), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('will not submit until it has what the API requires', (
      tester,
    ) async {
      await pump(tester, newInvoiceApp());

      // account_id, contact_id, invoice_title and at least one line are all
      // required; nothing has been filled, so the button must be inert.
      final button = tester.widget<FilledButton>(
        find.widgetWithText(FilledButton, 'Create draft'),
      );
      expect(button.onPressed, isNull);
    });

    testWidgets('the contact picker waits for an account', (tester) async {
      await pump(tester, newInvoiceApp());

      // Pairing a contact with the wrong account is a 400, so the form asks
      // for the account that narrows the list first.
      expect(find.text('Pick an account first'), findsOneWidget);
    });

    testWidgets('says the running total excludes tax and discount', (
      tester,
    ) async {
      await pump(tester, newInvoiceApp());

      // Tax, discount and shipping are applied server-side and are not on
      // this form, so calling the figure "Total" would overstate it.
      expect(find.text('before any tax or discount'), findsOneWidget);
    });

    testWidgets('the create button is thumb-sized', (tester) async {
      await pump(tester, newInvoiceApp());

      final size = tester.getSize(
        find.widgetWithText(FilledButton, 'Create draft'),
      );
      expect(size.height, greaterThanOrEqualTo(44));
    });
  });

  group('the new schedule form at 390px', () {
    testWidgets('renders without overflowing', (tester) async {
      await pump(tester, newRecurringApp());
      expect(tester.takeException(), isNull);
    });

    testWidgets('fits with the system font scaled up', (tester) async {
      await pump(tester, newRecurringApp(), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('asks for the interval only on a custom cadence', (
      tester,
    ) async {
      await pump(tester, newRecurringApp());

      // Monthly by default, so the field is absent.
      expect(find.text('Every how many days'), findsNothing);

      await tester.tap(find.text('Monthly').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Custom').last);
      await tester.pumpAndSettle();

      expect(find.text('Every how many days'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('a bad interval is called out on the field itself', (
      tester,
    ) async {
      // The submit button proves nothing here: it is disabled anyway while the
      // account, contact, title and lines are empty, so asserting on it would
      // pass with the cadence rule deleted. `cadenceIsComplete` is unit-tested
      // instead; this covers the message the user actually sees.
      await pump(tester, newRecurringApp());

      await tester.tap(find.text('Monthly').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Custom').last);
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).last, '0');
      await tester.pumpAndSettle();

      expect(find.text('Enter a number of days, at least 1'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('says how often the amount recurs, not just the amount', (
      tester,
    ) async {
      await pump(tester, newRecurringApp());

      // A figure with no cadence beside it is the one number this screen
      // must never show: it reads as a one-off total.
      expect(find.textContaining('monthly, before tax'), findsOneWidget);
    });
  });
}

/// One estimate still to convert, one already billed.
class _FakeEstimates extends EstimatesNotifier {
  @override
  Future<List<Estimate>> build() async => [
    Estimate.fromJson({
      'id': 'e1',
      'estimate_number': 'EST-0001',
      'title': 'Warehouse rebuild',
      'status': 'Accepted',
      'account_name': 'Northwind Traders and Logistics Incorporated',
      'total_amount': '52000.00',
      'currency': 'USD',
      'expiry_date': '2026-09-30',
    }),
    Estimate.fromJson({
      'id': 'e2',
      'estimate_number': 'EST-0002',
      'title': 'Support',
      'status': 'Accepted',
      'account_name': 'Initech',
      'total_amount': '1000.00',
      'currency': 'USD',
      'converted_to_invoice': {'id': 'inv-9', 'invoice_number': 'INV-0009'},
    }),
  ];
}

/// One running monthly schedule and one paused custom one. Both carry a next
/// generation date; only the running one may show it.
class _FakeRecurring extends RecurringNotifier {
  @override
  Future<List<RecurringInvoice>> build() async => [
    RecurringInvoice.fromJson({
      'id': 'r1',
      'title': 'Managed hosting retainer',
      'account_name': 'Northwind Traders and Logistics Incorporated',
      'frequency': 'MONTHLY',
      'is_active': true,
      'auto_send': true,
      'next_generation_date': '2026-09-01',
      'total_amount': '1200.00',
      'currency': 'USD',
      'invoices_generated': 14,
    }),
    RecurringInvoice.fromJson({
      'id': 'r2',
      'title': 'Onsite visits',
      'account_name': 'Initech',
      'frequency': 'CUSTOM',
      'custom_days': 10,
      'is_active': false,
      'next_generation_date': '2026-08-20',
      'total_amount': '400.00',
      'currency': 'USD',
    }),
  ];
}

/// One live product and one retired that has been billed.
class _FakeProducts extends ProductsNotifier {
  @override
  Future<List<Product>> build() async => [
    Product.fromJson({
      'id': 'p1',
      'name': 'Managed hosting, standard tier with onsite support',
      'sku': 'MH-STD-001',
      'category': 'Hosting',
      'price': '1200.00',
      'currency': 'USD',
      'is_active': true,
      'used_on': 3,
    }),
    Product.fromJson({
      'id': 'p2',
      'name': 'Legacy plan',
      'sku': 'LEG-001',
      'price': '99.00',
      'currency': 'USD',
      'is_active': false,
      'used_on': 12,
    }),
  ];
}

/// Monday has one stopped entry, Tuesday a running one, Wednesday nothing.
class _FakeTimesheet extends TimesheetNotifier {
  @override
  Future<TimesheetWeek> build() async => TimesheetWeek(
    start: DateTime(2026, 8, 3),
    end: DateTime(2026, 8, 9),
    profileName: 'Ada',
    runningCount: 1,
    days: [
      TimesheetDay(
        date: DateTime(2026, 8, 3),
        entries: [
          TimeEntry(
            id: 'e1',
            caseId: 'case-9',
            caseName: 'Printer on fire in the third floor copy room',
            profileId: 'p1',
            startedAt: DateTime(2026, 8, 3, 9),
            endedAt: DateTime(2026, 8, 3, 11),
            durationMinutes: 120,
            billable: true,
            description: 'Diagnosis and a replacement fuser',
            invoiceId: 'inv-2',
            invoiceNumber: 'INV-0002',
          ),
        ],
      ),
      TimesheetDay(
        date: DateTime(2026, 8, 4),
        entries: [
          TimeEntry(
            id: 'e2',
            caseId: 'case-9',
            caseName: 'Printer on fire',
            profileId: 'p1',
            startedAt: DateTime(2026, 8, 4, 8, 48),
            billable: true,
            liveDurationMinutes: 12,
          ),
        ],
      ),
      TimesheetDay(date: DateTime(2026, 8, 5)),
    ],
  );
}

Invoice _row({
  required String id,
  required String number,
  required String status,
  required String account,
  required String total,
  required String due,
  String currency = 'USD',
  String amountDue = '0.00',
}) {
  return Invoice.fromJson({
    'id': id,
    'invoice_number': number,
    'invoice_title': 'Retainer',
    'status': status,
    'account': 'acc-$id',
    'account_name': account,
    'total_amount': total,
    'amount_due': amountDue,
    'due_date': due,
    'currency': currency,
    'line_items_count': 2,
  });
}

/// A draft, a long-overdue invoice, and one settled years ago.
class _FakeInvoices extends InvoicesNotifier {
  @override
  Future<InvoicesListData> build() async => InvoicesListData(
    totals: const InvoiceTotals(
      count: 3,
      outstanding: 12500,
      overdue: 1250,
      draft: 400,
      actionNeeded: 2,
    ),
    invoices: [
      _row(
        id: '1',
        number: 'INV-0001',
        status: 'Overdue',
        // Long on purpose: the name and the amount share one row.
        account: 'Northwind Traders and Logistics Incorporated',
        total: '1250.00',
        amountDue: '1250.00',
        due: '2024-01-15',
      ),
      _row(
        id: '2',
        number: 'INV-0002',
        status: 'Draft',
        account: 'Initech',
        total: '400.00',
        amountDue: '400.00',
        due: '2026-09-30',
      ),
      _row(
        id: '3',
        number: 'INV-0003',
        status: 'Paid',
        account: 'Umbrella',
        total: '900.00',
        due: '2020-03-01',
      ),
    ],
  );
}

/// The same list billed in two currencies, which makes the server's sums a
/// total of unlike things.
class _FakeMixedInvoices extends InvoicesNotifier {
  @override
  Future<InvoicesListData> build() async => InvoicesListData(
    totals: const InvoiceTotals(count: 2, outstanding: 200),
    invoices: [
      _row(
        id: '1',
        number: 'INV-0001',
        status: 'Sent',
        account: 'Northwind',
        total: '100.00',
        amountDue: '100.00',
        due: '2026-09-01',
      ),
      _row(
        id: '2',
        number: 'INV-0002',
        status: 'Sent',
        account: 'Initech',
        total: '100.00',
        amountDue: '100.00',
        due: '2026-09-01',
        currency: 'EUR',
      ),
    ],
  );
}

class _FakeNotifications extends NotificationsNotifier {
  @override
  Future<NotificationFeed> build() async => NotificationFeed(
    unreadCount: 1,
    total: 2,
    items: [
      AppNotification(
        id: 'n1',
        verb: 'case.mentioned',
        actorName: 'Ada Lovelace',
        entityName: 'Printer on fire',
        commentExcerpt: 'can you take a look at this before Friday?',
        link: '/tickets/case-9',
        createdAt: DateTime.now().subtract(const Duration(minutes: 20)),
      ),
      AppNotification(
        id: 'n2',
        verb: 'case.sla_breached',
        actorName: 'Grace',
        entityName: 'Handled',
        link: '/tickets/case-1',
        readAt: DateTime.now().subtract(const Duration(days: 1)),
        createdAt: DateTime.now().subtract(const Duration(days: 2)),
      ),
    ],
  );
}
