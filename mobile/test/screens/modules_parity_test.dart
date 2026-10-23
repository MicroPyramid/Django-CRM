import 'package:bottle_crm/data/models/org_settings.dart';
import 'package:bottle_crm/providers/settings_provider.dart';
import 'package:bottle_crm/providers/webhooks_provider.dart';
import 'package:bottle_crm/screens/settings/organization_edit_screen.dart';
import 'package:bottle_crm/screens/settings/organization_screen.dart';
import 'package:bottle_crm/screens/settings/webhooks_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/modules_fixtures.dart';

/// Organization settings and the webhooks empty state follow the modules that
/// are switched off, as the web's do. With every module on the copy is the
/// copy these screens always had.
OrgSettings _org() => OrgSettings.fromJson({
  'id': 'org-1',
  'name': 'Acme',
  'timezone': 'UTC',
  'invoice_number_prefix': 'INV-',
  'estimate_number_prefix': 'EST-',
  'number_date_part': 'DAY',
  'number_padding': 4,
  'invoice_number_start': 1,
});

class _Org extends OrgSettingsNotifier {
  final List<Map<String, dynamic>> saved = [];

  @override
  Future<OrgSettings> build() async => _org();

  @override
  Future<String?> save(Map<String, dynamic> payload) async {
    saved.add(payload);
    return null;
  }
}

class _Hooks extends WebhooksNotifier {
  @override
  Future<WebhooksState> build() async => const WebhooksState(limit: 5);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // A tall phone builds the whole list at once, so a section is found by its
  // text rather than by scrolling to it.
  void usePhone(
    WidgetTester tester, {
    double textScale = 1.0,
    double height = 844,
  }) {
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = Size(390 * 3, height * 3);
    tester.platformDispatcher.textScaleFactorTestValue = textScale;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  }

  Future<_Org> pump(
    WidgetTester tester,
    Widget screen,
    List<String> off, {
    double textScale = 1.0,
    double height = 4000,
  }) async {
    usePhone(tester, textScale: textScale, height: height);
    final org = _Org();
    await tester.pumpWidget(
      ProviderScope(
        key: UniqueKey(),
        overrides: [
          ...modulesOverrides(
            FakeOrgModules(() async => modulesAnswer(off: off)),
          ),
          orgSettingsProvider.overrideWith(() => org),
          orgTimezonesProvider.overrideWith(
            (ref) async => const [
              TimezoneOption(name: 'UTC', offsetMinutes: 0),
            ],
          ),
          orgPacksProvider.overrideWith((ref) async => const <VerticalPack>[]),
          webhooksProvider.overrideWith(_Hooks.new),
        ],
        child: MaterialApp(home: screen),
      ),
    );
    await tester.pumpAndSettle();
    return org;
  }

  Future<void> scrollAll(WidgetTester tester) async {
    final list = find.byType(ListView).first;
    for (var i = 0; i < 12; i++) {
      await tester.drag(list, const Offset(0, -500));
      await tester.pump();
    }
    await tester.pumpAndSettle();
  }

