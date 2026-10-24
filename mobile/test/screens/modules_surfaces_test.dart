import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/providers/accounts_provider.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:bottle_crm/providers/deal_pipelines_provider.dart';
import 'package:bottle_crm/providers/deals_provider.dart';
import 'package:bottle_crm/providers/invoice_extras_provider.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/providers/notifications_provider.dart';
import 'package:bottle_crm/providers/org_modules_provider.dart';
import 'package:bottle_crm/providers/solutions_provider.dart';
import 'package:bottle_crm/providers/tickets_provider.dart';
import 'package:bottle_crm/screens/solutions/solutions_list_screen.dart';
import 'package:bottle_crm/providers/web_forms_provider.dart';
import 'package:bottle_crm/data/models/models.dart';
import 'package:bottle_crm/data/models/account.dart';
import 'package:bottle_crm/screens/accounts/account_detail_screen.dart';
import 'package:bottle_crm/screens/deals/deal_detail_screen.dart';
import 'package:bottle_crm/screens/invoices/products_list_screen.dart';
import 'package:bottle_crm/screens/notifications/notifications_screen.dart';
import 'package:bottle_crm/screens/settings/automation/automation_rule_screen.dart';
import 'package:bottle_crm/screens/settings/automation/automation_rules_screen.dart';
import 'package:bottle_crm/screens/settings/custom_field_form_sheet.dart';
import 'package:bottle_crm/screens/settings/web_forms_screen.dart';
import 'package:bottle_crm/screens/tickets/ticket_detail_screen.dart';
import 'package:bottle_crm/services/automation_text.dart';
import 'package:bottle_crm/widgets/cards/deal_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../support/automation_fixtures.dart';
import '../support/modules_fixtures.dart';

