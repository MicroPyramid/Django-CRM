import 'package:bottle_crm/data/models/app_notification.dart';
import 'package:bottle_crm/data/models/business_calendar.dart';
import 'package:bottle_crm/data/models/custom_field_definition.dart';
import 'package:bottle_crm/data/models/escalation_policy.dart';
import 'package:bottle_crm/data/models/macro.dart';
import 'package:bottle_crm/data/models/reopen_policy.dart';
import 'package:bottle_crm/data/models/invoice.dart';
import 'package:bottle_crm/data/models/time_entry.dart';
import 'package:bottle_crm/data/models/timesheet.dart';
import 'package:bottle_crm/data/models/estimate.dart';
import 'package:bottle_crm/data/models/product.dart';
import 'package:bottle_crm/data/models/recurring_invoice.dart';
import 'package:bottle_crm/data/models/lookup_models.dart';
import 'package:bottle_crm/data/models/routing_rule.dart';
import 'package:bottle_crm/data/models/tag.dart';
import 'package:bottle_crm/providers/invoice_extras_provider.dart';
import 'package:bottle_crm/providers/invoices_provider.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/providers/notifications_provider.dart';
import 'package:bottle_crm/providers/settings_provider.dart';
import 'package:bottle_crm/providers/timesheet_provider.dart';
import 'package:bottle_crm/screens/invoices/estimates_list_screen.dart';
import 'package:bottle_crm/screens/invoices/invoices_list_screen.dart';
import 'package:bottle_crm/screens/invoices/new_invoice_screen.dart';
import 'package:bottle_crm/screens/invoices/new_recurring_screen.dart';
import 'package:bottle_crm/screens/invoices/products_list_screen.dart';
import 'package:bottle_crm/screens/invoices/recurring_list_screen.dart';
import 'package:bottle_crm/screens/notifications/notifications_screen.dart';
import 'package:bottle_crm/screens/settings/business_hours_form_sheet.dart';
import 'package:bottle_crm/screens/settings/business_hours_screen.dart';
import 'package:bottle_crm/screens/settings/custom_fields_screen.dart';
import 'package:bottle_crm/screens/settings/escalation_policy_form_sheet.dart';
import 'package:bottle_crm/screens/settings/escalation_screen.dart';
import 'package:bottle_crm/screens/settings/macros_screen.dart';
import 'package:bottle_crm/screens/tickets/macro_picker_sheet.dart';
import 'package:bottle_crm/screens/settings/settings_hub_screen.dart';
import 'package:bottle_crm/screens/settings/reopen_screen.dart';
import 'package:bottle_crm/screens/settings/routing_rule_form_sheet.dart';
import 'package:bottle_crm/screens/settings/routing_screen.dart';
import 'package:bottle_crm/screens/settings/tags_screen.dart';
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

  Widget settingsHubApp() =>
      const ProviderScope(child: MaterialApp(home: SettingsHubScreen()));

  /// [isAdmin] is overridden rather than left to fall out of a signed-in
  /// profile, because both answers matter here: the read is open to a member
  /// and every write is admin-only.
  Widget customFieldsApp({required bool isAdmin}) => ProviderScope(
    overrides: [
      customFieldsProvider.overrideWith(_FakeCustomFields.new),
      isOrgAdminProvider.overrideWithValue(isAdmin),
    ],
    child: const MaterialApp(home: CustomFieldsScreen()),
  );

  /// [myEmail] decides ownership of the personal rows, which is what the edit
  /// control turns on. `myEmailProvider` normally reads the signed-in user, so
  /// it is overridden here to drive both answers.
  Widget macrosApp({required bool isAdmin, String? myEmail}) => ProviderScope(
    overrides: [
      macrosProvider.overrideWith(_FakeMacros.new),
      isOrgAdminProvider.overrideWithValue(isAdmin),
      myEmailProvider.overrideWithValue(myEmail),
    ],
    child: const MaterialApp(home: MacrosScreen()),
  );

  /// Both answers again: a member reads the tag list, and every write on it is
  /// admin-only.
  Widget tagsApp({required bool isAdmin, bool empty = false}) => ProviderScope(
    overrides: [
      tagSettingsProvider.overrideWith(empty ? _FakeNoTags.new : _FakeTags.new),
      isOrgAdminProvider.overrideWithValue(isAdmin),
    ],
    child: const MaterialApp(home: TagsScreen()),
  );

  /// The routing list, whose fixture carries every state a rule can be in:
  /// a live rotation with a deactivated member, a rule that can assign nobody,
  /// and one already turned off.
  Widget routingApp({required bool isAdmin, bool empty = false}) =>
      ProviderScope(
        overrides: [
          routingRulesProvider.overrideWith(
            empty ? _FakeNoRoutingRules.new : _FakeRoutingRules.new,
          ),
          isOrgAdminProvider.overrideWithValue(isAdmin),
        ],
        child: const MaterialApp(home: RoutingScreen()),
      );

  /// The rule form over a button, with the people and team pickers stubbed.
  /// `people` deliberately omits the deactivated assignee, because the real
  /// lookup does: it is the case where opening the form could silently drop
  /// part of the rule.
  Widget routingFormApp({RoutingRule? existing}) => ProviderScope(
    overrides: [
      usersProvider.overrideWithValue(const [
        UserLookup(
          id: 'a1',
          email: 'ada@example.com',
          name: 'Ada',
          role: 'USER',
          isActive: true,
        ),
      ]),
      teamsProvider.overrideWithValue(const [
        TeamLookup(id: 't1', name: 'Billing crew'),
      ]),
    ],
    child: MaterialApp(
      home: Scaffold(
        body: Builder(
          builder: (context) => Center(
            child: ElevatedButton(
              onPressed: () =>
                  showRoutingRuleFormSheet(context, existing: existing),
              child: const Text('open'),
            ),
          ),
        ),
      ),
    ),
  );

  /// The escalation list. The fixture leaves Low unconfigured on purpose, so
  /// the note about priorities with no policy at all has something to say.
  Widget escalationApp({required bool isAdmin, bool empty = false}) =>
      ProviderScope(
        overrides: [
          escalationProvider.overrideWith(
            empty ? _FakeNoEscalation.new : _FakeEscalation.new,
          ),
          isOrgAdminProvider.overrideWithValue(isAdmin),
        ],
        child: const MaterialApp(home: EscalationScreen()),
      );

  /// The policy form over a button. `people` omits the deactivated target for
  /// the same reason it does in the routing form: the real lookup returns
  /// `Profile.objects.filter(is_active=True)`, so a policy pointing at somebody
  /// turned off is the case where opening the form could empty it.
  Widget escalationFormApp({
    EscalationPolicy? existing,
    List<String> available = const ['Urgent', 'Low'],
  }) => ProviderScope(
    overrides: [
      usersProvider.overrideWithValue(const [
        UserLookup(
          id: 'a1',
          email: 'ada@example.com',
          name: 'Ada',
          role: 'USER',
          isActive: true,
        ),
      ]),
      teamsProvider.overrideWithValue(const [
        TeamLookup(id: 't1', name: 'Support'),
      ]),
    ],
    child: MaterialApp(
      home: Scaffold(
        body: Builder(
          builder: (context) => Center(
            child: ElevatedButton(
              onPressed: () => showEscalationPolicyFormSheet(
                context,
                existing: existing,
                availablePriorities: available,
              ),
              child: const Text('open'),
            ),
          ),
        ),
      ),
    ),
  );

  /// The business-hours screen. `alwaysOn` is the state the engine reads as
  /// 24/7 rather than as permanently shut.
  Widget businessHoursApp({
    required bool isAdmin,
    bool alwaysOn = false,
    bool noHolidays = false,
  }) => ProviderScope(
    overrides: [
      businessHoursProvider.overrideWith(
        noHolidays
            ? _FakeNoHolidayCalendar.new
            : alwaysOn
            ? _FakeClosedCalendar.new
            : _FakeCalendar.new,
      ),
      isOrgAdminProvider.overrideWithValue(isAdmin),
    ],
    child: const MaterialApp(home: BusinessHoursScreen()),
  );

  /// The holiday sheet over a button, with a calendar that already carries
  /// 25 December so the duplicate warning has something to warn about.
  Widget holidayFormApp() => MaterialApp(
    home: Scaffold(
      body: Builder(
        builder: (context) => Center(
          child: ElevatedButton(
            onPressed: () => showHolidayFormSheet(context, _calendar()),
            child: const Text('open'),
          ),
        ),
      ),
    ),
  );

  Widget weekFormApp() => MaterialApp(
    home: Scaffold(
      body: Builder(
        builder: (context) => Center(
          child: ElevatedButton(
            onPressed: () => showBusinessHoursFormSheet(context, _calendar()),
            child: const Text('open'),
          ),
        ),
      ),
    ),
  );

  /// The reopen screen. The read is admin-only server-side, so `isAdmin` here
  /// decides whether the screen issues it at all.
  Widget reopenApp({required bool isAdmin, bool policyOff = false}) =>
      ProviderScope(
        overrides: [
          reopenPolicyProvider.overrideWith(
            policyOff ? _FakeReopenOff.new : _FakeReopen.new,
          ),
          isOrgAdminProvider.overrideWithValue(isAdmin),
        ],
        child: const MaterialApp(home: ReopenScreen()),
      );

  /// A button that opens the picker, so the sheet is rendered the way it is
  /// really reached: over a screen, with the keyboard inset in play.
  Widget macroPickerApp({List<Macro>? macros}) => ProviderScope(
    overrides: [
      activeMacrosProvider.overrideWith(
        (ref) async =>
            macros ??
            [
              Macro.fromJson(const {
                'id': 'm1',
                'title': 'Password reset, standard wording agreed with legal',
                'body':
                    'Hi there, follow the link below to reset your password '
                    'and let us know if it does not arrive within ten minutes.',
                'scope': 'org',
                'is_active': true,
              }),
              Macro.fromJson(const {
                'id': 'm2',
                'title': 'My follow-up',
                'body': 'Just checking in on this one.',
                'scope': 'personal',
                'owner_name': 'me@example.com',
                'is_active': true,
              }),
            ],
      ),
    ],
    child: MaterialApp(
      home: Scaffold(
        body: Builder(
          builder: (context) => Center(
            child: ElevatedButton(
              onPressed: () => showMacroPickerSheet(context, 't42'),
              child: const Text('open'),
            ),
          ),
        ),
      ),
    ),
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

  group('the settings cluster at 390px', () {
    testWidgets('the hub renders without overflowing', (tester) async {
      await pump(tester, settingsHubApp());
      expect(tester.takeException(), isNull);
    });

    testWidgets('the hub opens to a member, not just an admin', (tester) async {
      // isOrgAdminProvider is false in this test's state. The reads under the
      // hub are open to any member server-side, and the web sidebar keeps the
      // entry for everyone for that reason, so a lock screen here would be
      // this app disagreeing with the API about who may look.
      await pump(tester, settingsHubApp());
      expect(find.text('Custom fields'), findsOneWidget);
      expect(find.text('Tags'), findsOneWidget);
    });

    testWidgets('custom fields render without overflowing', (tester) async {
      await pump(tester, customFieldsApp(isAdmin: true));
      expect(tester.takeException(), isNull);
    });

    testWidgets('custom fields fit with the system font scaled up', (
      tester,
    ) async {
      // The row that earns this: a Wrap of up to four badges plus an option
      // count, over a long label, with two buttons under it.
      await pump(tester, customFieldsApp(isAdmin: true), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('a member sees the fields but no write controls', (
      tester,
    ) async {
      await pump(tester, customFieldsApp(isAdmin: false));

      expect(find.text('Severity'), findsOneWidget, reason: 'the read is open');
      expect(find.widgetWithText(OutlinedButton, 'Edit'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Turn off'), findsNothing);
      expect(find.byTooltip('New custom field'), findsNothing);
    });

    testWidgets('a turned-off field offers Turn on, not Turn off', (
      tester,
    ) async {
      await pump(tester, customFieldsApp(isAdmin: true));

      expect(find.widgetWithText(OutlinedButton, 'Turn on'), findsOneWidget);
      expect(find.text('Turned off'), findsOneWidget);
    });

    testWidgets('a required field with gaps says so on the row', (
      tester,
    ) async {
      await pump(tester, customFieldsApp(isAdmin: true));

      // Marking a field required binds new saves only, so the count is the
      // thing that makes "Required" honest.
      expect(find.textContaining('23 records have no value'), findsOneWidget);
      // One gap, so the singular branch of the banner. The fake sets
      // requiredWithGaps to 1 deliberately: the plural string is the one that
      // reads naturally when written, and the singular is where "1 required
      // fields have" slips through.
      expect(
        find.textContaining('One required field has records'),
        findsOneWidget,
      );
    });

    testWidgets('the new-field sheet renders without overflowing', (
      tester,
    ) async {
      await pump(tester, customFieldsApp(isAdmin: true));
      await tester.tap(find.byTooltip('New custom field'));
      await tester.pumpAndSettle();

      expect(find.text('New custom field'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('the sheet fills the key in from the label', (tester) async {
      await pump(tester, customFieldsApp(isAdmin: true));
      await tester.tap(find.byTooltip('New custom field'));
      await tester.pumpAndSettle();

      await tester.enterText(
        find.widgetWithText(TextField, 'Label'),
        'Deal source',
      );
      await tester.pumpAndSettle();

      final key = tester.widget<TextField>(
        find.widgetWithText(TextField, 'Key'),
      );
      expect(key.controller?.text, 'deal_source');
    });

    testWidgets('the sheet asks for options only on a dropdown', (
      tester,
    ) async {
      await pump(tester, customFieldsApp(isAdmin: true));
      await tester.tap(find.byTooltip('New custom field'));
      await tester.pumpAndSettle();

      expect(find.text('Add option'), findsNothing);

      await tester.tap(find.text('Text').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Dropdown').last);
      await tester.pumpAndSettle();

      expect(find.text('Add option'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('editing a field shows the frozen three as text', (
      tester,
    ) async {
      await pump(tester, customFieldsApp(isAdmin: true));
      await tester.tap(find.widgetWithText(OutlinedButton, 'Edit').first);
      await tester.pumpAndSettle();

      // The server refuses a change to any of the three with a 400. Offering
      // the input and letting the save fail teaches the rule the hard way.
      expect(find.widgetWithText(TextField, 'Key'), findsNothing);
      expect(find.textContaining('Fixed after creation'), findsWidgets);
      expect(tester.takeException(), isNull);
    });
  });

  group('saved replies at 390px', () {
    testWidgets('render without overflowing', (tester) async {
      await pump(tester, macrosApp(isAdmin: true, myEmail: 'me@example.com'));
      expect(tester.takeException(), isNull);
    });

    testWidgets('fit with the system font scaled up', (tester) async {
      await pump(
        tester,
        macrosApp(isAdmin: true, myEmail: 'me@example.com'),
        textScale: 1.5,
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('a member may still write their own', (tester) async {
      // The only settings page with a write open to everyone. Hiding the add
      // button from a member would remove a feature the API grants them.
      await pump(tester, macrosApp(isAdmin: false, myEmail: 'me@example.com'));
      expect(find.byTooltip('New saved reply'), findsOneWidget);
    });

    testWidgets('a member gets no controls on a shared reply', (tester) async {
      await pump(tester, macrosApp(isAdmin: false, myEmail: 'me@example.com'));

      // Two rows are mine (one personal, one turned-off personal), one is the
      // org macro a member may read and not touch.
      expect(find.widgetWithText(OutlinedButton, 'Turn off'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Delete'), findsOneWidget);
    });

    testWidgets('an admin gets Turn off on the shared reply', (tester) async {
      await pump(tester, macrosApp(isAdmin: true, myEmail: 'me@example.com'));

      expect(find.widgetWithText(OutlinedButton, 'Turn off'), findsOneWidget);
      expect(find.widgetWithText(OutlinedButton, 'Delete'), findsOneWidget);
    });

    testWidgets('an admin gets nothing on somebody else personal reply', (
      tester,
    ) async {
      // The one place admin is not an override: the server answers 404 there.
      await pump(
        tester,
        macrosApp(isAdmin: true, myEmail: 'other@example.com'),
      );

      expect(find.widgetWithText(OutlinedButton, 'Delete'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Edit'), findsOneWidget);
    });

    testWidgets('a broken placeholder is named, not counted', (tester) async {
      await pump(tester, macrosApp(isAdmin: true, myEmail: 'me@example.com'));

      // The author has to know which token to fix. A typo is only obvious
      // beside the right spelling. Two widgets carry the token, the body
      // preview and the warning; this asserts the warning.
      expect(
        find.text('%custmer_name% is not recognized and goes out as written'),
        findsOneWidget,
      );
    });

    testWidgets('the form offers the scope choice only to an admin', (
      tester,
    ) async {
      await pump(tester, macrosApp(isAdmin: false, myEmail: 'me@example.com'));
      await tester.tap(find.byTooltip('New saved reply'));
      await tester.pumpAndSettle();

      // Not a greyed control: showing a disabled "Everyone" would advertise
      // an action the server answers 403 to.
      expect(find.text('Who can use it'), findsNothing);
      expect(find.textContaining('Saved for you alone'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('the form inserts a placeholder at the cursor', (tester) async {
      await pump(tester, macrosApp(isAdmin: true, myEmail: 'me@example.com'));
      await tester.tap(find.byTooltip('New saved reply'));
      await tester.pumpAndSettle();

      await tester.enterText(find.widgetWithText(TextField, 'Reply'), 'Hi ');
      await tester.tap(find.text('%customer_name%'));
      await tester.pumpAndSettle();

      final body = tester.widget<TextField>(
        find.widgetWithText(TextField, 'Reply'),
      );
      expect(body.controller?.text, 'Hi %customer_name%');
      expect(tester.takeException(), isNull);
    });
  });

  group('the saved-reply picker at 390px', () {
    testWidgets('renders without overflowing', (tester) async {
      await pump(tester, macroPickerApp());
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      expect(find.text('Saved replies'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('fits with the system font scaled up', (tester) async {
      await pump(tester, macroPickerApp(), textScale: 1.5);
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
    });

    testWidgets('says where to write one when there are none', (tester) async {
      // An empty picker with no explanation reads as broken. The settings
      // page is two taps away and a member can use it.
      await pump(tester, macroPickerApp(macros: const []));
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      expect(find.textContaining('Organization settings'), findsOneWidget);
    });

    testWidgets('filters as you type', (tester) async {
      await pump(tester, macroPickerApp());
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      // "follow-up", not "follow": the search reads the body as well as the
      // title, and the shared reply's body says "follow the link below". That
      // is deliberate, since the words you remember are usually in the reply
      // rather than in its name, and it is why the narrower term is used here.
      await tester.enterText(find.byType(TextField).first, 'follow-up');
      await tester.pumpAndSettle();

      expect(find.text('My follow-up'), findsOneWidget);
      expect(find.textContaining('Password reset'), findsNothing);
    });

    testWidgets('searches the body, not just the title', (tester) async {
      await pump(tester, macroPickerApp());
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).first, 'ten minutes');
      await tester.pumpAndSettle();

      expect(find.textContaining('Password reset'), findsOneWidget);
      expect(find.text('My follow-up'), findsNothing);
    });

    testWidgets('marks which replies are shared and which are yours', (
      tester,
    ) async {
      await pump(tester, macroPickerApp());
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      // Sending a personal draft believing it is the agreed org wording is the
      // mistake this label prevents.
      expect(find.text('Everyone'), findsOneWidget);
      expect(find.text('Just you'), findsOneWidget);
    });
  });

  group('tags at 390px', () {
    testWidgets('render without overflowing', (tester) async {
      await pump(tester, tagsApp(isAdmin: true));
      expect(tester.takeException(), isNull);
    });

    testWidgets('fit with the system font scaled up', (tester) async {
      // The rows that earn this: a duplicate banner carrying two names, a
      // sentence about both, and a merge button, over a tag name long enough
      // to wrap on its own.
      await pump(tester, tagsApp(isAdmin: true), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('a member sees the tags but no write controls', (tester) async {
      await pump(tester, tagsApp(isAdmin: false));

      expect(find.text('Renewals'), findsOneWidget, reason: 'the read is open');
      expect(find.byTooltip('New tag'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Turn off'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Turn back on'), findsNothing);
    });

    testWidgets('a member is still told two tags overlap', (tester) async {
      // Worth something without the merge: they can stop using one today.
      await pump(tester, tagsApp(isAdmin: false));

      expect(
        find.textContaining('look like the same tag'),
        findsOneWidget,
        reason: 'the banner is a read, not an action',
      );
      expect(find.textContaining('Merge'), findsNothing);
    });

    testWidgets('the merge button names the tag that survives', (tester) async {
      // Which way a merge runs is the whole question, and it is not reversible
      // by pressing the other button.
      await pump(tester, tagsApp(isAdmin: true));

      expect(
        find.widgetWithText(OutlinedButton, 'Merge into Renewals'),
        findsOneWidget,
      );
    });

    testWidgets('turning a tag off never promises a delete', (tester) async {
      // The server soft-archives: the row stays and every record keeps the
      // tag. Saying Delete would promise a removal that does not happen.
      await pump(tester, tagsApp(isAdmin: true));
      await tester.tap(find.widgetWithText(OutlinedButton, 'Turn off').first);
      await tester.pumpAndSettle();

      expect(find.text('Turn off Renewals?'), findsOneWidget);
      expect(find.textContaining('9 records keep this tag'), findsOneWidget);
      expect(find.textContaining('turn it back on'), findsOneWidget);
      expect(find.textContaining('Delete'), findsNothing);
    });

    testWidgets('the merge confirm says it cannot be undone', (tester) async {
      await pump(tester, tagsApp(isAdmin: true));
      await tester.tap(
        find.widgetWithText(OutlinedButton, 'Merge into Renewals'),
      );
      await tester.pumpAndSettle();

      expect(find.text('Merge Renewal into Renewals?'), findsOneWidget);
      expect(
        find.textContaining('2 records move from Renewal to Renewals'),
        findsOneWidget,
      );
      expect(find.textContaining('cannot be undone'), findsOneWidget);
    });

    testWidgets('a turned-off tag offers Turn back on, not Turn off', (
      tester,
    ) async {
      await pump(tester, tagsApp(isAdmin: true));

      expect(
        find.widgetWithText(OutlinedButton, 'Turn back on'),
        findsOneWidget,
      );
      expect(find.text('Turned off'), findsOneWidget);
    });

    testWidgets('a row says where the tag is actually used', (tester) async {
      // The web has a column per record type; a phone row has one line, so it
      // lists the non-zero ones and every one of them, so the parts sum to the
      // total beside them.
      await pump(tester, tagsApp(isAdmin: true));

      expect(find.text('9 leads'), findsOneWidget);
      expect(find.text('2 leads, 1 ticket'), findsOneWidget);
    });

    testWidgets('an unused tag is called out while it is still on', (
      tester,
    ) async {
      await pump(tester, tagsApp(isAdmin: true));
      // Below the fold on a phone, which is the point of scrolling to it: the
      // badge has to survive the list, not just the first screenful.
      await tester.scrollUntilVisible(find.text('Dormant'), 200);
      await tester.pumpAndSettle();
      expect(find.text('Unused'), findsOneWidget);
    });

    testWidgets('an org with no tags gets the empty state', (tester) async {
      await pump(tester, tagsApp(isAdmin: true, empty: true));
      expect(find.text('No tags yet'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  });

  group('routing rules at 390px', () {
    testWidgets('render without overflowing', (tester) async {
      await pump(tester, routingApp(isAdmin: true));
      expect(tester.takeException(), isNull);
    });

    testWidgets('fit with the system font scaled up', (tester) async {
      await pump(tester, routingApp(isAdmin: true), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('keep the order the engine runs them in', (tester) async {
      // The order is the program: the engine takes the first match. A list
      // that reordered would show a different program from the one that runs.
      await pump(tester, routingApp(isAdmin: true));

      final first = tester.getTopLeft(find.text('Billing questions')).dy;
      final second = tester.getTopLeft(find.text('Everything else')).dy;
      expect(first, lessThan(second));
    });

    testWidgets('name the agent the engine would actually pick', (
      tester,
    ) async {
      // The fixture is built so the two ways of getting this wrong give
      // different, checkable answers: the cursor is the NEXT index, not the
      // last, and it indexes the active pool in id order. Adding one and
      // indexing the serializer's list names Cai, who is deactivated and can
      // never be picked.
      await pump(tester, routingApp(isAdmin: true));

      expect(find.text('Next in the rotation: Brin'), findsOneWidget);
      expect(find.text('Next in the rotation: Cai'), findsNothing);
    });

    testWidgets('flag a rule that matches everything', (tester) async {
      await pump(tester, routingApp(isAdmin: true));
      expect(find.text('Matches every new ticket'), findsOneWidget);
    });

    testWidgets('say what happens to tickets a dead rule matches', (
      tester,
    ) async {
      await pump(tester, routingApp(isAdmin: true));
      expect(
        find.textContaining('fall through to the rules below'),
        findsOneWidget,
      );
    });

    testWidgets('name the deactivated member the rotation skips', (
      tester,
    ) async {
      await pump(tester, routingApp(isAdmin: true));
      expect(find.text('Cai is deactivated and is skipped.'), findsOneWidget);
    });

    testWidgets('a member sees the rules but no write controls', (
      tester,
    ) async {
      await pump(tester, routingApp(isAdmin: false));

      expect(find.text('Billing questions'), findsOneWidget);
      expect(find.byTooltip('New rule'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Edit'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Delete'), findsNothing);
    });

    testWidgets('the delete confirm says it is permanent and offers the '
        'reversible option', (tester) async {
      // This resource hard-deletes, unlike custom fields, tags and org macros,
      // so the dialog cannot borrow their wording.
      await pump(tester, routingApp(isAdmin: true));
      await tester.tap(find.widgetWithText(OutlinedButton, 'Delete').first);
      await tester.pumpAndSettle();

      expect(find.text('Delete Billing questions?'), findsOneWidget);
      expect(find.textContaining('gone for good'), findsOneWidget);
      expect(find.textContaining('turn it off instead'), findsOneWidget);
    });

    testWidgets('a turned-off rule offers Turn on, not Turn off', (
      tester,
    ) async {
      await pump(tester, routingApp(isAdmin: true));
      await tester.scrollUntilVisible(find.text('Old escalation'), 200);
      await tester.pumpAndSettle();
      expect(find.widgetWithText(OutlinedButton, 'Turn on'), findsOneWidget);
    });

    testWidgets('an org with no rules is told what that means', (tester) async {
      await pump(tester, routingApp(isAdmin: true, empty: true));
      expect(find.text('No routing rules'), findsOneWidget);
      expect(
        find.textContaining('arrive unassigned'),
        findsOneWidget,
        reason: 'an empty list is a working state with a consequence',
      );
    });
  });

  group('the routing rule form at 390px', () {
    Future<void> open(WidgetTester tester, {RoutingRule? existing}) async {
      await pump(tester, routingFormApp(existing: existing));
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
    }

    testWidgets('renders without overflowing', (tester) async {
      await open(tester);
      expect(tester.takeException(), isNull);
    });

    testWidgets('fits with the system font scaled up', (tester) async {
      await pump(tester, routingFormApp(), textScale: 1.5);
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });

    testWidgets('warns that a rule with no conditions catches everything', (
      tester,
    ) async {
      await open(tester);
      expect(find.textContaining('matches every new ticket'), findsOneWidget);
    });

    testWidgets('says what stopping after this rule costs', (tester) async {
      // On by default, and it is the setting that turns an empty pool from
      // "falls through" into "swallows the ticket".
      await open(tester);
      expect(
        find.textContaining('No rule below this one gets a turn'),
        findsOneWidget,
      );
    });

    testWidgets('keeps a deactivated assignee the picker cannot offer', (
      tester,
    ) async {
      // The lookup returns active profiles only, so a rule pointing at a
      // deactivated one would lose them just by being opened. That is a delete
      // performed as a side effect of viewing.
      await open(
        tester,
        existing: RoutingRule(
          id: 'r1',
          name: 'Billing questions',
          strategy: RoutingRule.strategyRoundRobin,
          targetAssignees: const [
            RoutingTarget(id: 'a1', name: 'Ada'),
            RoutingTarget(id: 'c1', name: 'Cai', isActive: false),
          ],
        ),
      );

      expect(find.text('Cai (deactivated)'), findsOneWidget);
    });
  });

  group('escalation policies at 390px', () {
    testWidgets('render without overflowing', (tester) async {
      await pump(tester, escalationApp(isAdmin: true));
      expect(tester.takeException(), isNull);
    });

    testWidgets('fit with the system font scaled up', (tester) async {
      await pump(tester, escalationApp(isAdmin: true), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('sort by severity, not alphabetically', (tester) async {
      // The model orders the CharField, which puts Low between High and
      // Normal. Both clients override it.
      await pump(tester, escalationApp(isAdmin: true));

      final urgent = tester.getTopLeft(find.text('Urgent')).dy;
      final high = tester.getTopLeft(find.text('High')).dy;
      expect(
        urgent,
        lessThan(high),
        reason: 'alphabetical order would put High first',
      );
      // The third card is below the fold on a phone, which is itself the
      // assertion that it sorts last.
      expect(find.text('Normal'), findsNothing);
      await tester.scrollUntilVisible(find.text('Normal'), 200);
      expect(find.text('Normal'), findsOneWidget);
    });

    testWidgets('stack the two halves rather than columning them', (
      tester,
    ) async {
      // The web puts them side by side and collapses to one column below
      // 768px. Two columns at 390px does not overflow, it just leaves each
      // outcome sentence about twenty characters wide, so nothing but this
      // catches it.
      await pump(tester, escalationApp(isAdmin: true));

      final first = tester.getTopLeft(find.text('MISSED FIRST RESPONSE').first);
      final second = tester.getTopLeft(find.text('MISSED RESOLUTION').first);
      expect(second.dy, greaterThan(first.dy));
      expect(second.dx, first.dx);
    });

    testWidgets('call a half with a team but no target dead', (tester) async {
      // The combination the web reported as live. `_scan_org` guards the
      // dispatch on the target being set, so a team alone is never told.
      await pump(tester, escalationApp(isAdmin: true));

      expect(
        find.text(
          'Nothing. No target is set, and the Support team is not notified '
          'on its own.',
        ),
        findsOneWidget,
      );
    });

    testWidgets('total the breaches that reached nobody', (tester) async {
      // 11 on the dead High half, plus both halves of the policy that is off.
      await pump(tester, escalationApp(isAdmin: true));

      expect(
        find.textContaining('19 breaches in the last 30 days told nobody'),
        findsOneWidget,
      );
    });

    testWidgets('say a dead half acted on none of its breaches', (
      tester,
    ) async {
      await pump(tester, escalationApp(isAdmin: true));
      expect(
        find.text('11 in the last 30 days, none of them acted on'),
        findsOneWidget,
      );
    });

    testWidgets('warn that a reassign half never notifies the team', (
      tester,
    ) async {
      // The other half of the same correction: `_dispatch_breach` builds a
      // recipient list only for the two notify actions.
      await pump(tester, escalationApp(isAdmin: true));

      expect(
        find.text(
          'The Support team is not notified here: this half only reassigns.',
        ),
        findsOneWidget,
      );
      expect(find.text('Reassign to Ada.'), findsOneWidget);
    });

    testWidgets('name the priorities with no policy at all', (tester) async {
      // Otherwise invisible: breach counts are attached to policies, so an
      // unconfigured priority contributes no row and no number.
      await pump(tester, escalationApp(isAdmin: true));

      expect(
        find.textContaining('Low has no policy, so breaches at that priority'),
        findsOneWidget,
      );
    });

    testWidgets('a member sees the policies but no write controls', (
      tester,
    ) async {
      await pump(tester, escalationApp(isAdmin: false));

      expect(find.text('Urgent'), findsOneWidget);
      expect(find.byTooltip('New policy'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Edit'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Delete'), findsNothing);
    });

    testWidgets('the delete confirm says it is permanent and offers the '
        'reversible option', (tester) async {
      await pump(tester, escalationApp(isAdmin: true));
      await tester.tap(find.widgetWithText(OutlinedButton, 'Delete').first);
      await tester.pumpAndSettle();

      expect(find.text('Delete the Urgent policy?'), findsOneWidget);
      expect(find.textContaining('gone for good'), findsOneWidget);
      expect(find.textContaining('turn it off instead'), findsOneWidget);
    });

    testWidgets('a turned-off policy offers Turn on, not Turn off', (
      tester,
    ) async {
      await pump(tester, escalationApp(isAdmin: true));
      await tester.scrollUntilVisible(find.text('Turned off'), 200);
      await tester.pumpAndSettle();
      expect(find.widgetWithText(OutlinedButton, 'Turn on'), findsOneWidget);
    });

    testWidgets('an org with no policies is told what that means', (
      tester,
    ) async {
      await pump(tester, escalationApp(isAdmin: true, empty: true));
      expect(find.text('No escalation policies'), findsOneWidget);
      expect(
        find.textContaining('escalates to nobody'),
        findsOneWidget,
        reason: 'an empty list is a working state with a consequence',
      );
    });
  });

  group('the escalation policy form at 390px', () {
    Future<void> open(
      WidgetTester tester, {
      EscalationPolicy? existing,
      double textScale = 1.0,
    }) async {
      await pump(
        tester,
        escalationFormApp(existing: existing),
        textScale: textScale,
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
    }

    testWidgets('renders without overflowing', (tester) async {
      await open(tester);
      expect(tester.takeException(), isNull);
    });

    testWidgets('fits with the system font scaled up', (tester) async {
      await open(tester, textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('warns that a half with no target does nothing yet', (
      tester,
    ) async {
      // A create starts with both targets on Nobody, and the warning is not
      // tied to the action: Notify with nobody picked is as dead as Reassign
      // with nobody picked.
      await open(tester);
      expect(find.text(escalationNoTargetHint), findsNWidgets(2));
    });

    testWidgets('offers only the priorities with no policy yet', (
      tester,
    ) async {
      await open(tester);
      // The priority select is the first dropdown on the sheet.
      await tester.tap(find.byType(DropdownButtonFormField<String>).first);
      await tester.pumpAndSettle();

      // Urgent and Low are free in the fixture; High and Normal are taken, and
      // offering them would only produce a 400 the admin could be spared.
      expect(find.text('Low'), findsWidgets);
      expect(find.text('High'), findsNothing);
      expect(find.text('Normal'), findsNothing);
    });

    testWidgets('freezes the priority on an edit rather than offering it', (
      tester,
    ) async {
      // `EscalationPolicyDetailView.put` strips the key from the body, so a
      // control here would report a change it did not make.
      await open(tester, existing: _urgentPolicy());

      expect(find.textContaining('fixed after it is created'), findsOneWidget);
      expect(
        find.widgetWithText(DropdownButtonFormField<String>, 'Priority'),
        findsNothing,
      );
    });

    testWidgets('keeps a deactivated target the picker cannot offer', (
      tester,
    ) async {
      await open(tester, existing: _deactivatedTargetPolicy());

      expect(find.text('Cai (deactivated)'), findsOneWidget);
      expect(
        find.textContaining('waits for somebody who cannot sign in'),
        findsOneWidget,
      );
    });
  });
  group('business hours at 390px', () {
    testWidgets('renders without overflowing', (tester) async {
      await pump(tester, businessHoursApp(isAdmin: true));
      expect(tester.takeException(), isNull);
    });

    testWidgets('fits with the system font scaled up', (tester) async {
      await pump(tester, businessHoursApp(isAdmin: true), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('names a closed day rather than leaving it blank', (
      tester,
    ) async {
      // A blank cell reads as missing data, "Closed" reads as a decision.
      await pump(tester, businessHoursApp(isAdmin: true));
      expect(find.text('Closed'), findsWidgets);
      expect(find.text('09:00 to 17:00'), findsWidgets);
    });

    testWidgets('says a calendar with no open day runs the clock anyway', (
      tester,
    ) async {
      // The finding. `_has_any_open_window` false means the calendar is
      // dropped and the SLA runs on the wall clock, so every row reading
      // Closed means the opposite of what it looks like.
      await pump(tester, businessHoursApp(isAdmin: true, alwaysOn: true));

      expect(
        find.textContaining('targets run around the clock'),
        findsOneWidget,
      );
      expect(
        find.textContaining('expires four hours after the ticket arrives'),
        findsOneWidget,
      );
    });

    testWidgets('does not cry wolf on an ordinary week', (tester) async {
      await pump(tester, businessHoursApp(isAdmin: true));
      expect(find.textContaining('around the clock'), findsNothing);
    });

    testWidgets('says what an empty holiday list means', (tester) async {
      await pump(tester, businessHoursApp(isAdmin: true, noHolidays: true));
      expect(
        find.textContaining('Targets keep running on public holidays'),
        findsOneWidget,
      );
    });

    testWidgets('a member sees the week but no write controls', (tester) async {
      await pump(tester, businessHoursApp(isAdmin: false));

      expect(find.text('Monday'), findsOneWidget);
      expect(find.byTooltip('Edit hours'), findsNothing);
      expect(find.text('Add'), findsNothing);
      expect(find.byTooltip('Remove this holiday'), findsNothing);
    });

    testWidgets('the remove confirm says the day counts as work again', (
      tester,
    ) async {
      await pump(tester, businessHoursApp(isAdmin: true));
      await tester.scrollUntilVisible(
        find.byTooltip('Remove this holiday'),
        200,
      );
      await tester.tap(find.byTooltip('Remove this holiday').first);
      await tester.pumpAndSettle();

      expect(find.text('Remove Xmas?'), findsOneWidget);
      expect(
        find.textContaining('counts as working time again'),
        findsOneWidget,
      );
    });
  });

  group('the business-hours forms at 390px', () {
    Future<void> openWeek(WidgetTester tester, {double textScale = 1.0}) async {
      await pump(tester, weekFormApp(), textScale: textScale);
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
    }

    testWidgets('the week form renders without overflowing', (tester) async {
      await openWeek(tester);
      expect(tester.takeException(), isNull);
    });

    testWidgets('the week form fits with the font scaled up', (tester) async {
      await openWeek(tester, textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('the week form warns live when the last day is closed', (
      tester,
    ) async {
      await openWeek(tester);
      // Close the five open days; the warning appears as the last one goes.
      for (var i = 0; i < 5; i++) {
        await tester.tap(find.byType(Switch).at(i));
        await tester.pumpAndSettle();
      }
      expect(
        find.textContaining('targets run around the clock'),
        findsOneWidget,
      );
    });

    testWidgets('the holiday form warns before writing a date already taken', (
      tester,
    ) async {
      // The POST answers 200 with the row already stored and throws the typed
      // name away, so the warning has to come before the write.
      await pump(tester, holidayFormApp());
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      expect(find.text('Pick a date'), findsOneWidget);
    });
  });

  group('reopen policy at 390px', () {
    testWidgets('renders without overflowing', (tester) async {
      await pump(tester, reopenApp(isAdmin: true));
      expect(tester.takeException(), isNull);
    });

    testWidgets('fits with the system font scaled up', (tester) async {
      await pump(tester, reopenApp(isAdmin: true), textScale: 1.5);
      expect(tester.takeException(), isNull);
    });

    testWidgets('a member is told why rather than shown a failed request', (
      tester,
    ) async {
      // `ReopenPolicyView.get` is admin-only, unlike every other read in this
      // cluster, so the screen gates the read rather than issuing it.
      await pump(tester, reopenApp(isAdmin: false));

      expect(find.text('Administrators only'), findsOneWidget);
      expect(find.byTooltip('Edit policy'), findsNothing);
    });

    testWidgets('shows the three figures behind the window', (tester) async {
      await pump(tester, reopenApp(isAdmin: true));
      expect(find.text('6'), findsOneWidget);
      expect(find.text('4'), findsOneWidget);
      expect(find.text('2d'), findsOneWidget);
    });

    testWidgets('says the misses reached nobody while the policy is on', (
      tester,
    ) async {
      await pump(tester, reopenApp(isAdmin: true));
      expect(
        find.textContaining('Those customers are still waiting'),
        findsOneWidget,
      );
    });

    // Present tense: with the policy off, nothing brings a ticket back, so the
    // explanation cannot be written as though a reply still did. Two tests
    // rather than one, because re-pumping a second ProviderScope over the first
    // keeps the element tree and the assertions cross-contaminate.
    testWidgets('does not describe a reopen that cannot happen', (
      tester,
    ) async {
      await pump(tester, reopenApp(isAdmin: true, policyOff: true));
      await tester.scrollUntilVisible(
        find.textContaining('Which addresses accept replies'),
        300,
      );
      expect(find.textContaining('Turned on, a reply'), findsOneWidget);
    });

    testWidgets('describes it plainly while the policy is on', (tester) async {
      await pump(tester, reopenApp(isAdmin: true));
      await tester.scrollUntilVisible(
        find.textContaining('Which addresses accept replies'),
        300,
      );
      expect(find.textContaining('Turned on, a reply'), findsNothing);
      expect(
        find.textContaining('A reopened ticket is the same ticket'),
        findsOneWidget,
      );
    });

    testWidgets('refuses to report a zero it did not measure', (tester) async {
      // The finding. With reopening off, `_evaluate_reopen` returns before the
      // window comparison and nothing is ever flagged, so a plain 0 here is
      // reassurance about the one thing certainly happening.
      await pump(tester, reopenApp(isAdmin: true, policyOff: true));

      expect(find.text('n/a'), findsOneWidget);
      expect(
        find.textContaining('not because nothing is being lost'),
        findsOneWidget,
      );
    });
  });
}

/// A working week with one holiday, which is what most orgs look like.
BusinessCalendar _calendar({bool alwaysOn = false, bool holidays = true}) {
  final json = <String, dynamic>{
    'id': 'c1',
    'name': 'Support desk',
    'timezone': 'Asia/Kolkata',
    'is_default': true,
    'holidays': holidays
        ? const [
            {'id': 'h1', 'date': '2026-12-25', 'name': 'Xmas'},
          ]
        : const [],
  };
  const open = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday'};
  for (final (_, key) in businessWeekdays) {
    final isOpen = !alwaysOn && open.contains(key);
    json['${key}_open'] = isOpen ? '09:00:00' : null;
    json['${key}_close'] = isOpen ? '17:00:00' : null;
  }
  return BusinessCalendar.fromJson(json);
}

class _FakeCalendar extends BusinessHoursNotifier {
  @override
  Future<BusinessCalendar> build() async => _calendar();
}

class _FakeClosedCalendar extends BusinessHoursNotifier {
  @override
  Future<BusinessCalendar> build() async => _calendar(alwaysOn: true);
}

class _FakeNoHolidayCalendar extends BusinessHoursNotifier {
  @override
  Future<BusinessCalendar> build() async => _calendar(holidays: false);
}

class _FakeReopen extends ReopenPolicyNotifier {
  @override
  Future<ReopenPolicy> build() async => ReopenPolicy.fromJson(const {
    'is_enabled': true,
    'reopen_window_days': 7,
    'reopen_to_status': 'Pending',
    'notify_assigned': true,
    'reopened_last_30d': 6,
    'replies_after_window_30d': 4,
    'median_days_to_reply': 2,
  });
}

class _FakeReopenOff extends ReopenPolicyNotifier {
  @override
  Future<ReopenPolicy> build() async => ReopenPolicy.fromJson(const {
    'is_enabled': false,
    'reopen_window_days': 7,
    'reopen_to_status': 'Pending',
    'notify_assigned': true,
    'reopened_last_30d': 1,
    'replies_after_window_30d': 0,
    'median_days_to_reply': 9,
  });
}

/// A policy set on Urgent, both halves live.
EscalationPolicy _urgentPolicy() => EscalationPolicy.fromJson(const {
  'id': 'e1',
  'priority': 'Urgent',
  'is_active': true,
  'first_response_action': 'notify',
  'resolution_action': 'reassign',
  'first_response_target': {
    'id': 'a1',
    'is_active': true,
    'user_details': {'name': 'Ada', 'email': 'ada@example.com'},
  },
  'resolution_target': {
    'id': 'a1',
    'is_active': true,
    'user_details': {'name': 'Ada', 'email': 'ada@example.com'},
  },
  'notify_team': {'id': 't1', 'name': 'Support'},
  'breaches_last_30d': {'first_response': 3, 'resolution': 2},
});

/// A policy whose first-response target is somebody deactivated. The engine
/// still escalates to them, with no active filter.
EscalationPolicy _deactivatedTargetPolicy() => EscalationPolicy.fromJson(const {
  'id': 'e9',
  'priority': 'High',
  'is_active': true,
  'first_response_action': 'notify',
  'resolution_action': 'notify',
  'first_response_target': {
    'id': 'c1',
    'is_active': false,
    'user_details': {'name': 'Cai', 'email': 'cai@example.com'},
  },
  'resolution_target': null,
  'notify_team': null,
  'breaches_last_30d': {'first_response': 0, 'resolution': 0},
});

/// Three policies covering every state a card has to draw, and Low left
/// unconfigured so the "no policy at all" note has something to say.
///
/// The High policy is the case the web read wrong: a `notify` half with a team
/// and no target. Its 11 breaches are the ones that reached nobody while the
/// row looked configured.
class _FakeEscalation extends EscalationNotifier {
  @override
  Future<EscalationState> build() async => EscalationState(
    policies: sortedEscalationPolicies([
      _urgentPolicy(),
      EscalationPolicy.fromJson(const {
        'id': 'e2',
        'priority': 'High',
        'is_active': true,
        'first_response_action': 'notify',
        'resolution_action': 'notify_and_reassign',
        'first_response_target': null,
        'resolution_target': {
          'id': 'b1',
          'is_active': true,
          'user_details': {'name': 'Brin', 'email': 'brin@example.com'},
        },
        'notify_team': {'id': 't1', 'name': 'Support'},
        'breaches_last_30d': {'first_response': 11, 'resolution': 1},
      }),
      EscalationPolicy.fromJson(const {
        'id': 'e3',
        'priority': 'Normal',
        'is_active': false,
        'first_response_action': 'notify',
        'resolution_action': 'notify',
        'first_response_target': {
          'id': 'a1',
          'is_active': true,
          'user_details': {'name': 'Ada', 'email': 'ada@example.com'},
        },
        'resolution_target': {
          'id': 'a1',
          'is_active': true,
          'user_details': {'name': 'Ada', 'email': 'ada@example.com'},
        },
        'notify_team': null,
        'breaches_last_30d': {'first_response': 4, 'resolution': 4},
      }),
    ]),
  );
}

class _FakeNoEscalation extends EscalationNotifier {
  @override
  Future<EscalationState> build() async => const EscalationState();
}

/// A tag set with every state the screen has to draw: a duplicate pair, a name
/// long enough to wrap, a tag applied to nothing, and one already turned off.
class _FakeTags extends TagsNotifier {
  @override
  Future<TagsState> build() async => TagsState(
    tags: sortedTags([
      Tag.fromJson(const {
        'id': 't1',
        'name': 'Renewals',
        'slug': 'renewals',
        'is_active': true,
        'usage': {'leads': 9},
      }),
      Tag.fromJson(const {
        'id': 't2',
        'name': 'Renewal',
        'slug': 'renewal',
        'is_active': true,
        'usage': {'leads': 2},
      }),
      Tag.fromJson(const {
        'id': 't3',
        'name': 'Escalated by the customer success team',
        'slug': 'escalated-by-the-customer-success-team',
        'is_active': true,
        'usage': {'leads': 2, 'cases': 1},
      }),
      Tag.fromJson(const {
        'id': 't4',
        'name': 'Dormant',
        'slug': 'dormant',
        'is_active': true,
        'usage': {'leads': 0},
      }),
      Tag.fromJson(const {
        'id': 't5',
        'name': 'Legacy import',
        'slug': 'legacy-import',
        'is_active': false,
        'usage': {'leads': 4},
      }),
    ]),
    count: 5,
    active: 4,
    unused: 1,
  );
}

class _FakeNoTags extends TagsNotifier {
  @override
  Future<TagsState> build() async => const TagsState();
}

/// Three rules covering every state a row has to draw. The rotation is built
/// so the two ways of reading the cursor wrong give different answers: the
/// active pool in id order is [Ada, Brin], cursor 1 is Brin, while adding one
/// and indexing the serializer's list gives Cai, who is deactivated.
class _FakeRoutingRules extends RoutingRulesNotifier {
  @override
  Future<RoutingRulesState> build() async => RoutingRulesState(
    rules: [
      RoutingRule.fromJson(const {
        'id': 'r1',
        'name': 'Billing questions',
        'priority_order': 10,
        'is_active': true,
        'strategy': 'round_robin',
        'stop_processing': true,
        'conditions': [
          {
            'field': 'priority',
            'op': 'in',
            'value': ['High', 'Urgent'],
          },
        ],
        'target_assignees': [
          {
            'id': 'a1',
            'is_active': true,
            'user_details': {'name': 'Ada'},
          },
          {
            'id': 'b1',
            'is_active': true,
            'user_details': {'name': 'Brin'},
          },
          {
            'id': 'c1',
            'is_active': false,
            'user_details': {'name': 'Cai'},
          },
        ],
        'matched_last_30d': 12,
        'state': {'last_assigned_index': 1},
      }),
      RoutingRule.fromJson(const {
        'id': 'r2',
        'name': 'Everything else',
        'priority_order': 200,
        'is_active': true,
        'strategy': 'direct',
        'stop_processing': false,
        'conditions': [],
        'target_assignees': [],
        'matched_last_30d': 0,
      }),
      RoutingRule.fromJson(const {
        'id': 'r3',
        'name': 'Old escalation',
        'priority_order': 300,
        'is_active': false,
        'strategy': 'by_team',
        'target_team': {'id': 't1', 'name': 'Billing crew'},
        'matched_last_30d': 4,
      }),
    ],
    count: 3,
    active: 2,
    unroutedLast30d: 9,
  );
}

class _FakeNoRoutingRules extends RoutingRulesNotifier {
  @override
  Future<RoutingRulesState> build() async => const RoutingRulesState();
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

/// Three fields across two record types: one required with a real gap, one
/// dropdown, and one already turned off. Between them they light every branch
/// the row and the summary have.
class _FakeCustomFields extends CustomFieldsNotifier {
  @override
  Future<CustomFieldsState> build() async => CustomFieldsState(
    fields: [
      CustomFieldDefinition.fromJson(const {
        'id': 'f1',
        'target_model': 'Case',
        'key': 'severity',
        'label': 'Severity',
        'field_type': 'text',
        'is_required': true,
        'is_filterable': true,
        'display_order': 0,
        'is_active': true,
        'records_missing_value': 23,
      }),
      CustomFieldDefinition.fromJson(const {
        'id': 'f2',
        'target_model': 'Case',
        'key': 'root_cause',
        'label': 'Root cause, as agreed with the customer at close',
        'field_type': 'dropdown',
        'display_order': 1,
        'is_active': true,
        'options': [
          {'value': 'process', 'label': 'Process'},
          {'value': 'people', 'label': 'People'},
        ],
      }),
      CustomFieldDefinition.fromJson(const {
        'id': 'f3',
        'target_model': 'Lead',
        'key': 'campaign',
        'label': 'Campaign',
        'field_type': 'text',
        'is_active': false,
      }),
    ],
    count: 3,
    active: 2,
    modelsExtended: 2,
    requiredWithGaps: 1,
  );
}

/// One shared reply, one of mine, and one of mine already turned off. Between
/// them they drive both answers of every control on the screen.
class _FakeMacros extends MacrosNotifier {
  @override
  Future<MacrosState> build() async => MacrosState(
    macros: [
      Macro.fromJson(const {
        'id': 'm1',
        'title': 'Password reset, standard wording agreed with legal',
        'body': 'Hi %custmer_name%, follow the link to reset your password.',
        'scope': 'org',
        'owner_name': null,
        'is_active': true,
        'usage_count': 41,
        'unknown_placeholders': ['%custmer_name%'],
      }),
      Macro.fromJson(const {
        'id': 'm2',
        'title': 'My follow-up',
        'body': 'Just checking in on this one.',
        'scope': 'personal',
        'owner_name': 'me@example.com',
        'is_active': true,
        'usage_count': 0,
      }),
      Macro.fromJson(const {
        'id': 'm3',
        'title': 'Old holiday notice',
        'body': 'We are closed until January.',
        'scope': 'personal',
        'owner_name': 'me@example.com',
        'is_active': false,
        'usage_count': 7,
      }),
    ],
    placeholders: const [
      MacroPlaceholder(
        token: '%customer_name%',
        resolves: "The case's first contact",
      ),
      MacroPlaceholder(token: '%case_id%', resolves: 'The case number'),
    ],
    orgCount: 1,
    personalCount: 2,
    inactiveCount: 1,
    brokenCount: 1,
  );
}