  group('organization screen', () {
    testWidgets('Invoices off drops the invoice settings and copy', (
      tester,
    ) async {
      await pump(tester, const OrganizationScreen(), const ['invoices']);
      expect(find.textContaining('printed on every invoice'), findsNothing);
      expect(
        find.textContaining('Applied to new invoices and estimates'),
        findsNothing,
      );
      expect(
        find.textContaining('The default for new records that carry an amount'),
        findsOneWidget,
      );
      expect(find.text('INVOICE NUMBERS'), findsNothing);
      expect(find.text('New invoices'), findsNothing);
      expect(find.text('New estimates'), findsNothing);
      expect(find.text('BEHAVIOUR'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('Tickets off drops the two ticket settings', (tester) async {
      await pump(tester, const OrganizationScreen(), const ['tickets']);
      expect(find.text('BEHAVIOUR'), findsNothing);
      expect(find.text('Satisfaction surveys'), findsNothing);
      expect(find.text('Close child tickets with the parent'), findsNothing);
      expect(find.text('INVOICE NUMBERS'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('with every module on the settings and copy are unchanged', (
      tester,
    ) async {
      await pump(tester, const OrganizationScreen(), const []);
      expect(find.textContaining('printed on every invoice'), findsOneWidget);
      expect(
        find.text(
          'Applied to new invoices and estimates. Existing ones keep theirs.',
        ),
        findsOneWidget,
      );
      expect(find.text('INVOICE NUMBERS'), findsOneWidget);
      expect(find.text('BEHAVIOUR'), findsOneWidget);
      expect(find.text('Satisfaction surveys'), findsOneWidget);
      expect(
        find.textContaining(
          'A pack adds starter pipelines, tags, custom fields, products and '
          'sample records',
        ),
        findsOneWidget,
      );
    });

    testWidgets('the pack sentence names products only while they are used', (
      tester,
    ) async {
      await pump(tester, const OrganizationScreen(), const [
        'deals',
        'invoices',
      ]);
      expect(
        find.textContaining(
          'A pack adds starter pipelines, tags, custom fields and sample '
          'records',
        ),
        findsOneWidget,
      );
      // Products serve Pipeline or Invoices: one of them on keeps the word.
      await pump(tester, const OrganizationScreen(), const ['deals']);
      expect(
        find.textContaining('custom fields, products and'),
        findsOneWidget,
      );
    });

    for (final scale in [1.0, 1.3, 1.5]) {
      testWidgets('with Invoices and Tickets off fits at x$scale', (
        tester,
      ) async {
        await pump(
          tester,
          const OrganizationScreen(),
          const ['invoices', 'tickets'],
          textScale: scale,
          height: 844,
        );
        await scrollAll(tester);
        expect(tester.takeException(), isNull);
      });
    }
  });

  group('organization edit form', () {
    testWidgets('Invoices off drops the numbering fields and hint', (
      tester,
    ) async {
      await pump(tester, const OrganizationEditScreen(), const ['invoices']);
      expect(find.textContaining('Printed on every invoice'), findsNothing);
      expect(
        find.textContaining('The default for new records that carry an amount'),
        findsOneWidget,
      );
      expect(find.text('INVOICE NUMBERS'), findsNothing);
      expect(find.text('Invoice prefix'), findsNothing);
      expect(find.text('Estimate prefix'), findsNothing);
      expect(find.text('Counter digits'), findsNothing);
      expect(find.text('BEHAVIOUR'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('Tickets off drops both switches', (tester) async {
      await pump(tester, const OrganizationEditScreen(), const ['tickets']);
      expect(find.text('BEHAVIOUR'), findsNothing);
      expect(find.text('Satisfaction surveys'), findsNothing);
      expect(find.text('Close child tickets with the parent'), findsNothing);
      expect(find.text('INVOICE NUMBERS'), findsOneWidget);
      expect(find.text('Invoice prefix'), findsOneWidget);
    });

    testWidgets('with every module on the form is unchanged', (tester) async {
      await pump(tester, const OrganizationEditScreen(), const []);
      expect(find.textContaining('Printed on every invoice'), findsOneWidget);
      expect(find.text('INVOICE NUMBERS'), findsOneWidget);
      expect(find.text('Counter digits'), findsOneWidget);
      expect(find.text('BEHAVIOUR'), findsOneWidget);
      expect(find.text('Satisfaction surveys'), findsOneWidget);
    });

    testWidgets('saving with both off keeps the stored values', (tester) async {
      final org = await pump(tester, const OrganizationEditScreen(), const [
        'invoices',
        'tickets',
      ]);
      await tester.tap(find.text('Save changes'));
      await tester.pumpAndSettle();
      expect(org.saved, hasLength(1));
      expect(org.saved.single['invoice_number_prefix'], 'INV-');
      expect(org.saved.single['estimate_number_prefix'], 'EST-');
      expect(org.saved.single['number_padding'], 4);
      expect(org.saved.single['number_date_part'], 'DAY');
    });

    for (final scale in [1.0, 1.3, 1.5]) {
      testWidgets('with Invoices and Tickets off fits at x$scale', (
        tester,
      ) async {
        await pump(
          tester,
          const OrganizationEditScreen(),
          const ['invoices', 'tickets'],
          textScale: scale,
          height: 844,
        );
        await scrollAll(tester);
        expect(tester.takeException(), isNull);
      });
    }
  });

  group('webhooks empty state', () {
    String sentence(WidgetTester tester) => tester
        .widgetList<Text>(find.textContaining('A webhook posts'))
        .single
        .data!;

    testWidgets('names only the modules that are on', (tester) async {
      await pump(tester, const WebhooksScreen(), const []);
      expect(
        sentence(tester),
        'A webhook posts to a URL whenever a lead, deal, ticket or other '
        'record changes. Point one at Zapier, n8n, Slack or your own code.',
      );
      await pump(tester, const WebhooksScreen(), const ['leads']);
      expect(
        sentence(tester),
        contains('whenever a deal, ticket or other record'),
      );
      await pump(tester, const WebhooksScreen(), const ['leads', 'tickets']);
      expect(sentence(tester), contains('whenever a deal or other record'));
      await pump(tester, const WebhooksScreen(), const [
        'leads',
        'deals',
        'tickets',
      ]);
      expect(sentence(tester), contains('whenever a record changes'));
    });
  });
}