/// The record screens and other copy that follow a switched-off module.
/// Hiding is UX only; the API refuses the module's requests regardless.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  void usePhone(WidgetTester tester, {double textScale = 1.0}) {
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    tester.platformDispatcher.textScaleFactorTestValue = textScale;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  }

  FakeOrgModules modules(List<String> off) =>
      FakeOrgModules(() async => modulesAnswer(off: off));

  List<Override> moduleOverrides(List<String> off, {bool admin = true}) =>
      modulesOverrides(modules(off), admin: admin);

  group('account', () {
    Widget app(List<String> off) => ProviderScope(
      key: UniqueKey(),
      overrides: [
        ...moduleOverrides(off),
        accountsProvider.overrideWith(_FakeAccounts.new),
      ],
      child: const MaterialApp(home: AccountDetailScreen(accountId: 'a1')),
    );

    testWidgets(
      'the account hides deals, tickets, tasks, their figures and the statement by module',
      (tester) async {
        usePhone(tester);
        await tester.pumpWidget(app(const []));
        await tester.pumpAndSettle();
        expect(find.text('Open pipeline'), findsOneWidget);
        expect(find.text('Open tickets'), findsOneWidget);
        expect(find.textContaining('Deals ('), findsOneWidget);
        expect(find.textContaining('Tickets ('), findsOneWidget);
        expect(find.textContaining('Tasks ('), findsOneWidget);
        expect(find.byTooltip('Statement'), findsOneWidget);

        await tester.pumpWidget(
          app(const ['deals', 'tickets', 'tasks', 'invoices']),
        );
        await tester.pumpAndSettle();
        expect(find.text('Open pipeline'), findsNothing);
        expect(find.text('Won'), findsNothing);
        expect(find.text('Open tickets'), findsNothing);
        expect(find.textContaining('Deals ('), findsNothing);
        expect(find.textContaining('Tickets ('), findsNothing);
        expect(find.textContaining('Tasks ('), findsNothing);
        expect(find.byTooltip('Statement'), findsNothing);
        expect(find.textContaining('Contacts ('), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );

    testWidgets('one module off keeps the other figures', (tester) async {
      usePhone(tester);
      await tester.pumpWidget(app(const ['tickets']));
      await tester.pumpAndSettle();
      expect(find.text('Open pipeline'), findsOneWidget);
      expect(find.text('Open tickets'), findsNothing);
      expect(find.textContaining('Deals ('), findsOneWidget);
    });

    for (final scale in [1.0, 1.3, 1.5]) {
      testWidgets(
        'the delete dialog says what goes with the account, x$scale',
        (tester) async {
          usePhone(tester, textScale: scale);
          await tester.pumpWidget(app(const []));
          await tester.pumpAndSettle();
          await tester.tap(find.byIcon(LucideIcons.trash2));
          await tester.pumpAndSettle();
          expect(
            find.text(
              'Deleting Northwind cannot be undone. Its deals and tickets are '
              'deleted with it, and its contacts lose the link.',
            ),
            findsOneWidget,
          );
          expect(tester.takeException(), isNull);
        },
      );
    }
  });

  group('deal', () {
    Widget app(List<String> off, Deal deal) {
      final router = GoRouter(
        initialLocation: '/deals/d1',
        routes: [
          GoRoute(
            path: '/deals/:id',
            builder: (_, s) =>
                DealDetailScreen(dealId: s.pathParameters['id']!),
          ),
        ],
      );
      return ProviderScope(
        key: UniqueKey(),
        overrides: [
          ...moduleOverrides(off),
          dealsProvider.overrideWith(() => _FakeDeals(deal)),
          dealPipelinesProvider.overrideWith(_FakePipelines.new),
        ],
        child: MaterialApp.router(routerConfig: router),
      );
    }

    final won = Deal.fromJson({
      'id': 'd1',
      'name': 'Renewal',
      'stage': 'SIGNED',
      'stage_label': 'Signed',
      'stage_kind': 'won',
      'amount': '300',
      'currency': 'EUR',
      'can_delete': true,
      'account': {'id': 'acc-1', 'name': 'Northwind'},
      'created_at': '2026-09-01T00:00:00Z',
    });

    testWidgets(
      'the deal hides its invoice and estimate actions while Invoices is off',
      (tester) async {
        usePhone(tester);
        await tester.pumpWidget(app(const [], won));
        await tester.pumpAndSettle();
        expect(find.text('Create invoice'), findsOneWidget);
        await tester.tap(find.byIcon(LucideIcons.moreVertical));
        await tester.pumpAndSettle();
        expect(find.text('Create estimate'), findsOneWidget);
        expect(find.text('Create invoice'), findsNWidgets(2));

        await tester.pumpWidget(app(const ['invoices'], won));
        await tester.pumpAndSettle();
        expect(find.text('Create invoice'), findsNothing);
        await tester.tap(find.byIcon(LucideIcons.moreVertical));
        await tester.pumpAndSettle();
        expect(find.text('Edit Deal'), findsOneWidget);
        expect(find.text('Create estimate'), findsNothing);
        expect(find.text('Create invoice'), findsNothing);
        expect(tester.takeException(), isNull);
      },
    );
  });

  group('deal cards', () {
    Widget app(List<String> off) => ProviderScope(
      key: UniqueKey(),
      overrides: [
        ...moduleOverrides(off),
        usersProvider.overrideWithValue(const []),
      ],
      child: MaterialApp(
        theme: AppTheme.light,
        home: Scaffold(
          body: ListView(
            children: [
              DealCard(
                deal: Deal.fromJson({
                  'id': 'x',
                  'name': 'Renewal',
                  'stage': 'DEMO_BOOKED',
                  'stage_label': 'Demo booked',
                  'stage_kind': 'open',
                  'amount': '100',
                  'next_activity': null,
                }),
              ),
            ],
          ),
        ),
      ),
    );

    testWidgets('deal cards show no next step while Tasks is off', (
      tester,
    ) async {
      usePhone(tester);
      await tester.pumpWidget(app(const []));
      await tester.pumpAndSettle();
      expect(find.text('No next step'), findsOneWidget);
      await tester.pumpWidget(app(const ['tasks']));
      await tester.pumpAndSettle();
      expect(find.text('No next step'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  });

  group('articles', () {
    Widget app(List<String> off) => ProviderScope(
      key: UniqueKey(),
      overrides: [
        ...moduleOverrides(off),
        solutionsProvider.overrideWith(_OneArticle.new),
      ],
      child: const MaterialApp(home: SolutionsListScreen()),
    );

    testWidgets('the linked-ticket count shows only while Tickets is on', (
      tester,
    ) async {
      usePhone(tester);
      await tester.pumpWidget(app(const []));
      await tester.pumpAndSettle();
      expect(find.text('Reset a password'), findsOneWidget);
      expect(find.text('0 linked'), findsOneWidget);

      await tester.pumpWidget(app(const ['tickets']));
      await tester.pumpAndSettle();
      expect(find.text('Reset a password'), findsOneWidget);
      expect(find.textContaining('linked'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  });

  group('ticket', () {
    Widget app(List<String> off) => ProviderScope(
      key: UniqueKey(),
      overrides: [
        ...moduleOverrides(off),
        ticketsProvider.overrideWith(_FakeTickets.new),
        usersProvider.overrideWithValue(const []),
        tagsProvider.overrideWithValue(const []),
        accountOptionsProvider.overrideWithValue(const []),
      ],
      child: MaterialApp.router(
        theme: AppTheme.light,
        routerConfig: GoRouter(
          initialLocation: '/here',
          routes: [
            GoRoute(
              path: '/here',
              builder: (_, _) => const TicketDetailScreen(ticketId: 't1'),
            ),
          ],
        ),
      ),
    );

    testWidgets(
      'the ticket hides time while Timesheet is off and articles while the knowledge base is off',
      (tester) async {
        usePhone(tester);
        await tester.pumpWidget(app(const []));
        await tester.pumpAndSettle();
        expect(find.text('TIME TRACKING'), findsOneWidget);
        expect(find.text('SOLUTIONS'), findsOneWidget);

        await tester.pumpWidget(app(const ['timesheet']));
        await tester.pumpAndSettle();
        expect(find.text('TIME TRACKING'), findsNothing);
        expect(find.text('SOLUTIONS'), findsOneWidget);

        await tester.pumpWidget(app(const ['knowledge_base']));
        await tester.pumpAndSettle();
        expect(find.text('TIME TRACKING'), findsOneWidget);
        expect(find.text('SOLUTIONS'), findsNothing);
        expect(tester.takeException(), isNull);
      },
    );
  });

  group('products, notifications and web forms', () {
    Widget products(List<String> off) => ProviderScope(
      key: UniqueKey(),
      overrides: [
        ...moduleOverrides(off),
        productsProvider.overrideWith(_FakeProducts.new),
      ],
      child: const MaterialApp(home: ProductsListScreen()),
    );

    testWidgets('products drop their invoice captions while Invoices is off', (
      tester,
    ) async {
      usePhone(tester);
      await tester.pumpWidget(products(const []));
      await tester.pumpAndSettle();
      expect(find.text('on 3 invoices'), findsOneWidget);
      await tester.pumpWidget(products(const ['invoices']));
      await tester.pumpAndSettle();
      expect(find.textContaining('invoice'), findsNothing);
      expect(tester.takeException(), isNull);
    });

    testWidgets(
      'the notifications empty state drops tickets while they are off',
      (tester) async {
        usePhone(tester);
        Widget app(List<String> off) => ProviderScope(
          key: UniqueKey(),
          overrides: [
            ...moduleOverrides(off),
            notificationsProvider.overrideWith(_EmptyNotifications.new),
          ],
          child: const MaterialApp(home: NotificationsScreen()),
        );
        await tester.pumpWidget(app(const []));
        await tester.pumpAndSettle();
        expect(find.textContaining('CRM ticket activity'), findsOneWidget);
        await tester.pumpWidget(app(const ['tickets']));
        await tester.pumpAndSettle();
        expect(
          find.text(
            'Notifications arrive for automation rules and updates from '
            'BottleCRM Support.',
          ),
          findsOneWidget,
        );
      },
    );

    testWidgets('custom fields offer only the targets that are on', (
      tester,
    ) async {
      usePhone(tester);
      await tester.pumpWidget(
        ProviderScope(
          key: UniqueKey(),
          overrides: moduleOverrides(const ['tickets', 'invoices']),
          child: MaterialApp(
            home: Builder(
              builder: (context) => TextButton(
                onPressed: () => showCustomFieldFormSheet(context, null),
                child: const Text('open'),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Accounts').last);
      await tester.pumpAndSettle();
      expect(find.text('Leads'), findsOneWidget);
      expect(find.text('Deals'), findsOneWidget);
      expect(find.text('Contacts'), findsOneWidget);
      expect(find.text('Tickets'), findsNothing);
      expect(find.text('Invoices'), findsNothing);
      expect(find.text('Estimates'), findsNothing);
      expect(find.text('Recurring invoices'), findsNothing);
    });

    testWidgets('a custom field target that goes off falls back to one on', (
      tester,
    ) async {
      usePhone(tester);
      var off = <String>[];
      final fake = FakeOrgModules(() async => modulesAnswer(off: off));
      await tester.pumpWidget(
        ProviderScope(
          key: UniqueKey(),
          overrides: modulesOverrides(fake),
          child: MaterialApp(
            home: Builder(
              builder: (context) => TextButton(
                onPressed: () => showCustomFieldFormSheet(context, null),
                child: const Text('open'),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Accounts').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Leads'));
      await tester.pumpAndSettle();

      final container = ProviderScope.containerOf(
        tester.element(find.byType(TextField).first),
      );
      off = ['leads'];
      container.invalidate(orgModulesProvider);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(find.text('Leads'), findsNothing);
      expect(find.text('Accounts'), findsOneWidget);
    });

    Widget webForms(List<String> off) => ProviderScope(
      key: UniqueKey(),
      overrides: [
        ...moduleOverrides(off),
        webFormsProvider.overrideWith(_NoWebForms.new),
      ],
      child: const MaterialApp(home: WebFormsScreen()),
    );

    testWidgets('web forms offer only the targets that are on', (tester) async {
      usePhone(tester);
      await tester.pumpWidget(webForms(const ['tickets']));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('New web form'));
      await tester.pumpAndSettle();
      expect(find.text('A lead'), findsOneWidget);
      expect(find.text('A ticket'), findsNothing);
      expect(find.text('Create and add fields'), findsOneWidget);
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();

      await tester.pumpWidget(webForms(const ['leads', 'tickets']));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('New web form'));
      await tester.pumpAndSettle();
      expect(
        find.text(
          'Web forms create leads or tickets, and both are switched off. '
          'An admin can switch one on in Apps settings.',
        ),
        findsOneWidget,
      );
      expect(find.text('Create and add fields'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  });

  group('automation', () {
    AutomationRuleRow row(String object, String status) => AutomationRuleRow(
      id: autoRuleId,
      name: 'Rule one',
      objectKey: object,
      trigger: autoTrigger.copy(),
      status: status,
      statusText: status == 'paused' ? 'Paused: Pipeline is switched off' : '',
    );

    test('only a paused rule on a module object is paused by its module', () {
      final off = modulesAnswer(off: const ['deals']);
      expect(pausedByModule(row('deal', 'paused'), off), isTrue);
      expect(pausedByModule(row('deal', 'on'), off), isFalse);
      expect(pausedByModule(row('contact', 'paused'), off), isFalse);
      expect(pausedByModule(row('lead', 'paused'), off), isFalse);
      expect(pausedByModule(row('deal', 'paused'), null), isFalse);
    });

    List<Override> overrides(List<String> off, AutomationRuleRow r) => [
      ...moduleOverrides(off),
      automationCatalogueProvider.overrideWith((ref) async => autoCatalogue),
      automationRulesProvider.overrideWith(
        () => _OneRule(AutomationRulesAnswer(rules: [r])),
      ),
      automationRuleProvider.overrideWith((ref, id) async => autoRule()),
    ];

    Widget app(Widget screen, List<Override> o) => ProviderScope(
      key: UniqueKey(),
      overrides: o,
      child: MaterialApp.router(
        theme: AppTheme.light,
        routerConfig: GoRouter(
          initialLocation: '/here',
          routes: [GoRoute(path: '/here', builder: (_, _) => screen)],
        ),
      ),
    );

    const note =
        '"Rule one": Paused: Pipeline is switched off. It runs again once '
        'that module is switched back on.';

    testWidgets('a rule paused by its module says so and opens read-only', (
      tester,
    ) async {
      usePhone(tester);
      await tester.pumpWidget(
        app(
          const AutomationRulesScreen(),
          overrides(const ['deals'], row('deal', 'paused')),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text(note), findsOneWidget);

      await tester.pumpWidget(
        app(
          const AutomationRuleScreen(ruleId: autoRuleId),
          overrides(const ['deals'], row('deal', 'paused')),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text(note), findsOneWidget);
      expect(find.widgetWithText(FilledButton, 'Save'), findsNothing);
      expect(find.widgetWithText(OutlinedButton, 'Save'), findsNothing);
      expect(find.text('Try it on a record'), findsNothing);
      expect(find.text('Switch off'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.text('Delete rule'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      expect(find.text('Delete rule'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets(
      'a paused rule with its module on keeps the old note and Save',
      (tester) async {
        usePhone(tester);
        await tester.pumpWidget(
          app(
            const AutomationRuleScreen(ruleId: autoRuleId),
            overrides(const [], row('deal', 'paused')),
          ),
        );
        await tester.pumpAndSettle();
        expect(find.text(note), findsNothing);
        await tester.scrollUntilVisible(
          find.text('Delete rule'),
          300,
          scrollable: find.byType(Scrollable).first,
        );
        expect(find.text('Save'), findsOneWidget);
      },
    );
  });
}

class _FakeAccounts extends AccountsNotifier {
  @override
  Future<AccountsListData> build() async => const AccountsListData();

  @override
  Future<Account?> getAccount(String id, {void Function()? onNotFound}) async =>
      Account.fromJson(canDelete: true, {
        'id': id,
        'name': 'Northwind',
        'currency': 'USD',
        'contacts': [
          {'id': 'c1', 'first_name': 'Ada', 'last_name': 'Lovelace'},
        ],
        'opportunities': [
          {'id': 'd1', 'name': 'Renewal'},
        ],
        'cases': [
          {'id': 't1', 'name': 'Printer'},
        ],
        'tasks': [
          {'id': 'k1', 'title': 'Call'},
        ],
        'rollups': {
          'won_amount': '500.00',
          'won_count': 1,
          'open_pipeline': '10.00',
          'open_deal_count': 1,
          'overdue_amount': '0',
          'open_tickets': 2,
          'by_currency': [
            {
              'currency': 'USD',
              'won_amount': '500.00',
              'open_pipeline': '10.00',
              'overdue_amount': '0',
            },
          ],
        },
      });
}

class _FakeDeals extends DealsNotifier {
  _FakeDeals(this.deal);

  final Deal deal;

  @override
  Future<DealsListData> build() async => const DealsListData();

  @override
  Future<DealDetail?> getDealDetail(
    String id, {
    void Function()? onNotFound,
  }) async => DealDetail(deal: deal);
}

class _FakePipelines extends DealPipelinesNotifier {
  @override
  Future<List<DealPipeline>> build() async => const [];
}

class _FakeTickets extends TicketsNotifier {
  @override
  Future<TicketsListData> build() async =>
      TicketsListData(tickets: const [], totalCount: 0, hasMore: false);

  @override
  Future<TicketDetailResult?> getTicketDetail(String id) async =>
      TicketDetailResult(
        ticketObj: Ticket.fromJson({
          'id': id,
          'name': 'Printer on fire',
          'status': 'New',
          'priority': 'Normal',
          'created_at': '2026-09-01T09:00:00Z',
        }),
        activities: const [],
        commentPermission: true,
        approvalRule: const ApprovalRuleSummary(id: 'r1', name: 'Close check'),
        internalCommentIds: const {},
      );

  @override
  Future<TicketWatchers?> getWatchers(String id) async => const TicketWatchers(
    watchers: [],
    count: 0,
    isCurrentUserWatching: false,
  );

  @override
  Future<TicketTreeNode?> fetchTree(String id) async => null;

  @override
  Future<List<TimeEntry>> fetchTimeEntries(String id) async => const [];

  @override
  Future<TimeSummary?> fetchTimeSummary(String id) async => null;
}

class _FakeProducts extends ProductsNotifier {
  @override
  Future<List<Product>> build() async => [
    Product.fromJson({
      'id': 'p1',
      'name': 'Hosting',
      'price': '10.00',
      'currency': 'USD',
      'is_active': true,
      'used_on': 3,
    }),
  ];
}

class _EmptyNotifications extends NotificationsNotifier {
  @override
  Future<NotificationFeed> build() async => const NotificationFeed();
}

class _OneArticle extends SolutionsNotifier {
  @override
  SolutionsListData build() => SolutionsListData(
    solutions: [
      Solution.fromJson(const {
        'id': 's1',
        'title': 'Reset a password',
        'description': 'Steps',
        'case_count': 0,
      }),
    ],
  );
}

class _NoWebForms extends WebFormsNotifier {
  @override
  Future<WebFormsState> build() async => const WebFormsState();
}

class _OneRule extends AutomationRulesNotifier {
  _OneRule(this.answer);

  final AutomationRulesAnswer answer;

  @override
  Future<AutomationRulesAnswer> build() async => answer;
}
