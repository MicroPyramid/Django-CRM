import 'dart:convert';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/screens/accounts/account_detail_screen.dart';
import 'package:bottle_crm/screens/accounts/account_form_screen.dart';
import 'package:bottle_crm/screens/contacts/contact_detail_screen.dart';
import 'package:bottle_crm/screens/contacts/contact_form_screen.dart';
import 'package:bottle_crm/screens/deals/deal_detail_screen.dart';
import 'package:bottle_crm/screens/invoices/invoice_detail_screen.dart';
import 'package:bottle_crm/screens/leads/lead_detail_screen.dart';
import 'package:bottle_crm/screens/tasks/task_detail_screen.dart';
import 'package:bottle_crm/screens/tickets/ticket_detail_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:bottle_crm/widgets/common/custom_fields_display.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// Custom fields on every record the phone opens: one shared display on the
/// seven detail screens, and the inputs on the contact and account forms and
/// the invoice's edit sheet. The API is faked per route; anything else a
/// screen asks for answers 404, which every one of them already survives.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Map<String, http.Response Function(http.Request)> routes;
  late List<http.Request> sent;

  setUp(() {
    sent = [];
    routes = {};
    ApiService().setClientForTesting(
      MockClient((request) async {
        sent.add(request);
        return routes['${request.method} ${request.url.path}']?.call(request) ??
            http.Response('{}', 404);
      }),
    );
  });

  tearDown(() => ApiService().setClientForTesting(http.Client()));

  String path(String url) => Uri.parse(url).path;

  /// The writes to [url] alone: the create forms also post duplicate checks.
  Iterable<http.Request> writes(String method, String url) =>
      sent.where((r) => r.method == method && r.url.path == path(url));

  void answer(String method, String url, Object body, {int status = 200}) {
    routes['$method ${path(url)}'] = (_) =>
        http.Response(jsonEncode(body), status);
  }

  List<Map<String, dynamic>> definitions(String target) => [
    {
      'id': 'f1',
      'target_model': target,
      'key': 'budget',
      'label': 'Budget',
      'field_type': 'number',
      'display_order': 0,
    },
    {
      'id': 'f2',
      'target_model': target,
      'key': 'tier',
      'label': 'Tier',
      'field_type': 'dropdown',
      'options': [
        {'value': 'gold', 'label': 'Gold'},
      ],
      'display_order': 1,
    },
    {
      'id': 'f3',
      'target_model': target,
      'key': 'possession_by',
      'label': 'Possession by',
      'field_type': 'date',
      'display_order': 2,
    },
  ];

  const values = {'budget': 1500000.0, 'tier': 'gold'};

  /// Pushed over a home page, so a form that pops after saving has somewhere
  /// to go. Tall enough that every card on a detail screen is built.
  Future<void> open(WidgetTester tester, Widget screen) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(800, 5000);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final router = GoRouter(
      initialLocation: '/',
      routes: [
        GoRoute(
          path: '/',
          builder: (_, _) => const Scaffold(body: Text('home')),
        ),
        GoRoute(path: '/here', builder: (_, _) => screen),
      ],
    );
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp.router(theme: AppTheme.light, routerConfig: router),
      ),
    );
    router.push('/here');
    await tester.pumpAndSettle();
  }

  Finder inBlock(Finder finder) =>
      find.descendant(of: find.byType(CustomFieldsDisplay), matching: finder);

  void expectShown() {
    expect(find.byType(CustomFieldsDisplay), findsOneWidget);
    expect(inBlock(find.text('BUDGET')), findsOneWidget);
    expect(inBlock(find.text('1,500,000')), findsOneWidget);
    expect(inBlock(find.text('Gold')), findsOneWidget);
    // A field the org tracks and this record leaves empty still shows.
    expect(inBlock(find.text('POSSESSION BY')), findsOneWidget);
    expect(inBlock(find.text('Not set')), findsOneWidget);
  }

  void expectHidden() {
    expect(find.byType(CustomFieldsDisplay), findsNothing);
    expect(find.text('BUDGET'), findsNothing);
  }

  /// Each screen, its detail route, and the body that route answers with.
  final screens =
      <
        (
          String,
          Widget,
          String,
          Map<String, dynamic> Function(List<Map<String, dynamic>>),
        )
      >[
        (
          'lead',
          const LeadDetailScreen(leadId: 'l1'),
          '${ApiConfig.leads}l1/',
          (defs) => {
            'lead_obj': {
              'id': 'l1',
              'first_name': 'Maya',
              'last_name': 'Rao',
              'title': 'Flat enquiry',
              'status': 'assigned',
              'created_at': '2026-10-01T09:00:00Z',
              'custom_fields': values,
            },
            'custom_field_definitions': defs,
          },
        ),
        (
          'deal',
          const DealDetailScreen(dealId: 'd1'),
          '${ApiConfig.opportunities}d1/',
          (defs) => {
            'opportunity_obj': {
              'id': 'd1',
              'name': 'Harbour flat',
              'stage': 'PROSPECTING',
              'created_at': '2026-10-01T09:00:00Z',
              'custom_fields': values,
            },
            'custom_field_definitions': defs,
          },
        ),
        (
          'task',
          const TaskDetailScreen(taskId: 't1'),
          '${ApiConfig.tasks}t1/',
          (defs) => {
            'task_obj': {
              'id': 't1',
              'title': 'Call back',
              'status': 'New',
              'priority': 'Medium',
              'created_at': '2026-10-01T09:00:00Z',
              'custom_fields': values,
            },
            'custom_field_definitions': defs,
          },
        ),
        (
          'contact',
          const ContactDetailScreen(contactId: 'c1'),
          '${ApiConfig.contacts}c1/',
          (defs) => {
            'contact_obj': {
              'id': 'c1',
              'first_name': 'Ada',
              'last_name': 'Lovelace',
              'custom_fields': values,
            },
            'custom_field_definitions': defs,
          },
        ),
        (
          'account',
          const AccountDetailScreen(accountId: 'a1'),
          '${ApiConfig.accounts}a1/',
          (defs) => {
            'account_obj': {
              'id': 'a1',
              'name': 'Northwind',
              'custom_fields': values,
            },
            'custom_field_definitions': defs,
          },
        ),
        (
          'ticket',
          const TicketDetailScreen(ticketId: 'k1'),
          ApiConfig.ticketDetail('k1'),
          (defs) => {
            'cases_obj': {
              'id': 'k1',
              'name': 'Printer on fire',
              'status': 'New',
              'priority': 'Normal',
              'created_at': '2026-10-01T09:00:00Z',
              'custom_fields': values,
            },
            'custom_field_definitions': defs,
          },
        ),
        (
          'invoice',
          const InvoiceDetailScreen(invoiceId: 'i1'),
          ApiConfig.invoice('i1'),
          (defs) => {
            'invoice': {
              'id': 'i1',
              'invoice_number': 'INV-1',
              'invoice_title': 'Retainer',
              'status': 'Sent',
              'currency': 'USD',
              'custom_fields': values,
            },
            'custom_field_definitions': defs,
          },
        ),
      ];

  group('the shared display on every detail screen', () {
    for (final (name, screen, url, body) in screens) {
      testWidgets('$name shows every active field, filled or not', (
        tester,
      ) async {
        answer('GET', url, body(definitions(name)));
        await open(tester, screen);
        expect(tester.takeException(), isNull);
        expectShown();
      });

      testWidgets('$name shows no block when the org has no fields', (
        tester,
      ) async {
        answer('GET', url, body(const []));
        await open(tester, screen);
        expect(tester.takeException(), isNull);
        expectHidden();
      });
    }
  });

  group('the contact form', () {
    const required = {
      'id': 'f9',
      'target_model': 'Contact',
      'key': 'licence_no',
      'label': 'Licence number',
      'field_type': 'text',
      'is_required': true,
    };

    void definitionsAnswer() =>
        routes['GET ${path(ApiConfig.customFieldDefinitions)}'] = (request) {
          expect(request.url.queryParameters['target_model'], 'Contact');
          return http.Response(
            jsonEncode({
              'definitions': [required],
            }),
            200,
          );
        };

    Future<void> fillName(WidgetTester tester) async {
      await tester.enterText(
        find.widgetWithText(TextFormField, 'First name'),
        'Ada',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Last name'),
        'Lovelace',
      );
    }

    Future<void> create(WidgetTester tester) async {
      final button = find.widgetWithText(FilledButton, 'Create contact');
      await tester.ensureVisible(button);
      await tester.pumpAndSettle();
      await tester.tap(button);
      await tester.pumpAndSettle();
    }

    testWidgets('a required contact field is sent on create', (tester) async {
      definitionsAnswer();
      answer('POST', ApiConfig.contacts, {'id': 'c9'});
      await open(tester, const ContactFormScreen());

      await fillName(tester);
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Licence number *'),
        'RE-1234',
      );
      await create(tester);

      final body =
          jsonDecode(writes('POST', ApiConfig.contacts).single.body)
              as Map<String, dynamic>;
      expect(body['custom_fields'], {'licence_no': 'RE-1234'});
      expect(body['first_name'], 'Ada');
    });

    testWidgets('an empty required field is named beside it, and nothing '
        'is sent', (tester) async {
      definitionsAnswer();
      answer('POST', ApiConfig.contacts, {'id': 'c9'});
      await open(tester, const ContactFormScreen());

      await fillName(tester);
      await create(tester);

      expect(writes('POST', ApiConfig.contacts), isEmpty);
      // Beside the field, and in the snackbar.
      expect(find.text('Licence number is required'), findsNWidgets(2));

      await tester.enterText(
        find.widgetWithText(TextFormField, 'Licence number *'),
        'RE-1',
      );
      await tester.pump();
      expect(find.text('Licence number is required'), findsOneWidget);
    });

    testWidgets('an edit reads its fields from the detail response and '
        'sends them back with the change', (tester) async {
      answer('GET', '${ApiConfig.contacts}c1/', {
        'contact_obj': {
          'id': 'c1',
          'first_name': 'Ada',
          'last_name': 'Lovelace',
          'custom_fields': {'licence_no': 'RE-1', 'retired_key': 'kept'},
        },
        'custom_field_definitions': [required],
      });
      answer('PATCH', '${ApiConfig.contacts}c1/', {'error': false});
      await open(tester, const ContactFormScreen(contactId: 'c1'));

      // No separate definitions call: the detail response carried them.
      expect(
        sent.where((r) => r.url.path == path(ApiConfig.customFieldDefinitions)),
        isEmpty,
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Licence number *'),
        'RE-2',
      );
      final button = find.widgetWithText(FilledButton, 'Save changes');
      await tester.ensureVisible(button);
      await tester.tap(button);
      await tester.pumpAndSettle();

      final patch = writes('PATCH', '${ApiConfig.contacts}c1/').single;
      expect(jsonDecode(patch.body)['custom_fields'], {
        'licence_no': 'RE-2',
        'retired_key': 'kept',
      });
    });
  });

  testWidgets('the account form sends what is typed into its fields', (
    tester,
  ) async {
    routes['GET ${path(ApiConfig.customFieldDefinitions)}'] = (request) {
      expect(request.url.queryParameters['target_model'], 'Account');
      return http.Response(
        jsonEncode({
          'definitions': [
            {
              'id': 'f1',
              'target_model': 'Account',
              'key': 'tier',
              'label': 'Tier',
              'field_type': 'dropdown',
              'options': [
                {'value': 'gold', 'label': 'Gold'},
              ],
            },
          ],
        }),
        200,
      );
    };
    answer('POST', ApiConfig.accounts, {'id': 'a9'});
    await open(tester, const AccountFormScreen());

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Account name'),
      'Northwind',
    );
    await tester.tap(find.text('Select…'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Gold'));
    await tester.pumpAndSettle();
    final button = find.widgetWithText(FilledButton, 'Create account');
    await tester.ensureVisible(button);
    await tester.tap(button);
    await tester.pumpAndSettle();

    final post = writes('POST', ApiConfig.accounts).single;
    expect(jsonDecode(post.body)['custom_fields'], {'tier': 'gold'});
  });

  group('the invoice edit sheet', () {
    setUp(() {
      answer('GET', ApiConfig.invoice('i1'), {
        'invoice': {
          'id': 'i1',
          'invoice_number': 'INV-1',
          'invoice_title': 'Retainer',
          'status': 'Sent',
          'currency': 'USD',
          'custom_fields': {'po_ref': 'PO-7'},
        },
        'custom_field_definitions': [
          {
            'id': 'f1',
            'target_model': 'Invoice',
            'key': 'po_ref',
            'label': 'PO reference',
            'field_type': 'text',
            'is_required': true,
          },
        ],
      });
      answer('PUT', ApiConfig.invoice('i1'), {'error': false});
    });

    testWidgets('sends the fields and nothing else', (tester) async {
      await open(tester, const InvoiceDetailScreen(invoiceId: 'i1'));
      expect(find.text('PO-7'), findsOneWidget);

      await tester.tap(find.text('Edit fields'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.widgetWithText(TextFormField, 'PO reference *'),
        'PO-8',
      );
      await tester.tap(find.text('Save'));
      await tester.pumpAndSettle();

      final put = writes('PUT', ApiConfig.invoice('i1')).single;
      expect(jsonDecode(put.body), {
        'custom_fields': {'po_ref': 'PO-8'},
      });
      expect(find.text('Fields saved'), findsOneWidget);
    });

    testWidgets('will not save a required field emptied', (tester) async {
      await open(tester, const InvoiceDetailScreen(invoiceId: 'i1'));
      await tester.tap(find.text('Edit fields'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.widgetWithText(TextFormField, 'PO reference *'),
        '',
      );
      await tester.tap(find.text('Save'));
      await tester.pumpAndSettle();

      expect(writes('PUT', ApiConfig.invoice('i1')), isEmpty);
      expect(find.text('PO reference is required'), findsOneWidget);
      expect(find.text('Edit fields'), findsWidgets);
    });

    testWidgets('the server refusal reaches the person', (tester) async {
      answer('PUT', ApiConfig.invoice('i1'), {
        'error': true,
        'errors': {
          'custom_fields': {'po_ref': 'must be one of the allowed values'},
        },
      }, status: 400);
      await open(tester, const InvoiceDetailScreen(invoiceId: 'i1'));
      await tester.tap(find.text('Edit fields'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Save'));
      await tester.pumpAndSettle();

      expect(
        find.text('Po ref: must be one of the allowed values'),
        findsOneWidget,
      );
    });
  });
}
