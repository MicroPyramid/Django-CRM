import 'package:bottle_crm/data/models/org_settings.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/settings_provider.dart';
import 'package:bottle_crm/screens/settings/organization_edit_screen.dart';
import 'package:bottle_crm/screens/settings/organization_screen.dart';
import 'package:bottle_crm/services/org_date.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Invoice numbering (#802) on the two organization screens, at a 390px phone.
OrgSettings _org({String datePart = 'DAY', int start = 1}) =>
    OrgSettings.fromJson({
      'id': 'org-1',
      'name': 'Acme',
      'timezone': 'UTC',
      'invoice_number_prefix': 'INV-',
      'estimate_number_prefix': 'EST-',
      'number_date_part': datePart,
      'number_padding': 4,
      'invoice_number_start': start,
    });

/// The org as stored, and every body the screen saved.
class _Org extends OrgSettingsNotifier {
  _Org(this.org);

  final OrgSettings org;
  final List<Map<String, dynamic>> saved = [];

  @override
  Future<OrgSettings> build() async => org;

  @override
  Future<String?> save(Map<String, dynamic> payload) async {
    saved.add(payload);
    return null;
  }
}

void _usePhone(WidgetTester tester) {
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

String _ymd(DateTime d) =>
    '${d.year}${d.month.toString().padLeft(2, '0')}'
    '${d.day.toString().padLeft(2, '0')}';

void main() {
  Future<_Org> pumpScreen(
    WidgetTester tester,
    Widget screen, {
    OrgSettings? org,
  }) async {
    _usePhone(tester);
    final notifier = _Org(org ?? _org());
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          orgSettingsProvider.overrideWith(() => notifier),
          orgTimezonesProvider.overrideWith(
            (ref) async => const [
              TimezoneOption(name: 'UTC', offsetMinutes: 0),
            ],
          ),
          orgPacksProvider.overrideWith((ref) async => const <VerticalPack>[]),
          isOrgAdminProvider.overrideWithValue(true),
        ],
        child: MaterialApp(home: screen),
      ),
    );
    await tester.pumpAndSettle();
    return notifier;
  }

  /// The form's own list; every text field carries a Scrollable of its own.
  Future<void> reach(WidgetTester tester, Finder target) => tester
      .dragUntilVisible(target, find.byType(ListView), const Offset(0, -250));

  Future<void> chooseDatePart(
    WidgetTester tester,
    String from,
    String to,
  ) async {
    await reach(tester, find.text(from));
    await tester.tap(find.text(from));
    await tester.pumpAndSettle();
    await tester.tap(find.text(to).last);
    await tester.pumpAndSettle();
  }

  Future<void> save(WidgetTester tester) async {
    // The keyboard dismissed first, as a person would: a focused field keeps
    // scrolling itself back on screen. Then dragged until built and scrolled
    // into full view, since a drag can stop with the button under the list's
    // bottom edge, where a tap lands on the list.
    FocusManager.instance.primaryFocus?.unfocus();
    await tester.pumpAndSettle();
    await reach(tester, find.text('Save changes'));
    await tester.ensureVisible(find.text('Save changes'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save changes'));
    await tester.pumpAndSettle();
  }

  testWidgets('the organization screen shows how new numbers look', (
    tester,
  ) async {
    await pumpScreen(tester, const OrganizationScreen());
    final day = _ymd(orgToday());
    await reach(tester, find.text('EST-$day-0001'));
    expect(find.text('INV-$day-0001'), findsOneWidget);
    expect(find.text('EST-$day-0001'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('a starting number is offered for undated numbers only', (
    tester,
  ) async {
    await pumpScreen(tester, const OrganizationEditScreen());
    await reach(tester, find.text('Counter digits'));
    expect(find.text('Start invoices at'), findsNothing);

    await chooseDatePart(
      tester,
      'Full date, count restarts each day',
      'No date, one running count',
    );
    await reach(tester, find.text('Start invoices at'));
    await tester.enterText(
      find.widgetWithText(TextField, 'Start invoices at'),
      '1042',
    );
    await tester.pumpAndSettle();

    // The example follows the form as it is typed.
    expect(find.textContaining('INV-1042'), findsOneWidget);
    expect(find.textContaining('EST-0001'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('saves an undated sequence with its start', (tester) async {
    final org = await pumpScreen(tester, const OrganizationEditScreen());
    await chooseDatePart(
      tester,
      'Full date, count restarts each day',
      'No date, one running count',
    );
    await reach(tester, find.text('Start invoices at'));
    await tester.enterText(
      find.widgetWithText(TextField, 'Start invoices at'),
      '1042',
    );
    await save(tester);

    expect(org.saved.single['number_date_part'], 'NONE');
    expect(org.saved.single['invoice_number_start'], 1042);
    expect(org.saved.single['number_padding'], 4);
  });

  testWidgets('adding a date to a started sequence sends the start as 1', (
    tester,
  ) async {
    // The server refuses a start with a date, including one already stored.
    final org = await pumpScreen(
      tester,
      const OrganizationEditScreen(),
      org: _org(datePart: 'NONE', start: 1042),
    );
    await chooseDatePart(
      tester,
      'No date, one running count',
      'Year, count restarts each year',
    );
    await save(tester);

    expect(org.saved.single['number_date_part'], 'YEAR');
    expect(org.saved.single['invoice_number_start'], 1);
  });

  testWidgets('a prefix the server would refuse is caught before saving', (
    tester,
  ) async {
    final org = await pumpScreen(tester, const OrganizationEditScreen());
    await reach(tester, find.text('Invoice prefix'));
    await tester.enterText(
      find.widgetWithText(TextField, 'Invoice prefix'),
      'INV/2026/',
    );
    await save(tester);

    expect(org.saved, isEmpty);
    expect(find.textContaining('letters, numbers, hyphens'), findsOneWidget);
  });
}
